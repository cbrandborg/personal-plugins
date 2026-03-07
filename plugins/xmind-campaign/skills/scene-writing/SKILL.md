---
name: scene-writing
description: "This skill should be used when the user asks to \"write a scene\", \"generate a scene file\", \"create a scene from this node\", \"write the NPC file\", \"format the encounter\", or when converting XMind node content into Obsidian Markdown files for a DnD campaign. Covers all content types: scenes, NPCs, encounters, puzzles, locations, items."
version: 0.1.0
---

# Scene Writing — XMind Node Content to Obsidian Markdown

## Purpose

Transform extracted XMind node content into well-formed Obsidian Markdown files following DnD campaign conventions. Apply language rules (Danish read-aloud, English mechanics), correct formatting, and YAML frontmatter tagging.

## Core Language Rule

**Danish** = player-facing read-aloud text and NPC dialogue. Preserve exactly as written in the XMind notes — do not translate, paraphrase, or "fix" unless explicitly asked.

**English** = DM-facing mechanical content: DCs, stat blocks, HP, AC, CR, attack rolls, loot tables, DM notes, skill check descriptions, condition names.

When a node's notes mix languages, preserve that mix. Do not consolidate into one language.

## YAML Frontmatter

Every generated file starts with frontmatter:

```yaml
---
tags:
  - scene          # content type (scene/encounter/puzzle/npc/location/item/concept)
  - chapter-XX     # chapter slug (e.g. chapter-03)
  - imported       # marks this as xmind-imported content
aliases: []
---
```

Replace `XX` with the actual chapter number. Add additional tags for notable content:
- `encounter` nodes: add `combat`
- `npc` nodes: add `npc` and the NPC's faction if known
- `puzzle` nodes: add `puzzle`
- Nodes with images: add `has-image`

## File Structure by Content Type

### Scene (`scene`)

```markdown
---
tags: [scene, chapter-XX, imported]
aliases: []
---

[Danish atmospheric read-aloud paragraph(s)]

## [Section heading if needed]

[Additional Danish description or transition]

### Check: [Skill Name]
**DC XX (Success):**
[Success outcome in Danish if player-facing, English if DM note]

**DC XX+ (Failure):**
[Failure outcome]

## Player Choices
- [Option 1]
- [Option 2]

> **DM Note:** [English mechanics, tips, triggers]
```

**Rules:**
- NO `# Title` header — the canvas card uses the filename as label; a header duplicates it
- Start with atmospheric content or a `##` subheading, never a `#` heading
- Keep atomic: one scene per file, 200–1500 words
- DM notes go in `> **DM Note:**` blockquotes

### Encounter (`encounter`)

```markdown
---
tags: [scene, encounter, combat, chapter-XX, imported]
aliases: []
---

[Danish read-aloud for encounter opening]

## Setup

**Trigger:** [What causes this encounter]
**Location:** [[Location Name]] (if applicable)

## Enemies

### [Enemy Name]
- **AC:** X | **HP:** XX | **CR:** X
- **Speed:** Xft
- **Attack:** [Name] +X to hit, Xd6+X [type] damage
- **Special:** [Ability name] — [description]

## Tactics

[English DM notes on how enemies behave, priorities, escape conditions]

## Resolution

**Victory:** [What happens if players win]
**Defeat/Retreat:** [What happens otherwise]

## Loot
- [Item or gold amount]
```

### NPC (`npc`)

```markdown
---
tags: [npc, chapter-XX, imported]
aliases: [Alternate Name]
---

![[Characters/NPC Name.png]]

**Role:** [Title or function]
**Location:** [[Location Name]]
**Faction:** [Faction if known]

## Personality

[Danish description of personality, mannerisms, voice]

## Dialogue

### [Topic or scene]
> "[Danish dialogue line]"

### [Another topic]
> "[Danish dialogue]"

## Stats (if combatant)

- **AC:** X | **HP:** XX | **CR:** X

## DM Notes

[English: motivations, secrets, plot hooks]
```

### Location (`location`)

```markdown
---
tags: [location, imported]
aliases: []
---

![[Locations/Location Name.png]]

[Danish atmospheric description — how it looks, feels, smells]

## Points of Interest

- **[Area]:** [Description]
- **[Area]:** [Description]

## Connections

- [[Scene or NPC that references this place]]

## DM Notes

[English: hidden details, lore, hooks]
```

### Item (`item`)

```markdown
---
tags: [item, imported]
aliases: []
---

![[Items/Item Name.png]]

*[Item type, rarity]*

[Danish flavour description — appearance, history, feel]

## Properties

[English: mechanical effects, attunement, charges, activation]

## Lore

[Danish or English background story]
```

### Puzzle / Challenge (`puzzle`)

```markdown
---
tags: [scene, puzzle, chapter-XX, imported]
aliases: []
---

[Danish setup description]

## The Challenge

[English: mechanic description, what players must do]

### Check: [Skill]
**DC XX (Success):**
[Danish outcome or English DM note]

**DC XX+ (Failure):**
[Outcome]

## Solution

[English: intended solution and DM guidance]

## Rewards / Consequences

[What happens on success/failure]
```

## Content Preservation Rules

1. **Verbatim text**: Copy notes content directly. Do not rephrase, shorten, or expand unless the node content is a bare outline that requires structuring — in that case, use the structure above as scaffolding and preserve all titles/bullets as-is.

2. **Summary children**: Content from `summary_children` in the extracted JSON must be included. These are bracket groupings in XMind that often contain stat blocks or dialogue trees. Do not skip them.

3. **Nested nodes as sections**: If a node has `children` with their own notes, include each child as a `##` or `###` subsection within the parent file (if they belong together) OR generate separate files (if they are distinct scenes). Use content-mapping rules to decide.

4. **Images**: Embed using Obsidian wiki-link syntax: `![[Folder/filename.ext]]`. The image must be extracted from the XMind ZIP and placed in the correct vault folder before embedding.

## Completeness Check Before Saving

Before writing any file, confirm:
- [ ] All `notes` content from the node is represented (nothing cut)
- [ ] All `summary_children` content is included or has its own file
- [ ] Image is embedded if `image` field was set
- [ ] Frontmatter is complete with correct tags
- [ ] File does not start with a `#` heading

## Additional Resources

- **`references/templates.md`** — Copy-paste templates for all content types
- **`references/frontmatter.md`** — Full YAML frontmatter spec and tag taxonomy
