#!/usr/bin/env python3
"""
Extract content from XMind files into structured JSON.
Handles both attached AND summary children (the bracket/brace groupings).

Usage:
    python3 extract_xmind.py <path_to.xmind> <output_dir>

Output:
    <output_dir>/content.json     - Raw XMind JSON
    <output_dir>/full_tree.json   - Complete extracted tree (all node types)
    <output_dir>/branch_XX.json   - Individual top-level branches
    <output_dir>/summary_report.txt - Report of all summary subtrees found
"""

import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
import unicodedata
import uuid
import zipfile

MAX_ARCHIVE_FILES = 10_000
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
COPY_CHUNK_BYTES = 1024 * 1024
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def _safe_member_parts(info: zipfile.ZipInfo) -> tuple[str, ...]:
    """Return normalized relative path parts or reject an unsafe member."""
    if info.flag_bits & 0x1:
        raise ValueError(f"encrypted archive member is not supported: {info.filename}")
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if (
        not name
        or "\x00" in name
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or (path.parts and ":" in path.parts[0])
    ):
        raise ValueError(f"unsafe archive member path: {info.filename}")
    for part in path.parts:
        normalized = unicodedata.normalize("NFC", part)
        stem = normalized.split(".", 1)[0].upper()
        if (
            ":" in normalized
            or normalized.endswith((" ", "."))
            or stem in WINDOWS_RESERVED_NAMES
        ):
            raise ValueError(f"archive member is not portable: {info.filename}")
    mode = (info.external_attr >> 16) & 0o170000
    allowed_modes = {0, stat.S_IFDIR} if info.is_dir() else {0, stat.S_IFREG}
    if mode not in allowed_modes:
        raise ValueError(f"archive special files are not supported: {info.filename}")
    return path.parts


def safe_extract_archive(xmind_path: str | Path, output_dir: str | Path) -> None:
    """Extract a bounded XMind archive without traversal or special files."""
    requested_output = Path(output_dir).absolute()
    if requested_output.is_symlink():
        raise ValueError("output directory must not be a symlink")
    requested_output.parent.mkdir(parents=True, exist_ok=True)
    output = requested_output.parent.resolve() / requested_output.name
    if output.is_symlink():
        raise ValueError("output directory must not be a symlink")

    with zipfile.ZipFile(xmind_path, "r") as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ARCHIVE_FILES:
            raise ValueError(f"archive contains more than {MAX_ARCHIVE_FILES} entries")

        planned = []
        seen = set()
        kinds = {}
        declared_total = 0
        for info in entries:
            parts = _safe_member_parts(info)
            normalized = "/".join(parts)
            collision_key = "/".join(
                unicodedata.normalize("NFC", part).casefold() for part in parts
            )
            if collision_key in seen:
                raise ValueError(f"portable archive member collision: {normalized}")
            seen.add(collision_key)
            kinds[collision_key] = info.is_dir()
            if info.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f"archive member exceeds {MAX_MEMBER_BYTES} bytes: {normalized}")
            declared_total += info.file_size
            if declared_total > MAX_TOTAL_BYTES:
                raise ValueError(f"archive exceeds {MAX_TOTAL_BYTES} uncompressed bytes")
            planned.append((info, parts))

        for key, is_directory in kinds.items():
            parts = key.split("/")
            for index in range(1, len(parts)):
                ancestor = "/".join(parts[:index])
                if ancestor in kinds and not kinds[ancestor]:
                    raise ValueError(f"archive file/directory collision: {key}")
            if not is_directory and any(other.startswith(f"{key}/") for other in kinds):
                raise ValueError(f"archive file/directory collision: {key}")

        with tempfile.TemporaryDirectory(
            prefix=f".{output.name}.extract-", dir=output.parent
        ) as staging_name:
            staging = Path(staging_name)
            actual_total = 0
            for info, parts in planned:
                target = staging.joinpath(*parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                member_total = 0
                with archive.open(info, "r") as source, target.open("xb") as destination:
                    while chunk := source.read(COPY_CHUNK_BYTES):
                        member_total += len(chunk)
                        actual_total += len(chunk)
                        if member_total > MAX_MEMBER_BYTES or actual_total > MAX_TOTAL_BYTES:
                            raise ValueError(
                                f"archive expanded beyond configured limits: {info.filename}"
                            )
                        destination.write(chunk)

            backup = output.parent / f".{output.name}.backup-{uuid.uuid4().hex}"
            moved_existing = False
            commit_complete = False
            rollback_complete = False
            try:
                if output.exists():
                    if not output.is_dir():
                        raise ValueError("output path must be a directory")
                    os.replace(output, backup)
                    moved_existing = True
                os.replace(staging, output)
                commit_complete = True
            except BaseException as commit_error:
                if moved_existing and not output.exists() and backup.exists():
                    try:
                        os.replace(backup, output)
                        rollback_complete = True
                    except BaseException as rollback_error:
                        raise RuntimeError(
                            f"extraction commit and rollback failed; backup preserved at {backup}: "
                            f"{rollback_error}"
                        ) from commit_error
                raise
            finally:
                if backup.exists() and (commit_complete or rollback_complete):
                    shutil.rmtree(backup)


def extract_xmind(xmind_path: str, output_dir: str):
    """Extract and parse an XMind file."""
    # XMind files are ZIP archives. Extract only bounded regular files under
    # the selected output directory; never trust member paths from the archive.
    safe_extract_archive(xmind_path, output_dir)

    content_path = os.path.join(output_dir, "content.json")
    if not os.path.exists(content_path):
        print("ERROR: No content.json found in XMind file")
        sys.exit(1)

    with open(content_path) as f:
        data = json.load(f)

    print(f"Sheets found: {len(data)}")
    for i, sheet in enumerate(data):
        print(f"  Sheet {i}: {sheet.get('title', '?')}")

    root = data[0]["rootTopic"]
    full_tree = extract_topic(root)

    # Save full tree
    with open(os.path.join(output_dir, "full_tree.json"), "w") as f:
        json.dump(full_tree, f, indent=2, ensure_ascii=False)

    # Save individual branches
    for i, child in enumerate(full_tree.get("children", [])):
        branch_path = os.path.join(output_dir, f"branch_{i:02d}.json")
        with open(branch_path, "w") as f:
            json.dump(child, f, indent=2, ensure_ascii=False)
        n, c = count_tree(child)
        print(f"  Branch {i:02d}: {child['title'][:50]} ({n} nodes, {c} chars)")

    # Find and report all summary subtrees
    summaries = find_all_summaries(full_tree)
    report_path = os.path.join(output_dir, "summary_report.txt")
    with open(report_path, "w") as f:
        f.write(f"Summary subtrees found: {len(summaries)}\n\n")
        for s in summaries:
            n, c = count_tree(s["summary"])
            f.write(f"Title: {s['summary']['title']}\n")
            f.write(f"  Parent: {s['parent_path']}\n")
            f.write(f"  Nodes: {n}, Notes chars: {c}\n\n")

    print(f"\nSummary subtrees found: {len(summaries)}")
    print(f"Output saved to: {output_dir}")
    if summaries:
        print(f"WARNING: {len(summaries)} summary subtrees detected!")
        print("These contain content in XMind bracket/brace groupings.")
        print(f"See {report_path} for details.")


def extract_topic(topic: dict, path: str = "") -> dict:
    """Recursively extract a topic and ALL its children (attached + summary)."""
    title = topic.get("title", "?")
    current_path = f"{path}/{title}" if path else title

    notes = topic.get("notes", {})
    note_text = ""
    if isinstance(notes, dict) and "plain" in notes:
        note_text = notes["plain"].get("content", "")

    image = ""
    img_data = topic.get("image")
    if isinstance(img_data, dict):
        image = img_data.get("src", "")

    result = {
        "path": current_path,
        "title": title,
        "notes": note_text,
        "image": image,
        "children": [],
        "summary_children": [],
    }

    children_obj = topic.get("children", {})

    # CRITICAL: Extract BOTH attached and summary children
    for child in children_obj.get("attached", []):
        result["children"].append(extract_topic(child, current_path))

    for child in children_obj.get("summary", []):
        result["summary_children"].append(extract_topic(child, current_path))

    return result


def find_all_summaries(node: dict, results: list = None) -> list:
    """Find all summary subtrees in the extracted tree."""
    if results is None:
        results = []

    if node.get("summary_children"):
        for sc in node["summary_children"]:
            results.append({"parent_path": node["path"], "summary": sc})

    for child in node.get("children", []):
        find_all_summaries(child, results)
    for child in node.get("summary_children", []):
        find_all_summaries(child, results)

    return results


def count_tree(node: dict) -> tuple:
    """Count total nodes and note characters in a subtree."""
    nodes = 1
    chars = len(node.get("notes", ""))
    for c in node.get("children", []):
        n, ch = count_tree(c)
        nodes += n
        chars += ch
    for c in node.get("summary_children", []):
        n, ch = count_tree(c)
        nodes += n
        chars += ch
    return nodes, chars


def dump_tree_text(node: dict, indent: int = 0) -> str:
    """Dump a node tree as readable text for auditing."""
    lines = []
    title = node.get("title", "?")
    notes_len = len(node.get("notes", ""))
    img = " [IMG]" if node.get("image") else ""
    prefix = "  " * indent
    lines.append(f"{prefix}{title} [notes:{notes_len}]{img}")

    for c in node.get("children", []):
        lines.append(dump_tree_text(c, indent + 1))
    for c in node.get("summary_children", []):
        lines.append(dump_tree_text(c, indent + 1))

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <path_to.xmind> <output_dir>")
        sys.exit(1)

    extract_xmind(sys.argv[1], sys.argv[2])
