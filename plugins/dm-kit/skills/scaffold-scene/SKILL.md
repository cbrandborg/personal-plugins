---
name: scaffold-scene
description: "Runs when the user says 'create a new scene', 'scaffold a scene', 'add a scene to chapter X', 'new scene for chapter Y', or '/dm-kit:scaffold-scene ...'. Creates a new scene markdown file in the correct chapter's Scenes/ folder AND adds a matching file node to the chapter's .canvas JSON in one atomic operation. Enforces the canvas+scene sync hard rule."
argument-hint: "<chapter-number> <scene-title> [--type scene|encounter|puzzle] [--sub <parent-number>]"
allowed-tools: [Read, Write, Edit, Glob, Bash]
---

# Scaffold Scene

Create a new scene file AND its matching canvas node in one operation. This skill is the mandatory path for adding scenes — manual `Write` of a scene file without the canvas update violates the hard rule.

## Arguments

- `<chapter-number>` — the numeric prefix of the chapter folder (e.g. `09` or `9`).
- `<scene-title>` — the title, without the number prefix. Quote if it contains spaces.
- `--type scene|encounter|puzzle` — optional. Defaults to `scene`. Controls the template and tags.
- `--sub <parent-number>` — optional. Create a sub-scene (e.g. `01a`) under an existing parent (e.g. `01`). Auto-picks the next letter.

## Execution steps

### 1. Detect the vault

```bash
VAULT="$(${CLAUDE_PLUGIN_ROOT}/scripts/detect-vault.sh)" || { echo "Not inside a D&D vault. cd into one first."; exit 1; }
```

### 2. Find the chapter folder

Use `Glob` to find chapter folders matching the number:

```
Pattern: <VAULT>/Chapters/<NN> - */
```

If there's exactly one match, use it. If zero or multiple, tell the user and list the candidates.

### 3. Find the canvas file

The canvas file is named `<Chapter Name>.canvas` at the root of the chapter folder. Use `Glob`:

```
Pattern: <CHAPTER>/**.canvas
```

If there's no `.canvas` file, the chapter may be pre-canvas (flat markdown — chapter 01 is often like this). In that case, tell the user and ask whether to run `scaffold-chapter` instead or just create a flat .md file.

### 4. Determine the scene number

List existing scenes in `<CHAPTER>/Scenes/` and pick the next number:

- For normal scenes: next integer above the highest existing two-digit prefix (e.g. if `07`, `08` exist, use `09`).
- For sub-scenes (`--sub 01`): look at existing `01a`, `01b`, etc. and pick the next letter.

Use `ls` or `Glob` with the pattern `<CHAPTER>/Scenes/*.md`.

### 5. Build the scene file path and vault-relative path

- **Absolute path**: `<CHAPTER>/Scenes/<NN> - <Title>.md`
- **Vault-relative path** (for the canvas node, must start from the Drive mount): usually `DnD/<Campaign>/Chapters/<NN - Chapter>/Scenes/<NN - Title>.md`. Derive this by stripping everything before `DnD/` from the absolute path.

### 6. Write the scene file

Use the template matching the `--type` argument (see **Templates** below). Respect the hard rules:
- **No `# Title` header**
- YAML frontmatter with tags
- Danish placeholder prose
- English DM note blockquote
- Length target: start around 80–200 words of placeholder that the user can expand

### 7. Add the node to the canvas

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/add-scene-to-canvas.py \
  "<canvas-file>" \
  "<vault-relative-scene-path>"
```

The script prints the new node's ID. Include it in the confirmation message to the user.

### 8. Confirm

Report to the user:
- The created file path
- The new canvas node ID
- A one-line reminder that the canvas is updated and the file is ready for prose

## Templates

### Scene (default)

```markdown
---
tags:
  - scene
  - chapter-<NN>
aliases: []
---

[Dansk åbning — sæt atmosfæren, én sans først, én lille underlighed, én krog til spillerne. 2-5 sætninger.]

## [Valgfrit undersectionsnavn]

[Yderligere dansk beskrivelse eller overgang.]

### Check: [Færdighed] DC XX
**Success:** [Resultat]
**Failure:** [Resultat]

## Player Choices
- [Valg 1]
- [Valg 2]

> **DM Note:** [English — triggers, timing, what's hidden, how to react to player creativity.]
```

### Encounter (`--type encounter`)

```markdown
---
tags:
  - scene
  - encounter
  - combat
  - chapter-<NN>
aliases: []
---

[Dansk åbning — ro før bruddet. Én normal sætning. Én sætning der bryder den.]

## Setup

**Trigger:** [Hvad udløser encounteret]
**Location:** [[Location Name]]

## Enemies

### [Enemy Name]
- **AC:** X | **HP:** XX | **CR:** X | **Speed:** Xft
- **Attack:** [Name] +X to hit, Xd6+X [type] damage
- **Special:** [Ability] — [description]

## Tactics

[English DM notes: priorities, formations, escape conditions.]

## Resolution

**Victory:** [Dansk eller engelsk — hvad sker der hvis spillerne vinder]
**Defeat/Retreat:** [Hvad sker der ellers]

> **DM Note:** [Any scaling or alternative outcomes.]
```

### Puzzle (`--type puzzle`)

```markdown
---
tags:
  - scene
  - puzzle
  - chapter-<NN>
aliases: []
---

[Dansk setup — beskriv hvad spillerne ser. 3-5 sætninger.]

## The Challenge

[English: hvad skal spillerne mekanisk gøre?]

### Check: [Skill] DC XX
**Success:** [Dansk outcome]
**Failure:** [Outcome]

## Solution

[English: intended solution and DM guidance.]

## Rewards / Consequences

[What happens on success/failure.]
```

## Error handling

- **No vault**: "Not inside a D&D campaign vault. `cd` into one first."
- **Chapter not found**: list the chapters that do exist and ask which one.
- **Canvas missing**: the chapter may be flat-markdown (pre-canvas). Suggest `scaffold-chapter` or ask whether to create a plain scene file.
- **Scene number collision**: should not happen if you auto-pick the next number, but if the user passed a specific number that exists, warn and stop.
- **add-scene-to-canvas.py fails**: show the error, keep the scene file (don't delete — the user may still want it), suggest manual canvas inspection.

## Cross-references

- `write-scene` — for the prose once the file is scaffolded.
- `scaffold-chapter` — if the chapter doesn't exist yet.
- The `canvas-sync` hook will warn if you somehow bypass this skill and write a scene file directly.
