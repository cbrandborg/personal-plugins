#!/usr/bin/env python3
"""Manage vendored, cross-agent skills in this marketplace.

The tool deliberately relies only on Python's standard library and git.  It
keeps the plugin repository, not an external package cache, as the source of
truth for installed skills.
"""

from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
SOURCES = ROOT / "sources.json"
LOCK = ROOT / "sources.lock.json"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(*args: str, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def normalize_git_source(source: str) -> str:
    """Convert GitHub shorthand and skills.sh pages into Git clone URLs."""
    parsed = urlparse(source)
    if parsed.netloc in {"skills.sh", "www.skills.sh"}:
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            raise ValueError("a skills.sh URL must include at least owner/repository")
        return f"https://github.com/{parts[0]}/{parts[1]}.git"
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source):
        return f"https://github.com/{source}.git"
    return source


def skills_sh_skill_name(source: str) -> str | None:
    """Return the selected skill slug from a skills.sh skill page."""
    parsed = urlparse(source)
    if parsed.netloc not in {"skills.sh", "www.skills.sh"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) == 3:
        return parts[2]
    return None


def discover_skill_path(git_url: str, ref: str, skill_name: str) -> str:
    """Find an individual skills.sh skill in its upstream repository.

    skills.sh URLs name a skill but do not encode its repository-relative
    directory. Repositories commonly organize skills by category, so searching
    the checkout is more reliable than assuming `skills/<name>`.
    """
    with tempfile.TemporaryDirectory(prefix="personal-plugins-discover-") as dirname:
        checkout = Path(dirname) / "source"
        run("git", "clone", "--depth", "1", "--branch", ref, git_url, str(checkout))
        matches = sorted(
            skill.parent.relative_to(checkout).as_posix()
            for skill in checkout.rglob("SKILL.md")
            if skill.parent.name == skill_name
        )
    if len(matches) != 1:
        options = ", ".join(matches) if matches else "none"
        raise ValueError(
            f"could not uniquely find skills.sh skill {skill_name!r} (matches: {options}); pass --path"
        )
    return matches[0]


def valid_name(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", value))


def default_description(plugin: str) -> str:
    return f"Vendored cross-agent skills bundled in the {plugin} plugin."


def plugin_manifests(plugin: str, version: str, description: str, category: str) -> tuple[dict, dict]:
    author = {"name": "Christian Brandborg", "url": "https://github.com/cbrandborg"}
    claude = {
        "name": plugin,
        "version": version,
        "description": description,
        "author": author,
    }
    codex = {
        "name": plugin,
        "version": version,
        "description": description,
        "author": author,
        "repository": "https://github.com/cbrandborg/personal-plugins",
        "skills": "./skills/",
        "interface": {
            "displayName": plugin.replace("-", " ").title(),
            "shortDescription": description,
            "longDescription": description,
            "developerName": "Christian Brandborg",
            "category": category,
            "capabilities": ["Read", "Write"],
            "defaultPrompt": [f"Use {plugin} to help with this task."],
        },
    }
    return claude, codex


def ensure_plugin(plugin: str, description: str, category: str) -> None:
    plugin_dir = PLUGINS / plugin
    claude_manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    codex_manifest = plugin_dir / ".codex-plugin" / "plugin.json"
    if claude_manifest.exists() or codex_manifest.exists():
        return
    claude, codex = plugin_manifests(plugin, "0.1.0", description, category)
    write_json(claude_manifest, claude)
    write_json(codex_manifest, codex)
    (plugin_dir / "skills").mkdir(parents=True, exist_ok=True)
    update_marketplaces(plugin, category)


def update_marketplaces(plugin: str, category: str) -> None:
    claude = load_json(CLAUDE_MARKETPLACE)
    if not any(entry.get("name") == plugin for entry in claude["plugins"]):
        claude["plugins"].append(
            {
                "name": plugin,
                "source": f"./plugins/{plugin}",
                "author": {"name": "Christian Brandborg"},
            }
        )
        write_json(CLAUDE_MARKETPLACE, claude)

    codex = load_json(CODEX_MARKETPLACE)
    if not any(entry.get("name") == plugin for entry in codex["plugins"]):
        codex["plugins"].append(
            {
                "name": plugin,
                "source": {"source": "local", "path": f"./plugins/{plugin}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": category,
            }
        )
        write_json(CODEX_MARKETPLACE, codex)


def clone_source(source: dict, temp: Path) -> tuple[Path, str]:
    checkout = temp / "source"
    run("git", "clone", "--depth", "1", "--branch", source["ref"], source["git"], str(checkout))
    commit = run("git", "rev-parse", "HEAD", cwd=checkout)
    path = checkout / source["path"]
    if not path.is_dir():
        raise ValueError(f"upstream path does not exist: {source['path']}")
    return path, commit


def tree_equal(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    comparison = filecmp.dircmp(left, right)
    if comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files:
        return False
    return all(tree_equal(left / child, right / child) for child in comparison.common_dirs)


def tree_digest(path: Path) -> str:
    """Return a stable content hash for a skill directory."""
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        relative = child.relative_to(path).as_posix().encode("utf-8")
        digest.update(relative + b"\0")
        digest.update(child.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def find_skills(upstream: Path) -> list[tuple[str, Path, str]]:
    """Return every individual skill managed by one source declaration.

    A direct source path identifies one skill. A collection path is expanded
    into leaf skills, so later syncs compare and update every leaf separately.
    """
    if (upstream / "SKILL.md").is_file():
        return [(upstream.name, upstream, ".")]

    skills = [
        (skill.parent.name, skill.parent, skill.parent.relative_to(upstream).as_posix())
        for skill in sorted(upstream.rglob("SKILL.md"))
    ]
    if not skills:
        raise ValueError("source path contains no SKILL.md files")
    names = [name for name, _, _ in skills]
    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    if duplicate_names:
        raise ValueError(
            "a bundled plugin cannot contain duplicate skill directory names: "
            + ", ".join(duplicate_names)
        )
    return skills


def prepare_skill_payload(upstream_skill: Path, staging_root: Path) -> Path:
    """Copy and normalize one individual skill for a portable plugin payload."""
    payload = staging_root / "payload"
    shutil.copytree(upstream_skill, payload)
    # `disable-model-invocation` is a Claude Code extension. Removing it makes
    # the vendored SKILL.md use the portable Agent Skills subset understood by
    # both marketplace targets. The upstream URL and resolved commit remain
    # recorded in sources.json/sources.lock.json.
    for skill_file in payload.rglob("SKILL.md"):
        text = skill_file.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        end = text.find("\n---", 4)
        if end == -1:
            continue
        frontmatter = text[4:end]
        normalized = "\n".join(
            line for line in frontmatter.splitlines() if not line.startswith("disable-model-invocation:")
        )
        suffix = "\n" if not text.endswith("\n") else ""
        skill_file.write_text("---\n" + normalized + text[end:] + suffix, encoding="utf-8")
    return payload


def bump_patch(version: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"expected a strict semantic version, got {version!r}")
    return f"{match.group(1)}.{match.group(2)}.{int(match.group(3)) + 1}"


def bump_plugin(plugin: str, updates: list[dict]) -> str:
    manifest_paths = [
        PLUGINS / plugin / ".claude-plugin" / "plugin.json",
        PLUGINS / plugin / ".codex-plugin" / "plugin.json",
    ]
    manifests = [load_json(path) for path in manifest_paths]
    versions = {manifest.get("version") for manifest in manifests}
    if len(versions) != 1:
        raise ValueError(f"{plugin}: provider manifests have different versions: {sorted(versions)}")
    version = bump_patch(versions.pop())
    for path, manifest in zip(manifest_paths, manifests):
        manifest["version"] = version
        write_json(path, manifest)
    changelog = PLUGINS / plugin / "CHANGELOG.md"
    lines = [f"## {version} - {datetime.now(timezone.utc).date().isoformat()}", ""]
    lines.extend(
        f"- Synced `{update['source_id']}/{update['skill']}` at `{update['commit']}`."
        for update in updates
    )
    entry = "\n".join(lines) + "\n\n"
    old = changelog.read_text(encoding="utf-8") if changelog.exists() else ""
    changelog.write_text(entry + old, encoding="utf-8")
    return version


def sync_source(source: dict, apply: bool) -> list[dict]:
    """Compare and optionally replace only changed individual skill directories."""
    plugin = source["plugin"]
    plugin_dir = PLUGINS / plugin
    skills_root = plugin_dir / "skills"
    initial_import = not skills_root.exists() or not any(skills_root.iterdir())
    updates: list[dict] = []
    lock = load_json(LOCK)
    source_lock = lock.setdefault("sources", {}).get(source["id"], {})
    locked_skills = source_lock.get("skills", {})
    with tempfile.TemporaryDirectory(prefix="personal-plugins-") as dirname:
        temporary = Path(dirname)
        upstream, commit = clone_source(source, temporary)
        for index, (skill_name, upstream_skill, relative_path) in enumerate(find_skills(upstream)):
            payload = prepare_skill_payload(upstream_skill, temporary / f"skill-{index}")
            target = skills_root / skill_name
            upstream_digest = tree_digest(payload)
            target_digest = tree_digest(target) if target.exists() else None
            locked = locked_skills.get(skill_name, {})
            locked_digest = locked.get("content_sha256")
            locked_commit = locked.get("commit")

            # Legacy locks without a content digest are treated conservatively:
            # an identical local skill is already current, while a divergent
            # local skill is preserved unless a newer upstream commit proves a
            # genuine update may exist.
            if locked_digest is None and target_digest == upstream_digest:
                print(f"{source['id']}/{skill_name}: up to date ({commit[:12]})")
                continue
            if locked_digest is None and locked_commit == commit:
                print(f"{source['id']}/{skill_name}: local changes preserved ({commit[:12]})")
                continue

            # A source commit can move without changing this skill. In that
            # case there is nothing to write or release, even if a user has
            # changed their local vendored copy.
            upstream_changed = (
                locked_digest is None and locked_commit != commit
            ) or (locked_digest is not None and locked_digest != upstream_digest)
            if not upstream_changed:
                status = "up to date" if target_digest == upstream_digest else "local changes preserved"
                print(f"{source['id']}/{skill_name}: {status} ({commit[:12]})")
                continue

            # Never silently overwrite a locally modified vendored skill when
            # upstream also has a real update. CI runs from a clean checkout;
            # this protection is for local use.
            if locked_digest is not None and target_digest not in {None, locked_digest}:
                message = f"{source['id']}/{skill_name}: upstream and local content both changed"
                print(f"{message}; refusing to overwrite")
                if apply:
                    raise ValueError(message)
                continue

            print(f"{source['id']}/{skill_name}: changed ({commit[:12]})")
            update = {
                "source_id": source["id"],
                "plugin": plugin,
                "skill": skill_name,
                "source_path": source["path"] if relative_path == "." else f"{source['path'].rstrip('/')}/{relative_path}",
                "commit": commit,
                "content_sha256": upstream_digest,
                "initial": initial_import,
            }
            updates.append(update)
            if not apply:
                continue
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(payload, target)

    if apply and updates:
        source_lock = lock.setdefault("sources", {}).setdefault(source["id"], {})
        skill_locks = source_lock.setdefault("skills", {})
        for update in updates:
            skill_locks[update["skill"]] = {
                "commit": update["commit"],
                "source_path": update["source_path"],
                "content_sha256": update["content_sha256"],
                "synced_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            }
        write_json(LOCK, lock)
    return updates


def finalize_sync_updates(updates_by_plugin: dict[str, list[dict]]) -> None:
    """Release each affected plugin once, after every leaf update is applied."""
    for plugin, updates in updates_by_plugin.items():
        initial_import = all(update["initial"] for update in updates)
        changelog = PLUGINS / plugin / "CHANGELOG.md"
        if initial_import:
            version = load_json(PLUGINS / plugin / ".claude-plugin" / "plugin.json")["version"]
            lines = [f"## {version} - {datetime.now(timezone.utc).date().isoformat()}", ""]
            lines.extend(
                f"- Initial import of `{update['source_id']}/{update['skill']}` at `{update['commit']}`."
                for update in updates
            )
            old = changelog.read_text(encoding="utf-8") if changelog.exists() else ""
            changelog.write_text("\n".join(lines) + "\n\n" + old, encoding="utf-8")
            print(f"Imported {len(updates)} skill(s) into {plugin} at {version}.")
            continue
        version = bump_plugin(plugin, updates)
        names = ", ".join(update["skill"] for update in updates)
        print(f"Updated {plugin} to {version}: {names}.")


def add(args: argparse.Namespace) -> int:
    plugin = args.plugin
    if not valid_name(plugin):
        raise ValueError("plugin must be lowercase kebab-case and at most 63 characters")
    sources = load_json(SOURCES)
    source_id = args.id or plugin
    if any(item["id"] == source_id for item in sources["sources"]):
        raise ValueError(f"source id already exists: {source_id}")
    git_url = normalize_git_source(args.source)
    path = args.path
    if not path:
        skill_name = skills_sh_skill_name(args.source)
        if skill_name:
            path = discover_skill_path(git_url, args.ref, skill_name)
    if not path:
        raise ValueError("--path is required unless the skills.sh URL names one skill")
    source = {
        "id": source_id,
        "plugin": plugin,
        "git": git_url,
        "ref": args.ref,
        "path": path,
        "category": args.category,
        "description": args.description or default_description(plugin),
    }
    ensure_plugin(plugin, source["description"], source["category"])
    sources["sources"].append(source)
    write_json(SOURCES, sources)
    print(f"registered {source_id}; fetching initial content")
    updates = sync_source(source, apply=True)
    if updates:
        finalize_sync_updates({plugin: updates})
    return validate()


def sync(args: argparse.Namespace) -> int:
    sources = load_json(SOURCES)
    updates_by_plugin: dict[str, list[dict]] = {}
    for source in sources["sources"]:
        updates = sync_source(source, apply=args.apply)
        if updates:
            updates_by_plugin.setdefault(source["plugin"], []).extend(updates)
    if not updates_by_plugin:
        print("No upstream skill content changed.")
    elif not args.apply:
        print("Changes found. Re-run with --apply to vendor and release them.")
    else:
        finalize_sync_updates(updates_by_plugin)
    return validate() if args.apply else 0


def skill_frontmatter(path: Path) -> dict | None:
    contents = path.read_text(encoding="utf-8")
    if not contents.startswith("---\n"):
        return None
    end = contents.find("\n---", 4)
    if end == -1:
        return None
    frontmatter: dict[str, str] = {}
    for line in contents[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def validate() -> int:
    errors: list[str] = []
    try:
        claude = load_json(CLAUDE_MARKETPLACE)
        codex = load_json(CODEX_MARKETPLACE)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Marketplace validation failed: {error}", file=sys.stderr)
        return 1

    claude_names = {entry.get("name") for entry in claude.get("plugins", [])}
    codex_names = {entry.get("name") for entry in codex.get("plugins", [])}
    if claude_names != codex_names:
        errors.append("Claude and Codex marketplace plugin sets differ")

    for plugin_dir in sorted(path for path in PLUGINS.iterdir() if not path.is_symlink() and path.is_dir()):
        plugin = plugin_dir.name
        claude_manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        codex_manifest = plugin_dir / ".codex-plugin" / "plugin.json"
        if not claude_manifest.exists() or not codex_manifest.exists():
            errors.append(f"{plugin}: missing Claude or Codex plugin manifest")
            continue
        try:
            claude_data, codex_data = load_json(claude_manifest), load_json(codex_manifest)
        except json.JSONDecodeError as error:
            errors.append(f"{plugin}: invalid JSON ({error})")
            continue
        if claude_data.get("name") != plugin or codex_data.get("name") != plugin:
            errors.append(f"{plugin}: manifest name does not match directory")
        if claude_data.get("version") != codex_data.get("version"):
            errors.append(f"{plugin}: Claude and Codex manifest versions differ")
        if plugin not in claude_names or plugin not in codex_names:
            errors.append(f"{plugin}: missing marketplace registration")
        for skill in sorted((plugin_dir / "skills").glob("*/SKILL.md")) if (plugin_dir / "skills").exists() else []:
            metadata = skill_frontmatter(skill)
            if not metadata or not metadata.get("name") or not metadata.get("description"):
                errors.append(f"{skill.relative_to(ROOT)}: requires name and description frontmatter")

    for source in load_json(SOURCES).get("sources", []):
        if source.get("plugin") not in claude_names:
            errors.append(f"{source.get('id')}: source references an unregistered plugin")
        if not (PLUGINS / source.get("plugin", "") / "skills").is_dir():
            errors.append(f"{source.get('id')}: plugin has no skills directory")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Validation OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_parser = subparsers.add_parser("add", help="register and vendor a Git or skills.sh source")
    add_parser.add_argument("source", help="Git URL, owner/repo shorthand, or skills.sh URL")
    add_parser.add_argument("--path", help="path to a skill or skill collection in the source repo")
    add_parser.add_argument("--plugin", required=True, help="destination plugin bundle name")
    add_parser.add_argument("--id", help="stable source identifier (defaults to the plugin name)")
    add_parser.add_argument("--ref", default="main", help="upstream branch or tag (default: main)")
    add_parser.add_argument("--category", default="Productivity")
    add_parser.add_argument("--description")
    add_parser.set_defaults(func=add)
    sync_parser = subparsers.add_parser("sync", help="check or apply all registered source updates")
    sync_mode = sync_parser.add_mutually_exclusive_group()
    sync_mode.add_argument("--apply", action="store_true", help="vendor changes and bump affected plugin versions")
    sync_mode.add_argument("--check", action="store_true", help="explicit dry-run; this is also the default")
    sync_parser.set_defaults(func=sync)
    validate_parser = subparsers.add_parser("validate", help="validate marketplace and skill invariants")
    validate_parser.set_defaults(func=lambda _: validate())
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
