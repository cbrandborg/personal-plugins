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
import sys
import zipfile


def extract_xmind(xmind_path: str, output_dir: str):
    """Extract and parse an XMind file."""
    os.makedirs(output_dir, exist_ok=True)

    # XMind files are ZIP archives
    with zipfile.ZipFile(xmind_path, "r") as z:
        z.extractall(output_dir)

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
