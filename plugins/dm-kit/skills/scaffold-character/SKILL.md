---
name: scaffold-character
description: "Runs when the user wants to create a new character file in the campaign vault. Trigger phrases include: 'create a character', 'create a new NPC', 'create a new NPC called', 'add an NPC', 'scaffold a PC', 'new character for the party', 'new player character', 'add a new PC', 'add a new PC to the party', 'write up [name]', 'create a character file', 'create a character file for', 'I need to create a character file', 'I need to create a character', 'start a character file', 'start a character file for', 'make a new character file', 'make a character file', 'create an NPC for', '/dm-kit:scaffold-character'. Also triggers for any request to scaffold, initialize, or write up a new character document in the Characters/ folder — whether it's a major villain, a minor NPC, or a new player character joining the party. Creates a character markdown file using the correct PC or NPC template."
argument-hint: "<name> --type npc|pc [--chapter <NN>] [--faction ally|enemy|neutral|contested] [--major|--minor]"
allowed-tools: [Read, Write, Glob, Bash]
---

# Scaffold Character

Create an NPC or PC file using the right template. Both live in `<VAULT>/Characters/`.

## Arguments

- `<name>` — the character's name, as it appears on the file (e.g. `"Marshall Garrick"`). Quote if it contains spaces.
- `--type npc|pc` — **required**. Determines which template is used.
- `--chapter <NN>` — optional. The chapter number where they're first met. Used for the `first-met` field.
- `--faction ally|enemy|neutral|contested` — optional, NPC only. Defaults to `neutral` if not given.
- `--major` / `--minor` — optional. Marks whether they're a major recurring character or a minor one-scene NPC. Defaults to `--minor` for NPCs and always `--major` for PCs.

## Execution steps

### 1. Detect the vault

```bash
VAULT="$(${CLAUDE_PLUGIN_ROOT}/scripts/detect-vault.sh)" || { echo "Not inside a D&D vault."; exit 1; }
```

### 2. Check for collision

If `<VAULT>/Characters/<Name>.md` already exists, stop and tell the user. Do not overwrite existing character files.

### 3. Detect portrait image

Glob for `<VAULT>/Characters/<Name>.{png,jpg,jpeg}`. If one exists, note its extension and embed it in the file header.

### 4. Write the file using the right template

Use **NPC template** for `--type npc` and **PC template** for `--type pc`. See below.

### 5. Confirm

Report to the user:
- Created file path
- Whether a portrait image was detected and embedded
- Next steps: "Use `write-character` for voice and dialogue, or fill in the fields directly."

## Templates

### NPC Template

```markdown
---
type: npc
faction: <faction>
first-met: chapter-<NN>
major: <true|false>
appearances:
  - chapter-<NN>
aliases: []
---

<!-- If portrait exists: -->
![[Characters/<Name>.png]]

**Role:** [Kort titel eller funktion]
**Location:** [[Location Name]]
**Faction:** <faction>

## Appearance

[Dansk fysisk beskrivelse — ét detaljerende kendetegn, der bliver husket. 2-4 sætninger.]

## Personality

[Dansk — én manerisme, én gentagen vending, ét registrer (formel/vulgær/tøvende), ét hemmeligt motiv.]

## Voice

[Dansk — hvordan lyder de? Filler-ord, grammatiske tics, metaforbank? Kort.]

## Dialogue

### [Emne / situation]
> "[Dansk replik i deres stemme]"

### [Andet emne]
> "[Dansk replik]"

<!-- Optional — only if combat-relevant -->
## Stats

- **AC:** X | **HP:** XX | **CR:** X
- **Speed:** Xft
- **Attack:** [Name] +X to hit, Xd6+X [type] damage

## Backstory

[Dansk eller engelsk — baggrund, hvordan de er endt her, hvad der former dem.]

## DM Notes

[English — motivations, secrets, plot hooks, how they react to PC actions, faction shifts.]
```

### PC Template

```markdown
---
type: pc
player-name: [Spillerens navn]
character-sheet: [D&D Beyond URL — just paste it here]
first-met: chapter-<NN>
major: true
appearances:
  - chapter-<NN>
aliases: []
---

<!-- If portrait exists: -->
![[Characters/<Name>.png]]

**Class:** [Class, Level X]
**Race:** [Race]
**Party Role:** [Tank / Damage / Support / Face / etc.]

## Appearance

[Dansk fysisk beskrivelse.]

## Backstory

[Dansk eller engelsk — hvor kommer de fra, hvad driver dem, hvad er deres åbne tråde?]

## Personal Arc

[DM-facing: what is this character's unresolved personal thread? What payoff is promised? What's the emotional endpoint we're building toward?]

## Items (notable)

- [Item or feature the DM needs to remember — not a full inventory]

## Personality / Voice (optional)

[Kort dansk note hvis der er en distinkt stemme eller manerisme værd at huske.]

## DM Notes

[English — private notes about the character: secrets the player has shared, hooks for later, connections to NPCs, faction ties.]
```

## Field meanings

### For both

- **`first-met`**: the chapter number where this character was introduced (or will be). Used by Claude in future sessions to gauge how much shared history exists.
- **`appearances`**: growing list of chapters. Add entries over time.
- **`major: true|false`**: major characters get full treatment; minor NPCs are lean.

### NPC-specific

- **`faction`**: one of `ally`, `enemy`, `neutral`, `contested`. "Contested" is reserved for NPCs whose loyalty is actively being fought over or shifting — the most interesting label.

### PC-specific

- **`character-sheet`**: paste the D&D Beyond URL. dm-kit does not scrape it. If Claude needs stat details mid-session, the user can paste them or Claude can `WebFetch` the public page.
- **`personal-arc`**: the DM's plan for this PC's personal story. Kept private from the player.

## Error handling

- **No vault**: ask user to `cd` into a campaign.
- **Missing `--type`**: stop and ask explicitly — this determines which template to use.
- **File collision**: don't overwrite. Tell the user the file exists and offer to show it or suggest a different name.
- **Invalid faction value** (NPCs): default to `neutral` and note it.

## Cross-references

- `write-character` — for guidance on developing NPC voice, dialogue, and mannerisms.
- `scaffold-scene` — to create the scene where this character first appears.
- `vault-navigate` — for the full Characters/ folder convention.
