---
name: create-canvas
description: Generate an Obsidian Canvas JSON file for a chapter, connecting scene files in order. Runs create_canvas.py and offers to enhance the layout.
argument-hint: "[chapter folder name or number, e.g. '01' or '01 - The Arrival - Canvas']"
allowed-tools: [Read, Write, Bash, Glob, AskUserQuestion]
---

# Create Obsidian Canvas

Generate a `.canvas` file for a chapter, linking all scene files in narrative order.

## Steps

1. **Determine chapter**
   - If argument provided, find the matching chapter folder in `[vault]/Chapters/`
   - Otherwise list available chapter folders and ask which to canvas
   - Confirm: "Create canvas for [chapter folder name]?"

2. **Verify scenes exist**
   - List all `.md` files in `[chapter folder]/Scenes/`
   - If none found, tell user to run generate first
   - Show file list and ask: "Are these in the correct narrative order? If not, rename them with the correct NN- prefix before continuing."

3. **Determine vault prefix**
   - The canvas requires vault-relative paths
   - Construct from vault root: e.g. `DnD/The Plague of Myrkul/Chapters/01 - The Arrival - Canvas`
   - The vault root base is derived from settings. Ask user to confirm the vault name if unclear.

4. **Run canvas generator**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/create_canvas.py" \
     "[chapter_folder]/Scenes/" \
     "[vault_prefix]" \
     "[chapter_folder]/[chapter_name].canvas"
   ```

5. **Offer enhancements**
   Ask: "The canvas has been generated with a linear layout. Would you like me to enhance it? Options:
   - **[B] Add branching** — add player choice nodes with arrows to parallel paths
   - **[N] Add NPC references** — add colored nodes linking to Characters/ files
   - **[D] Add dialogue labels** — add edge labels for key transitions
   - **[S] Skip** — leave as linear layout"

   If user selects any enhancement, read the canvas JSON and modify it following Canvas JSON rules:
   - Branching: add text nodes (color "6") for choices, offset in X, add edges with labels
   - NPC references: add file nodes (color "4") pointing to Characters/ files, connect to relevant scenes
   - Dialogue labels: add `label` field to existing edges

6. **Verify canvas**
   After writing, remind the user:
   ```
   Canvas written: [path]

   To verify in Obsidian:
   1. Open Obsidian and navigate to the chapter folder
   2. Open the .canvas file
   3. Confirm all scene nodes show content (not just file paths)
   4. Check that all edges connect correctly

   Canvas colors reference:
   "1" = title/heading  "2" = chapter transition  "4" = NPC  "5" = dialogue  "6" = player choice
   ```

## Canvas JSON Rules

When modifying canvas JSON:
- Node heights must be 250–600px (smaller nodes don't render content in Obsidian)
- All file paths must be vault-relative (from vault root, not filesystem root)
- Node IDs must be unique strings
- Edge IDs must be unique strings, format: `e_[fromId]_[toId]`
- fromSide/toSide values: `top`, `bottom`, `left`, `right`
