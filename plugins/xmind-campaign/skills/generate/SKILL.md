---
name: generate
description: "Use when converting extracted XMind branches into Obsidian campaign files. Classifies every relevant node, confirms writes, logs provenance, and audits completeness."
version: 0.2.0
author: Christian Brandborg
license: 0BSD
compatibility: "Requires xmind-campaign extraction output and an accessible Obsidian vault."
---

# Generate Obsidian campaign files

Convert extracted XMind content into reviewed, traceable Obsidian Markdown files.

## Required companion skills

In Hermes, first call `skills_list`, identify this plugin's qualified sibling names ending in `:content-mapping`, `:scene-writing`, and `:completeness-rules`, then load those exact names with `skill_view`. In Claude Code or Codex, load the same sibling skills through that host's plugin skill selector. Their classification, formatting, and coverage rules are mandatory for this workflow.

## Preconditions

1. Require the selected `_extracted/full_tree.json` and `_extracted/summary_report.txt`.
2. Obtain and validate the target vault path. Never infer a writable vault from unrelated files.
3. Select one `branch_XX.json` or all branch files. If ambiguous, ask.
4. Read existing `_import-log.md` before deciding whether a node was already handled.

## Per-branch procedure

1. Report branch title, recursive node count, notes-bearing node count, image count, and summary-subtree count.
2. Walk both `children` and `summary_children`. Classify every relevant node with `content-mapping` and record node path, type, confidence, proposed file, and whether content is generated, merged, or skipped.
3. Ask the user to resolve low-confidence classifications. Show the complete classification table and obtain approval before writing.
4. Obtain the chapter folder name for chapter-scoped content and construct paths under `Chapters/<chapter> - Canvas/Scenes/`.
5. Before creating directories or files, list the exact destinations. For every existing target, offer overwrite, skip, merge, or inspect-diff; never overwrite silently.
6. Generate each approved file using `scene-writing`. Preserve source notes and all summary content. Copy referenced images from `_extracted/resources/` to the folder selected by `content-mapping`, verify the copy, then add the Obsidian embed.
7. Append a provenance row to `_import-log.md` for every generated, updated, merged, or intentionally skipped node. Include source node path, output path, type, and reason where relevant.
8. Run the `completeness-rules` audit for the branch. Resolve every gap interactively before proceeding to another branch.

## Safety rules

- Do not write outside the confirmed vault.
- Do not silently replace existing files.
- Do not skip notes-bearing or summary nodes without explicit confirmation and a logged reason.
- Do not claim an image was copied until the destination exists.
- Warn before creating a structure that differs from the expected vault layout.

## Final report

Report exact counts of files created, updated, skipped, and merged; images copied; summary subtrees covered; and unresolved gaps. Include the import-log path. Completeness passes only when the companion audit finds zero gaps.
