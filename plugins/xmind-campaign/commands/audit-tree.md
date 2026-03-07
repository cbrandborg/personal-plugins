---
name: audit-tree
description: Display the full XMind node tree with notes lengths, image flags, and summary children highlighted. Use before generate to review what will be created.
argument-hint: "[branch number (optional, e.g. 00)]"
allowed-tools: [Read, Bash, Glob]
---

# Audit XMind Node Tree

Display the extracted node tree so the user can review content before generating files.

## Steps

1. **Find extraction output**
   - Look for `_extracted/` directory near recent `.xmind` files
   - If not found, tell user to run `/xmind-campaign:extract` first

2. **Determine scope**
   - If a branch number argument was provided (e.g. `00`), read only `_extracted/branch_00.json`
   - Otherwise read `_extracted/full_tree.json`

3. **Display tree**
   Display in this format, indented by depth:

   ```
   Root Topic
     Branch 0: Act 1 — The Arrival [nodes:42, notes_chars:8432]
       ◆ Market Square [notes:312] ← has content
         ○ Guard Patrol [notes:0]
         ◆ Merchant Bram [notes:187, IMG] ← has content + image
       ▶ [SUMMARY] Encounter: Pickpocket [notes:445] ← SUMMARY CHILD
         ◆ Tactics [notes:220]
     Branch 1: Act 2 ...
   ```

   Legend:
   - `◆` = has notes or image (will produce output)
   - `○` = no notes, no image (will be skipped)
   - `▶ [SUMMARY]` = summary child (bracket grouping — high risk of being missed)
   - `[IMG]` = has an embedded image

4. **Summary statistics**
   After the tree, show:
   ```
   Nodes with notes: X
   Nodes with images: X
   Summary subtrees: X
   Nodes that will be skipped: X

   Files to generate (estimated): X
   ```

5. **Flag concerns**
   - If any SUMMARY node has notes but is deeply nested (depth > 4), highlight it: "⚠ Deep summary node — verify it gets covered"
   - If note character count is very high on a single node (> 3000 chars), flag it: "⚠ Large node — may need splitting"

6. **Prompt**
   After displaying, ask:
   ```
   Review the tree above. When ready, run /xmind-campaign:generate to start creating vault files.
   You can also run /xmind-campaign:audit-tree 01 to inspect a specific branch.
   ```
