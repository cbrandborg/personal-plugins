---
name: vault-navigate
description: "**Auto-triggers on any question about campaign state, vault structure, or navigation inside a D&D vault.** Natural triggers include 'what vault am I in', 'which vault', 'which campaign', 'where am I', 'what campaign are we in', 'where are we', 'what project is this', 'show me the chapters', 'list characters', plus any mention of 'this vault', 'this campaign', 'the chapter', 'the scene folder'. Also loads as supporting context whenever another dm-kit skill runs (scaffold-*, write-*, brainstorm, dnd-lookup). Teaches Claude how to detect the current vault, folder structure, canvas conventions, and which files to read first. **Critical: preserve the CWD path style — never swap between Google Drive and Documents mirrors.**"
---

# Vault Navigation

Every D&D campaign vault under `DnD/` follows the same structure. This skill teaches Claude how to orient itself in any of them.

## Detecting the current vault

Run the helper script to find the vault root by walking up from the current working directory:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/detect-vault.sh
```

It prints the absolute path of the nearest directory containing both `CLAUDE.md` and `Chapters/`, or exits 1 if not inside any vault.

Use this at the start of any task that needs vault context. Do not hardcode campaign names — the same skills work for *The Plague of Myrkul*, *The Fractured Crown*, *The Bounty of Dunbar*, or any future campaign.

### CRITICAL: preserve the CWD path style

Some users have the same vault mounted at multiple absolute roots (e.g. Google Drive at `~/My Drive/sync/private-obsidian/DnD/...` AND locally at `~/Documents/private-obsidian/DnD/...`). These are DIFFERENT absolute paths that refer to the same files.

**Always use the path that `detect-vault.sh` returns**, because it walks up from the literal `$PWD` without resolving symlinks. Never substitute a different absolute root even if you believe it's equivalent. All file Writes, Edits, and Reads must stay under that exact returned path.

Why this matters: the `canvas-sync-hook` and Claude Code's own path validation compare absolute paths. A Write to the Documents mirror while CWD is the Drive mirror will look like a file outside the project root and may trigger false warnings or blocks.

Rule of thumb: if `pwd` prints `~/My Drive/.../The Plague of Myrkul/Ideas`, every path you use must start with `~/My Drive/.../The Plague of Myrkul/`, not `~/Documents/.../The Plague of Myrkul/`. If Claude Code offers additional working directories, **ignore them** — always use the one matching `detect-vault.sh`'s output.

## Read these first

Once you know the vault root, read in this order for any task that touches campaign content:

1. **`<vault>/CLAUDE.md`** — conventions specific to this vault (language split, color codes, etc.). Usually very similar across vaults but may carry campaign-specific notes.
2. **`<vault>/_Campaign Overview.md`** — the live state snapshot. Who the party is, where they are, what threads are active. This is the single source of truth for current state.
3. **`<vault>/Campaign_Summary_Updated.md`** (if present) — detailed play-by-play history.

For finale or major planning work, also read `<vault>/Ideas/` for brainstorms and in-progress notes.

## Folder layout

```
<vault>/
├── CLAUDE.md                      # Vault conventions
├── _Campaign Overview.md          # Live state (read first for current-state tasks)
├── Campaign_Summary_Updated.md    # History
├── Chapters/
│   ├── 01 - <Name>/               # Chapter 1 (may be flat markdown for lore-only)
│   ├── 02 - <Name>/
│   │   ├── <Name>.canvas          # Obsidian canvas (JSON) — visual map
│   │   └── Scenes/                # Atomic scene markdown files
│   │       ├── 01 - Scene.md
│   │       ├── 01a - Sub Scene.md
│   │       └── ...
│   └── ...
├── Characters/                    # One .md per NPC/PC + images
├── Locations/                     # Location images
├── Items/                         # Magic items
├── Concepts/                      # Campaign mechanics
├── Ideas/                         # Drafts and brainstorms (active planning)
└── Outdated/                      # Frozen archive — do NOT treat as canon
```

## Hard rules (non-negotiable)

These apply to every vault. Any dm-kit skill that writes files must respect them.

### Canvas+Scene sync
A new scene file is **invisible in Obsidian** until it has a matching node in the chapter's `.canvas` file. Always update both together. Use `scripts/add-scene-to-canvas.py` — never hand-edit the canvas JSON.

### Danish / English split
- **Danish**: all player-facing text — read-aloud descriptions, NPC dialogue, atmospheric prose, scene openings.
- **English**: all mechanics — DCs, HP, AC, CR, stat blocks, DM notes in `> **DM Note:**` blockquotes, skill-check descriptions.
- Preserve a mix if that's what the user has — don't consolidate.

### No H1 title in scene files
Scene files live inside a chapter's `Scenes/` folder. Obsidian canvas cards use the filename as the label, so a `# Title` at the top causes a duplicated title. Scene files must start directly with description text or a `##` subheading.

### Node sizing on canvas
Canvas nodes that reference files must have `height` between 250 and 600 px. Smaller nodes render empty. The `add-scene-to-canvas.py` script enforces this.

### Color codes (canvas text nodes)
- `"1"` chapter title / section header
- `"2"` next chapter link
- `"4"` NPC character reference
- `"5"` dialogue label
- `"6"` player choice / decision point

### Path quoting
Chapter folders contain spaces and apostrophes (e.g. `02 - Durgan's Rest`). Always quote paths in shell commands.

## Scene filename convention

- Numbered with two-digit prefix: `01 - Scene Name.md`, `02 - Scene Name.md`
- Sub-scenes use a letter suffix: `01a - Sub Scene.md`, `01b - Another Sub.md`
- Use narrative order, not creation order
- Hyphens or underscores are both tolerated (you'll see both in older files); prefer spaces with hyphens for new scenes

## Routing tasks to files

When the user asks for something, use this quick routing:

| Task | Files involved |
|---|---|
| Create a new scene | `scaffold-scene` skill → writes `<vault>/Chapters/<NN - Name>/Scenes/<NN - Title>.md` + updates `.canvas` |
| Create a new chapter | `scaffold-chapter` skill → creates `<vault>/Chapters/<NN - Name>/` structure |
| Create an NPC or PC | `scaffold-character` skill → writes `<vault>/Characters/<Name>.md` |
| Write scene prose (read-aloud, atmosphere) | `write-scene` skill for guidance |
| Write NPC voice/dialogue | `write-character` skill for guidance |
| Brainstorm options (scene hooks, encounters, plot twists) | `brainstorm` skill |
| Look up a monster, spell, rule, DC | `dnd-lookup` skill |
| Review existing scene for conventions | The `scene-reviewer` agent triggers automatically after Write/Edit |
