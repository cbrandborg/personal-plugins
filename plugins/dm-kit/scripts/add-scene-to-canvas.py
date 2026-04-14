#!/usr/bin/env python3
"""add-scene-to-canvas.py — Add a scene file as a node to an Obsidian .canvas file.

Usage:
    add-scene-to-canvas.py <canvas-file> <scene-file-path> [--label LABEL]
                           [--width W] [--height H]

The scene file path must be given as a vault-relative path starting from the
vault root (e.g. "DnD/The Plague of Myrkul/Chapters/09 - The Road to
Ravenholt/Scenes/09 - Test.md"). Obsidian canvas nodes reference files this way.

The new node is positioned directly below the last existing file node in the
canvas, inheriting its x coordinate. If no file nodes exist, it goes at 0,0.

Node sizing defaults to 400x300, within the 250-600 height range required for
canvas cards to render content (see CLAUDE.md Canvas Format section).

Exits 0 on success and prints the new node's ID.
Exits 1 on failure (missing canvas, invalid JSON, scene file not found, etc.).
"""
import argparse
import json
import sys
import uuid
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canvas_file", type=Path, help="Path to the .canvas file")
    parser.add_argument(
        "scene_file",
        help="Vault-relative path to the scene markdown file (as stored in canvas nodes)",
    )
    parser.add_argument("--label", default=None, help="Optional display label (not used by Obsidian for file nodes, reserved)")
    parser.add_argument("--width", type=int, default=400, help="Node width (default 400)")
    parser.add_argument("--height", type=int, default=300, help="Node height (default 300, must be 250-600)")
    args = parser.parse_args()

    if not args.canvas_file.exists():
        print(f"error: canvas file not found: {args.canvas_file}", file=sys.stderr)
        return 1

    if not (250 <= args.height <= 600):
        print(f"error: --height must be 250-600 (got {args.height})", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.canvas_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in canvas file: {exc}", file=sys.stderr)
        return 1

    nodes = data.setdefault("nodes", [])
    data.setdefault("edges", [])

    # Find the last existing file node to position below it.
    file_nodes = [n for n in nodes if n.get("type") == "file"]
    if file_nodes:
        last = max(file_nodes, key=lambda n: n.get("y", 0))
        new_x = last.get("x", 0)
        new_y = last.get("y", 0) + last.get("height", 300) + 100
    else:
        new_x = 0
        new_y = 0

    new_id = uuid.uuid4().hex[:16]
    node = {
        "id": new_id,
        "type": "file",
        "file": args.scene_file,
        "x": new_x,
        "y": new_y,
        "width": args.width,
        "height": args.height,
    }
    nodes.append(node)

    args.canvas_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(new_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
