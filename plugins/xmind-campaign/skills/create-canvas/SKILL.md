---
name: create-canvas
description: "Use when creating an Obsidian Canvas from generated chapter scenes. Runs the bundled generator, verifies its JSON, and can add reviewed branching or references."
version: 0.2.0
author: Christian Brandborg
license: 0BSD
compatibility: "Requires Python 3.10+, Obsidian Canvas support, and generated Markdown scene files."
---

# Create an Obsidian Canvas

Generate a linear `.canvas` file that links chapter scenes in filename order.

## Resolve the bundled script

Set `<plugin-root>` to the installed plugin directory containing `plugin.json`. When this skill was loaded from `skills/create-canvas/SKILL.md`, `<plugin-root>` is two directories above that file. Do not rely on a provider-specific plugin-root variable.

The script is:

```text
<plugin-root>/scripts/create_canvas.py
```

## Procedure

1. Obtain the confirmed vault root and chapter folder. If more than one chapter matches an abbreviation or number, ask the user to choose.
2. Read `<chapter-folder>/Scenes/`, list all `.md` files in lexical filename order, and confirm that this is the intended narrative order. Stop if no scenes exist.
3. Construct a vault-relative chapter prefix. Never pass an absolute filesystem path as the canvas `file` prefix.
4. Choose an output path inside the chapter folder and warn before replacing an existing `.canvas` file.
5. Verify `python3` is available, then run with arguments as separate shell tokens:

   ```bash
   python3 "<plugin-root>/scripts/create_canvas.py" \
     "<chapter-folder>/Scenes" \
     "<vault-relative-chapter-prefix>" \
     "<chapter-folder>/<chapter-name>.canvas"
   ```

6. Parse the written file as JSON. Confirm that it has `nodes` and `edges`, one file node per scene, unique node and edge IDs, vault-relative file paths, and edges whose endpoints exist.
7. Report the output path and exact node and edge counts.

## Optional enhancements

Only after the basic canvas verifies, offer:

- branching player-choice text nodes (color `"6"`)
- NPC file references (color `"4"`)
- labels on transition edges

After edits, parse and verify the JSON again. File nodes should be 250–600 px high, IDs must remain unique, and `fromSide`/`toSide` must be one of `top`, `bottom`, `left`, or `right`.
