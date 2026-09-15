---
name: audit-tree
description: "Use when reviewing extracted XMind content before generation. Displays attached and summary nodes, notes and images, risk flags, and estimated output coverage."
version: 0.2.0
author: Christian Brandborg
license: 0BSD
compatibility: "Requires extraction output produced by the xmind-campaign extract skill."
---

# Audit an extracted XMind tree

Review the complete node hierarchy before any campaign files are generated.

## Procedure

1. Locate the intended `_extracted/` directory. Do not guess between multiple candidates; ask the user to choose.
2. Require `full_tree.json`. For a requested branch such as `01`, require and read `branch_01.json`; otherwise read the full tree.
3. Traverse both `children` and `summary_children` recursively. Never treat summary children as ordinary attached children in the report.
4. Display the tree using:
   - `◆` for a node with notes or an image
   - `○` for a node with neither notes nor an image
   - `▶ [SUMMARY]` for every summary child
   - `[IMG]` when an image reference is present
5. Include each node's notes-character count. For top-level branches include total recursive node and notes-character counts.
6. Report exact totals for all nodes, notes-bearing nodes, image-bearing nodes, summary subtrees, empty nodes, and estimated files.
7. Flag summary nodes deeper than four levels and nodes with more than 3,000 notes characters.

## Output example

```text
Root Topic
  Branch 0: Chapter [nodes:42, notes_chars:8432]
    ◆ Market Square [notes:312]
      ○ Guard Patrol [notes:0]
    ▶ [SUMMARY] Encounter [notes:445]
```

Estimated files are not a completeness result: classification can merge one node into another file or split a multi-type node. Preserve node paths so the later import log can prove coverage.

## Completion

Identify the audited file or branch and state every concern. Recommend generation only after the user has reviewed the classification scope.
