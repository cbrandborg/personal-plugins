---
name: generate
description: Generate Obsidian vault files (scenes, NPCs, locations, items, encounters) from extracted XMind data. Processes branch-by-branch with completeness checking. Asks before overwriting existing files.
argument-hint: "[branch number (optional, e.g. 00) or 'all']"
allowed-tools: [Read, Write, Edit, Bash, Glob, AskUserQuestion]
---

# Generate Vault Files from XMind Export

Convert extracted XMind node content into Obsidian Markdown files. Process one branch at a time with completeness verification.

## Steps

1. **Verify prerequisites**
   - Confirm `_extracted/full_tree.json` exists — if not, tell user to run extract first
   - Confirm vault path is set in settings or ask for it
   - Read `_extracted/summary_report.txt` so summary subtrees are tracked throughout

2. **Determine scope**
   - If branch number argument provided (e.g. `01`), process only `_extracted/branch_01.json`
   - If `all` provided, process all branches sequentially
   - If no argument, ask: "Which branch should I process? (run audit-tree to see branches, or type 'all' for all)"

3. **For each branch being processed:**

   ### 3a. Load and display branch overview
   Show the branch name, node count, notes node count, and summary subtrees count. Ask: "Process this branch? (yes/no/skip)"

   ### 3b. Classify all nodes
   Walk the branch tree applying content-mapping rules:
   - Apply Rule 1 (skip check), Rule 2 (title signals), Rule 3 (notes content)
   - For any LOW confidence classification, pause and ask the user before continuing
   - Build a classification table:
     ```
     Node: Market Square
     Path: Root/Act1/Town/Market Square
     Type: scene
     Confidence: HIGH
     Output: Chapters/01 - Town - Canvas/Scenes/01 - Market Square.md
     ```
   - Show the full table and ask: "Proceed with these classifications? Any to change?"

   ### 3c. Determine chapter/output folder
   - Ask: "What is the chapter number and name for this branch? (e.g. '01 - The Arrival')"
   - Construct: `[Vault]/Chapters/01 - The Arrival - Canvas/Scenes/`
   - Create directories if they don't exist

   ### 3d. Generate files node by node
   For each classified node (not `skip`):
   - Apply scene-writing rules to compose the Markdown content
   - Check if the file already exists:
     - If YES: the PreToolUse hook will fire and ask — Overwrite / Skip / Diff first
     - If NO: write directly
   - After writing, log the entry in `_import-log.md`

   ### 3e. Handle images
   For each node with an `image` field:
   - Determine destination folder from content type
   - Copy image from `_extracted/resources/[filename]` to vault destination
   - Confirm file was written before embedding the `![[...]]` link

   ### 3f. Branch completeness check
   After processing all nodes in the branch, run the completeness audit (uses completeness-rules skill):
   - Build expected set from branch JSON
   - Compare against log entries for this branch
   - Report any GAPs immediately
   - Resolve each GAP before proceeding to next branch

4. **Final report**
   After all branches processed:
   ```
   Generate complete.

   Files created: X
   Files updated: X
   Files skipped: X
   Files merged: X
   Images copied: X
   Gaps resolved: X

   Completeness: PASS ✓  (or list remaining gaps)

   Import log: [vault]/_import-log.md
   Next step: /xmind-campaign:create-canvas to generate canvas files
   ```

## Important Rules

- NEVER write a file without logging it in `_import-log.md`
- NEVER skip a notes-bearing node without an explicit user confirmation and log entry
- NEVER skip a summary child without an explicit user confirmation and log entry
- If the vault directory structure does not match the expected layout, warn the user before creating new folders
