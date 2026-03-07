---
name: content-mapping
description: "This skill should be used when the user asks to \"classify nodes\", \"map content\", \"decide where this goes\", \"which folder\", \"what type is this node\", or when processing XMind nodes and determining how they map to Obsidian vault structure for a DnD campaign. Use during extract, audit, and generate phases of the xmind-campaign pipeline."
version: 0.1.0
---

# Content Mapping — XMind Nodes to Obsidian Vault

## Purpose

Map every node from an extracted XMind tree to the correct content type and Obsidian vault location. Apply deterministic classification rules first; ask the user only when genuinely ambiguous.

## Content Types

Each XMind node maps to exactly one of these types:

| Type | Description | Vault Folder |
|------|-------------|--------------|
| `scene` | Location-based narrative moment, read-aloud description | `Chapters/XX - Name - Canvas/Scenes/` |
| `encounter` | Combat or structured conflict with stat blocks, triggers, resolution | `Chapters/XX - Name - Canvas/Scenes/` |
| `puzzle` | Skill challenge or puzzle with mechanics, DCs, outcomes | `Chapters/XX - Name - Canvas/Scenes/` |
| `npc` | Named character with dialogue, personality, or stat block | `Characters/` |
| `location` | Named place that exists independently of a single chapter moment | `Locations/` |
| `item` | Named magic item, weapon, artifact, or consumable | `Items/` |
| `concept` | Campaign mechanic, faction, lore element, or rule variant | `Concepts/` |
| `skip` | Structural/organizational node with no notes and no image — not a file | *(no output)* |

## Classification Rules (apply in order)

### Rule 1: Check for `skip`

Mark a node `skip` if ALL of the following are true:
- `notes` field is empty or whitespace only
- `image` field is empty
- No `summary_children` contain notes or images
- Node is clearly organizational (e.g. "Act 1", "Encounters", "NPCs")

Do not skip nodes that have meaningful title-only content if children reference them.

### Rule 2: Classify by explicit signals in title or parent path

Apply these patterns to `node.title` and `node.path`:

| Signal pattern | → Type |
|---------------|--------|
| Title starts with a proper name + "," or role ("Aldric, the Blacksmith") | `npc` |
| Title contains "Encounter:", "Combat:", "Ambush", "Bestiary" | `encounter` |
| Title contains "Puzzle:", "Challenge:", "Riddle", "Trap" | `puzzle` |
| Title contains "Item:", "Loot:", "[weapon name]", "[spell name]" | `item` |
| Title contains "Location:", place name that recurs across chapters | `location` |
| Parent path contains "NPCs" or "Characters" | `npc` |
| Parent path contains "Encounters" | `encounter` |
| Parent path contains "Items" or "Loot" | `item` |
| Parent path contains "Locations" | `location` |
| Parent path contains "Concepts" or "Mechanics" | `concept` |

### Rule 3: Classify by notes content

If title signals are inconclusive, examine the `notes` field:

- Notes open with atmospheric prose in Danish → `scene`
- Notes contain stat blocks (AC, HP, CR, Attack) → `encounter` or `npc`
- Notes contain DC checks with success/failure branches → `puzzle` or `scene`
- Notes describe a named place in general terms (not a specific moment) → `location`
- Notes describe an item's properties, attunement, or lore → `item`
- Notes describe faction rules, campaign-wide mechanics → `concept`

### Rule 4: Ask the user when ambiguous

Ask when:
- A node contains both location description AND NPC introduction (could be `scene` or both `location` + `npc`)
- A node could be classified as either `scene` or `encounter` based on notes alone
- A node has no title signal and notes are minimal

Present the node path, title, and first 100 characters of notes. Offer the candidate types and wait for the user to choose.

## Image Routing

When a node has an `image` field set, route the image file based on the node's content type:

| Node type | Image destination |
|-----------|------------------|
| `npc` | `Characters/` |
| `location` | `Locations/` |
| `item` | `Items/` |
| `scene` / `encounter` / `puzzle` | `Chapters/XX - Name - Canvas/` (chapter folder, not Scenes/) |
| `concept` | `Concepts/` |
| Ambiguous | Ask the user |

Image files are embedded in the XMind ZIP under `resources/`. The `image` field in the extracted JSON contains the `src` path (e.g. `xap:resources/img-abc123.png`). Strip the `xap:` prefix and extract from the ZIP.

Embed images in generated Markdown using vault-relative Obsidian syntax:
```markdown
![[Characters/npc-name.png]]
```

## File Naming

Apply consistent naming to all generated files:

**Scenes / Encounters / Puzzles** — in `Chapters/XX - Name - Canvas/Scenes/`:
- `01 - Scene Name.md`
- `01a - Sub Scene.md` (sub-scenes of a primary scene)
- Use two-digit prefix based on narrative order, not XMind branch order

**NPCs** — in `Characters/`:
- `NPC Name.md` (title case, no prefix)

**Locations** — in `Locations/`:
- `Location Name.md`

**Items** — in `Items/`:
- `Item Name.md`

**Concepts** — in `Concepts/`:
- `Concept Name.md`

## Multi-Type Nodes

When a node should produce multiple files (e.g. a scene that also introduces a named NPC with a stat block):

1. Generate the primary file (the dominant type — usually `scene`)
2. Generate secondary files for each additional type found
3. Cross-link: add `[[NPC Name]]` wiki-link in the scene file and vice versa
4. Note both files in the import log

## Update Decision Rules

When a target file already exists:

1. Check if the XMind node has a note or tag indicating it was updated (e.g. title contains "[UPDATE]" or "[REVISED]")
2. If update flag is present → proceed with overwrite after confirming with user
3. If no flag → the `PreToolUse` hook will intercept the write and ask: Overwrite / Skip / Diff first

Never silently overwrite. Always surface the choice.

## Additional Resources

- **`references/node-types.md`** — Detailed classification criteria with edge cases
- **`references/folder-structure.md`** — Full vault folder structure and path construction rules
