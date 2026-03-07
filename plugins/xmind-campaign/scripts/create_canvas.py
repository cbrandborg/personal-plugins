#!/usr/bin/env python3
"""
Create an Obsidian Canvas JSON file from a list of scene files.

Usage:
    python3 create_canvas.py <scenes_dir> <vault_prefix> <output_canvas>

Example:
    python3 create_canvas.py ./Scenes/ "DnD/Campaign/Chapters/03 - Town - Canvas" ./Town.canvas

The script reads all .md files in scenes_dir, sorts them by filename,
and creates a vertically-flowing canvas with nodes connected by edges.
"""

import json
import os
import sys


def create_canvas(scenes_dir: str, vault_prefix: str, output_path: str):
    """Generate an Obsidian Canvas from scene files."""
    # Collect scene files
    scenes = sorted(
        [f for f in os.listdir(scenes_dir) if f.endswith(".md")],
        key=lambda x: x.lower(),
    )

    if not scenes:
        print(f"No .md files found in {scenes_dir}")
        sys.exit(1)

    print(f"Found {len(scenes)} scene files")

    nodes = []
    edges = []
    y_pos = 0
    y_spacing = 420  # Space between nodes
    prev_id = None

    # Title node
    chapter_name = os.path.basename(vault_prefix).replace(" - Canvas", "")
    nodes.append(
        {
            "id": "title",
            "type": "text",
            "text": chapter_name.upper(),
            "x": 0,
            "y": y_pos,
            "width": 400,
            "height": 80,
            "color": "1",
        }
    )
    prev_id = "title"
    y_pos += 150

    # Scene nodes
    for i, scene_file in enumerate(scenes):
        node_id = f"scene_{i:02d}"
        file_path = f"{vault_prefix}/Scenes/{scene_file}"

        # Estimate height based on file size
        full_path = os.path.join(scenes_dir, scene_file)
        size = os.path.getsize(full_path)
        height = min(600, max(250, int(size / 5)))

        nodes.append(
            {
                "id": node_id,
                "type": "file",
                "file": file_path,
                "x": 0,
                "y": y_pos,
                "width": 400,
                "height": height,
            }
        )

        if prev_id:
            edges.append(
                {
                    "id": f"e_{prev_id}_{node_id}",
                    "fromNode": prev_id,
                    "fromSide": "bottom",
                    "toNode": node_id,
                    "toSide": "top",
                }
            )

        prev_id = node_id
        y_pos += height + 70

    canvas = {"nodes": nodes, "edges": edges}

    with open(output_path, "w") as f:
        json.dump(canvas, f, indent=2, ensure_ascii=False)

    print(f"Canvas created: {output_path}")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")
    print(f"\nNOTE: This generates a basic linear layout.")
    print("Edit the canvas manually or with Claude to add branching,")
    print("color coding, NPC references, and choice nodes.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <scenes_dir> <vault_prefix> <output_canvas>")
        print('Example: python3 create_canvas.py ./Scenes/ "DnD/My Campaign/Chapters/02 - Town - Canvas" ./Town.canvas')
        sys.exit(1)

    create_canvas(sys.argv[1], sys.argv[2], sys.argv[3])
