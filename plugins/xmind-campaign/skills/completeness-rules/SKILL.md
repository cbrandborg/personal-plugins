---
name: completeness-rules
description: "This skill should be used when the user asks to \"check completeness\", \"verify nothing was missed\", \"audit the import\", \"did we miss any nodes\", \"check summary subtrees\", \"run the completeness check\", or after generating scene files from an XMind export. Critical: ensures every notes-bearing node and every summary subtree has a corresponding output file."
version: 0.1.0
---

# Completeness Rules — Ensuring Nothing Is Missed

## Purpose

After generating files from an XMind export, verify with certainty that no notes content and no summary subtree was silently skipped. This is the most critical check in the pipeline.

## The Two Non-Negotiable Rules

### Rule A: Every notes-bearing node must produce output

A node "bears notes" if `len(node.notes.strip()) > 0`. Every such node must either:
- Have a corresponding generated file, OR
- Have been explicitly marked `skip` with a logged reason, OR
- Have its content merged into a parent file (documented in the log)

### Rule B: Every summary subtree must be accounted for

XMind stores content in TWO child arrays: `attached` and `summary`. Summary nodes (bracket groupings) are easy to miss and often contain stat blocks, dialogues, or encounter details. Every node appearing in any `summary_children` list must either:
- Have a corresponding generated file, OR
- Be included as a section within a parent file (documented), OR
- Be explicitly logged as intentionally skipped

## Completeness Audit Process

Run this audit automatically after every `generate` command.

### Step 1: Build the expected set

Walk the full extracted tree (`full_tree.json`) and collect every node that must produce output:

```python
def collect_required(node, required=None):
    if required is None:
        required = []
    # Notes-bearing nodes
    if node.get('notes', '').strip():
        required.append(node)
    # Summary children — always collect regardless of notes
    for sc in node.get('summary_children', []):
        required.append(sc)
        collect_required(sc, required)
    for c in node.get('children', []):
        collect_required(c, required)
    return required
```

### Step 2: Build the actual set

Collect all files generated in this run from the import log (`_import-log.md`) or by scanning the vault output directories.

### Step 3: Diff

For each required node, check:
1. Is there a generated file whose source node path matches?
2. Or is there a log entry marking it as merged/skipped with reason?

Anything not covered → **GAP**.

### Step 4: Report gaps

Report every gap immediately. Do not continue or summarise until all gaps are resolved. For each gap:

```
GAP: [node.path]
  Title: [node.title]
  Notes length: [X chars]
  Notes preview: "[first 80 chars]..."
  Summary child of: [parent path or "n/a"]
  Action needed: [Generate file | Merge into parent | Confirm skip]
```

### Step 5: Resolve each gap

For each reported gap, present the options to the user:
- **Generate now** — create the missing file using scene-writing rules
- **Merge** — fold content into an existing related file (user specifies which)
- **Skip with reason** — log the node as intentionally excluded (user must confirm)

Do not auto-resolve gaps. Always ask.

## Summary Subtree Verification (Critical)

Summary subtrees are the most common source of missed content. After building the expected set, run a dedicated check:

1. Open `summary_report.txt` from the extraction output
2. For each summary subtree listed, verify a file or log entry exists
3. If `summary_report.txt` shows N summary subtrees, the completeness check must account for all N

If `summary_report.txt` is not present, re-run extraction before proceeding.

## Import Log Format

Every generate run appends to `_import-log.md` in the vault root. The log must capture enough to reconstruct the audit trail.

```markdown
## Import Run — [ISO date]

**Source:** [path to .xmind file]
**Branch:** [branch name processed]
**Chapter:** [chapter folder]

### Generated Files
| Node Path | Output File | Type |
|-----------|-------------|------|
| Root/Act1/Town/Market | Chapters/01 - Town - Canvas/Scenes/01 - Market.md | scene |
| Root/Act1/NPCs/Aldric | Characters/Aldric.md | npc |

### Merged Into Parent
| Node Path | Merged Into | Reason |
|-----------|-------------|--------|
| Root/Act1/Town/Market/Guard | Chapters/01 - Town - Canvas/Scenes/01 - Market.md | short NPC, no separate file needed |

### Skipped
| Node Path | Reason |
|-----------|--------|
| Root/Act1/NPCs | Organizational node, no notes |

### Gaps (unresolved)
| Node Path | Status |
|-----------|--------|
| Root/Act1/Summary/Encounter | PENDING |

### Summary Subtrees
| Summary Title | Parent | Covered By |
|--------------|--------|------------|
| Combat: Bandit Ambush | Root/Act1/Road | Scenes/02 - Road Ambush.md |
```

## Verification Checklist

After every generate run, confirm all boxes before declaring the import complete:

- [ ] `summary_report.txt` exists and has been reviewed
- [ ] Node count from `full_tree.json` vs files generated + merged + skipped = 0 gaps
- [ ] Every summary subtree from `summary_report.txt` appears in the log
- [ ] No GAP entries remain in the import log
- [ ] Spot-check: 3 random notes-bearing nodes — open their file and confirm notes appear verbatim
- [ ] All images from `image`-bearing nodes are present in correct vault folder

## Additional Resources

- **`references/audit-checklist.md`** — Printable audit checklist and edge case handling
