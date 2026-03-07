# Completeness Audit Checklist

Use this after every generate run. Work through each section in order.

---

## Pre-Audit: Verify Inputs

- [ ] `_extracted/full_tree.json` exists and is readable
- [ ] `_extracted/summary_report.txt` exists
- [ ] `_import-log.md` was written during this generate run
- [ ] Target vault path is correct and accessible

If any input is missing, stop and re-run the relevant extraction step.

---

## Section 1: Summary Subtree Coverage

This is the highest-risk area for missed content.

1. Open `_extracted/summary_report.txt`
2. Count total summary subtrees: **N = ___**
3. For each summary subtree, find its entry in `_import-log.md` (Generated, Merged, or Skipped)
4. Tally: Generated ___  | Merged ___ | Skipped ___ | **Missing ___**

**Pass condition:** Missing = 0

If Missing > 0: List each unaccounted summary subtree as a GAP. Do not proceed until all are resolved.

---

## Section 2: Notes-Bearing Node Coverage

1. Count notes-bearing nodes from the full tree (nodes where `notes.strip() != ""`)
   - Run: `python3 scripts/extract_xmind.py` and check output counts
   - Or: manually count from `_extracted/branch_XX.json` files
2. Total notes-bearing nodes: **N = ___**
3. From `_import-log.md`, count: Generated ___ | Merged ___ | Skipped ___
4. Sum = ___ (must equal N)
5. **Delta = N - Sum = ___**

**Pass condition:** Delta = 0

If Delta > 0: Walk the tree again looking for nodes not in the log.

---

## Section 3: Image Coverage

1. Identify all nodes with non-empty `image` field
2. For each: confirm image file exists at expected vault destination
3. Confirm `![[folder/filename]]` embed appears in the generated file

| Node | Expected image path | File exists? | Embedded? |
|------|--------------------|--------------|-|
| | | [ ] | [ ] |
| | | [ ] | [ ] |

**Pass condition:** All rows checked.

---

## Section 4: Spot-Check Content Verbatim

Pick 3 random notes-bearing nodes. For each:

1. Open the source node in the extracted JSON
2. Open the generated file
3. Confirm a representative phrase from the notes appears verbatim in the file

This catches truncation, encoding errors, and silent content drops.

| Node | Phrase checked | Found verbatim? |
|------|---------------|-----------------|
| | | [ ] |
| | | [ ] |
| | | [ ] |

---

## Section 5: Import Log Integrity

- [ ] `_import-log.md` exists in vault root
- [ ] This run's section is appended (not replacing previous runs)
- [ ] No "PENDING" entries remain in the Gaps table
- [ ] Every intentional skip has a reason recorded

---

## Section 6: File Validity Spot-Check

Pick 3 generated files (one scene, one NPC if generated, one other). For each:

- [ ] File has valid YAML frontmatter (no parse errors)
- [ ] File does NOT start with a `#` heading
- [ ] `tags` includes `imported`
- [ ] Content type tag is present and correct
- [ ] Chapter tag format is `chapter-XX` (not `Chapter 3` or `ch03`)

---

## Sign-Off

When all sections pass:

```
COMPLETENESS AUDIT PASSED
Run: [ISO datetime]
Branch: [branch name]
Notes-bearing nodes: N
Files generated: X | Merged: Y | Skipped: Z
Summary subtrees: N — all accounted for
Gaps: 0
```

Write this sign-off at the bottom of the run's section in `_import-log.md`.

---

## Common Gap Patterns & Resolutions

### Gap: Summary child has no direct title
XMind sometimes creates summary nodes with blank titles. The extraction script gives them `"?"` as a title.

**Resolution**: Look at their `path` field to find the parent. Classify by notes content. Name the file `[Parent Title] - Detail.md`.

### Gap: Node appears in both attached and summary
Rare but possible when XMind internal references are duplicated.

**Resolution**: Generate one file. Note in log that it covered both entries. Verify content from both references was included.

### Gap: Notes are only whitespace or newlines
The notes field has content but it's only `\n` or `\t` characters.

**Resolution**: Treat as empty → `skip`. Log with reason "whitespace-only notes".

### Gap: Node has children but no notes
An organizational node with no notes but whose children all have notes.

**Resolution**: Skip the parent node itself. Ensure all children are processed individually.

### Gap: Image-only node
A node with `image` set but `notes` empty.

**Resolution**: Generate a stub file with the image embedded and `needs-content` tag. Log it.
