---
name: extract
description: "Use when extracting an XMind file for an Obsidian campaign import. Safely produces a complete JSON tree, branch files, resources, and a summary-subtree report."
version: 0.2.0
author: Christian Brandborg
license: 0BSD
compatibility: "Requires Python 3.10+ and a JSON-based .xmind file."
---

# Extract an XMind file

Safely extract a `.xmind` archive into structured JSON before auditing or generating notes.

## Resolve the bundled script

Set `<plugin-root>` to the installed plugin directory containing `plugin.json`. When this skill was loaded from `skills/extract/SKILL.md`, `<plugin-root>` is two directories above that file. Do not rely on a provider-specific plugin-root variable.

The script is:

```text
<plugin-root>/scripts/extract_xmind.py
```

## Procedure

1. Obtain the `.xmind` path from the request or ask for it. Verify it is an existing regular file with the `.xmind` suffix.
2. Use `_extracted/` beside the source file unless the user requests another output directory.
3. Warn before replacing an existing output directory. The script stages extraction, but replacement still removes the prior extracted output after a successful stage.
4. Verify `python3` is available, then run with arguments as separate shell tokens:

   ```bash
   python3 "<plugin-root>/scripts/extract_xmind.py" "<xmind-path>" "<output-dir>"
   ```

5. Read `full_tree.json` and `summary_report.txt`. Enumerate `branch_XX.json` files and report each branch's node count and notes-character count from the script output.
6. If summary subtrees exist, state their exact count and require them to be covered during generation.
7. Ask for the target Obsidian vault path if generation is requested and it is not already known. Do not store it outside the user's project unless the user explicitly asks.

## Verification

Confirm that these outputs exist and are readable:

- `content.json`
- `full_tree.json`
- `summary_report.txt`
- one `branch_XX.json` per top-level attached child
- referenced files under `resources/`, when images exist

Report branch count, notes-bearing node count, summary-subtree count, output path, and any rejected archive condition. If `content.json` is absent, treat the input as unsupported or corrupt and stop.
