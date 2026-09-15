---
name: scaffold-chapter
description: "Runs when the user wants to create a new chapter in the campaign vault. Trigger phrases include: 'create a new chapter', 'create a new chapter called', 'scaffold chapter', 'scaffold chapter X', 'add chapter', 'add a new chapter', 'add a new chapter to this vault', 'I need to start a new chapter', 'set up the folder and canvas for chapter', 'set up the folder for chapter', 'make a new chapter folder', 'make a new chapter folder with', 'I want a new chapter', 'new chapter container', 'set up a new chapter container', 'start chapter [N]', '/dm-kit:scaffold-chapter'. Also triggers for any request to initialize the folder structure, canvas file, and Scenes/ directory for a new chapter number — including vague phrasings like 'set up chapter 10' or 'get chapter 11 ready'. Creates the folder, .canvas file with a title node, Scenes/ directory, and a starter '01 - Arrival' scene."
argument-hint: "<chapter-number> <chapter-name>"
allowed-tools: [Read, Write, Edit, Glob, Bash]
---

# Scaffold Chapter

Create a new chapter from scratch: folder, canvas file, Scenes/ directory, starter scene.

## Arguments

- `<chapter-number>` — the numeric prefix (e.g. `10`, `11`). Use two digits.
- `<chapter-name>` — the chapter title (e.g. `"Ruined Observatory"`, `"The Long Road"`). Quote if it contains spaces.

## Execution steps

### 1. Detect the vault

```bash
VAULT="$(${CLAUDE_PLUGIN_ROOT}/scripts/detect-vault.sh)" || { echo "Not inside a D&D vault."; exit 1; }
```

### 2. Check for collision

Glob `<VAULT>/Chapters/<NN> - */`. If any match, stop and tell the user — don't overwrite an existing chapter.

### 3. Create the folder

```bash
mkdir -p "<VAULT>/Chapters/<NN> - <Name>/Scenes"
```

### 4. Create the canvas file

The canvas is named `<Name>.canvas` (same as the chapter name, no prefix). Seed it with a single title text node using color `"1"`:

```json
{
  "nodes": [
    {
      "id": "<random-16-hex>",
      "type": "text",
      "text": "# Chapter <NN>: <Name>",
      "x": 0,
      "y": -400,
      "width": 500,
      "height": 100,
      "color": "1"
    }
  ],
  "edges": []
}
```

Generate the node ID with Python's `uuid.uuid4().hex[:16]` (you can inline this via `python3 -c 'import uuid; print(uuid.uuid4().hex[:16])'`).

### 5. Create the starter scene

Write `<VAULT>/Chapters/<NN - Name>/Scenes/01 - Arrival.md`:

```markdown
---
tags:
  - scene
  - chapter-<NN>
aliases: []
---

[Dansk åbning af kapitlet — første gang spillerne ankommer til <location>. Sæt atmosfæren. Én sans først.]

## [Den første scene]

[Yderligere dansk beskrivelse.]

> **DM Note:** This is the chapter opener. Keep it short. Hand off to player decisions quickly.
```

### 6. Add the starter scene to the canvas

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/add-scene-to-canvas.py \
  "<VAULT>/Chapters/<NN - Name>/<Name>.canvas" \
  "DnD/<campaign-name>/Chapters/<NN - Name>/Scenes/01 - Arrival.md"
```

### 7. Update the chapter index (optional)

If `<VAULT>/_Campaign Overview.md` exists and contains a chapter index table (grep for `| # | Chapter |`), add a new row for this chapter. Use status `Not Played` and leave the events column empty for the user to fill in. Do NOT modify the overview if the structure doesn't match — just skip and report it.

### 8. Confirm

Report to the user:
- Created folder path
- Canvas file path
- Starter scene path
- Whether the overview was updated
- Suggestion: "Open the canvas in Obsidian to verify, then use `scaffold-scene` to add more scenes."

## Error handling

- **Chapter number already exists**: stop, list the existing chapter, ask if the user wants a different number.
- **No vault detected**: same as scaffold-scene — ask user to `cd` into a campaign.
- **Invalid chapter name** (empty, just whitespace): reject with a message.

## What this skill does NOT do

- Does not create Dialogues/ folders (legacy pattern, not used in new chapters).
- Does not write a full chapter outline — just the starter scene. Use `brainstorm` to generate chapter structure ideas, then `scaffold-scene` repeatedly to build it out.
- Does not auto-link this chapter to the previous chapter's canvas. That's a manual "next chapter" link the user places in the previous chapter's canvas.

## Cross-references

- `scaffold-scene` — to add more scenes once the chapter shell exists.
- `brainstorm` — to generate ideas for what the chapter should contain before scaffolding.
- `vault-navigate` — for the full vault structure reference.
