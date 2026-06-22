"""Regression tests for per-skill sync and versioning behavior."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import skills  # noqa: E402


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_skill(path: Path, name: str, body: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill {name}.\n---\n\n{body}\n",
        encoding="utf-8",
    )


def git(*args: str, cwd: Path) -> None:
    completed = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if completed.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")


class PerSkillSyncTest(unittest.TestCase):
    def test_updates_only_changed_leaf_and_bumps_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "marketplace"
            upstream = Path(temp_dir) / "upstream"
            root.mkdir()
            upstream.mkdir()
            write_skill(upstream / "skills" / "foo", "foo", "unchanged content")
            write_skill(upstream / "skills" / "bar", "bar", "new content")
            git("init", "-b", "main", cwd=upstream)
            git("config", "user.name", "Test", cwd=upstream)
            git("config", "user.email", "test@example.com", cwd=upstream)
            git("config", "commit.gpgSign", "false", cwd=upstream)
            git("add", ".", cwd=upstream)
            git("commit", "-m", "initial", cwd=upstream)

            plugins = root / "plugins"
            plugin = plugins / "bundle"
            shutil.copytree(upstream / "skills" / "foo", plugin / "skills" / "foo")
            write_skill(plugin / "skills" / "bar", "bar", "old content")
            write_json(plugin / ".claude-plugin" / "plugin.json", {"name": "bundle", "version": "1.0.0"})
            write_json(plugin / ".codex-plugin" / "plugin.json", {"name": "bundle", "version": "1.0.0"})
            write_json(root / "sources.lock.json", {"sources": {}})

            source = {
                "id": "test-collection",
                "plugin": "bundle",
                "git": str(upstream),
                "ref": "main",
                "path": "skills",
            }
            foo_before = (plugin / "skills" / "foo" / "SKILL.md").read_text(encoding="utf-8")

            with patch.multiple(
                skills,
                ROOT=root,
                PLUGINS=plugins,
                SOURCES=root / "sources.json",
                LOCK=root / "sources.lock.json",
                CLAUDE_MARKETPLACE=root / ".claude-plugin" / "marketplace.json",
                CODEX_MARKETPLACE=root / ".agents" / "plugins" / "marketplace.json",
            ):
                updates = skills.sync_source(source, apply=True)
                self.assertEqual([update["skill"] for update in updates], ["bar"])
                skills.finalize_sync_updates({"bundle": updates})
                self.assertEqual(skills.sync_source(source, apply=True), [])

            self.assertEqual(
                (plugin / "skills" / "foo" / "SKILL.md").read_text(encoding="utf-8"),
                foo_before,
            )
            self.assertIn("new content", (plugin / "skills" / "bar" / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual(
                json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())["version"],
                "1.0.1",
            )
            self.assertEqual(
                json.loads((plugin / ".codex-plugin" / "plugin.json").read_text())["version"],
                "1.0.1",
            )
            lock = json.loads((root / "sources.lock.json").read_text())
            self.assertIn("bar", lock["sources"]["test-collection"]["skills"])
            self.assertNotIn("foo", lock["sources"]["test-collection"]["skills"])

    def test_preserves_local_edits_when_upstream_skill_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "marketplace"
            upstream = Path(temp_dir) / "upstream"
            root.mkdir()
            upstream.mkdir()
            write_skill(upstream / "skills" / "foo", "foo", "upstream content")
            git("init", "-b", "main", cwd=upstream)
            git("config", "user.name", "Test", cwd=upstream)
            git("config", "user.email", "test@example.com", cwd=upstream)
            git("config", "commit.gpgSign", "false", cwd=upstream)
            git("add", ".", cwd=upstream)
            git("commit", "-m", "initial", cwd=upstream)
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=upstream, check=True, capture_output=True, text=True
            ).stdout.strip()

            plugins = root / "plugins"
            plugin = plugins / "bundle"
            write_skill(plugin / "skills" / "foo", "foo", "my local edit")
            write_json(plugin / ".claude-plugin" / "plugin.json", {"name": "bundle", "version": "1.0.0"})
            write_json(plugin / ".codex-plugin" / "plugin.json", {"name": "bundle", "version": "1.0.0"})
            upstream_hash = skills.tree_digest(upstream / "skills" / "foo")
            write_json(
                root / "sources.lock.json",
                {
                    "sources": {
                        "test-skill": {
                            "skills": {"foo": {"commit": commit, "content_sha256": upstream_hash}}
                        }
                    }
                },
            )
            source = {
                "id": "test-skill",
                "plugin": "bundle",
                "git": str(upstream),
                "ref": "main",
                "path": "skills/foo",
            }

            with patch.multiple(skills, ROOT=root, PLUGINS=plugins, LOCK=root / "sources.lock.json"):
                self.assertEqual(skills.sync_source(source, apply=True), [])

            self.assertIn("my local edit", (plugin / "skills" / "foo" / "SKILL.md").read_text())
            self.assertEqual(
                json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())["version"],
                "1.0.0",
            )


if __name__ == "__main__":
    unittest.main()
