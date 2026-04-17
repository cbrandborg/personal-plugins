---
name: write-scene
description: "Loads when the user is writing or improving player-facing atmospheric prose for a D&D campaign vault. Trigger phrases include: 'write a scene', 'write the read-aloud', 'write read-aloud', 'write the Danish read-aloud', 'give me a read-aloud', 'give me the read-aloud for', 'describe this place', 'describe [location] for my players', 'I need to describe', 'how should I write the description', 'how should I describe', 'help me write the atmospheric', 'help me write the [opening/description/text]', 'draft atmospheric prose', 'draft atmospheric', 'write atmosphere', 'draft the scene opening', 'write the encounter description', 'write a tense encounter opening', 'make this feel more [tense/eerie/dread/hopeful]', 'rework this scene', 'rework this scene opening', 'so it lands with more dread'. Also triggers whenever the user wants to produce Danish read-aloud text, atmospheric room or location descriptions, encounter openings, arrival scenes, or tavern descriptions — any request to write player-facing prose in a campaign vault. Provides principles, structure patterns, and template snippets for Danish read-aloud and English DM mechanics."
---

# Writing Scenes

Scene prose is the highest-leverage content in a campaign. Players remember the moment a door swings open and the room lands, not the DC that gated it. This skill teaches the principles and the patterns.

## The language split

Every scene file mixes two registers:

- **Danish** (all player-facing prose): read-aloud paragraphs, NPC dialogue, atmospheric description. Present tense, second-person plural (*I ser…*, *I hører…*, *I mærker…*). Never break the fourth wall. Never explain mechanics in Danish.
- **English** (DM mechanics): DCs, damage rolls, stat blocks, skill checks, condition names, trigger notes. Always inside `> **DM Note:**` blockquotes or under `##` mechanical subheadings.

If the user mixes languages in a passage on purpose, preserve the mix. Don't "clean it up" unless asked.

## Read-aloud principles

### Sense first

A strong read-aloud opening anchors on **one sensory detail** before the scene expands. Not the whole room — one thing. Sight is the default; sound, smell, and temperature land harder in horror.

Weak:
> *"I går ind i hallen. Den er stor og mørk. Der er støv overalt."*

Stronger:
> *"Lyden af jeres skridt bliver pludselig større. I er gået ind i en hal, der suger lyd ud af alt. Støv hvirvler i luften, hvor I trådte."*

### Present tense, you-plural

Always `I ser`, `I hører`, `I mærker`. Never `du` (singular), never past tense. The players are *in* the moment.

### Short sentences for tension, long for atmosphere

When the scene is calm, sentences can run long and layered. When something is about to break — a door, a silence, a stranger — **shorten them**. Single-clause sentences feel like held breath.

> *"Ilden knitrer. Mågen på taget er tavs nu. I hører skridt på grusset udenfor."*

### Name one thing that shouldn't be there

Every scene opening should contain one small wrongness — a detail that doesn't quite belong, that the players can fixate on if they want. A chair pulled out from the table. A door left ajar. A smell that shouldn't be there. Don't explain it.

### Leave a door for the players

End the read-aloud before anything requires an answer. Hand the scene back to the players with silence, not a question. Let them act.

## Scene structure patterns

### Arrival scene — **wide → narrow → hook**

1. **Wide shot**: the place as it first appears. Weather, scale, distance.
2. **Narrow detail**: one thing close up that the players can react to.
3. **Hook**: something happens, or something is wrong.

```markdown
[Wide: vejen drejer, træerne lysner, byen ligger i dalen]

[Narrow: galgerne i udkanten. Et halsbånd med et skilt.]

[Hook: En skikkelse træder ud fra det første hus. Han er i Ordenens røde kappe, men han holder sit sværd med begge hænder.]
```

### Investigation scene — **what they see → what they can check → what they find**

1. **Surface description** (Danish, read-aloud)
2. **Check options** in English, with DCs
3. **Success text** in Danish, failure text in English or as a branching note

Use `> **DM Note:**` blockquotes for the mechanical content, so the Danish narration flows uninterrupted above.

### Encounter opening — **calm → disruption → initiative**

Never open combat with "roll initiative." Give one beat of calm, then the disruption. The first Danish sentence is normal life. The second is what ends it.

```markdown
[Henrik ler ad noget, hans datter har sagt. Hesten puster damp ud i kulden.]

[Så bliver temperaturen koldere. Ikke gradvist. På én gang.]

> **DM Note:** Roll initiative. Morgoth enters from the east tree line.
```

### Dialogue scene — **setup → voice → the line → space for PCs**

1. **Setup**: where and how is the NPC standing? One physical detail.
2. **Voice**: a single mannerism or word choice that tells the players who this is.
3. **The line**: one or two sentences of direct Danish speech. No paragraph monologues.
4. **Space for PCs**: stop. Don't resolve the conversation for them.

## Template snippets

### Scene file skeleton

```markdown
---
tags:
  - scene
  - chapter-XX
aliases: []
---

[Danish atmospheric opening — 2-5 sentences, one sense first, one wrongness, one hook]

## [Optional subheading if the scene has phases or options]

[More Danish prose OR a mechanical section below]

### Check: [Skill] DC XX
**Success:** [Danish outcome if player-facing, English if DM note]
**Failure:** [Outcome]

## Player Choices
- [Option 1 — Danish]
- [Option 2 — Danish]

> **DM Note:** [English — triggers, timing, what's hidden, how to react to player creativity]
```

### Encounter file skeleton

```markdown
---
tags:
  - scene
  - encounter
  - combat
  - chapter-XX
aliases: []
---

[Danish encounter opening: calm → disruption. 3-6 sentences.]

## Setup

**Trigger:** [What causes this encounter]
**Location:** [[Location Name]]

## Enemies

### [Enemy Name]
- **AC:** X | **HP:** XX | **CR:** X | **Speed:** Xft
- **Attack:** [Name] +X to hit, Xd6+X [type] damage
- **Special:** [Ability] — [description]

## Tactics

[English DM notes: priorities, formations, escape conditions, what makes the fight interesting]

## Resolution

**Victory:** [Danish or English — what happens if players win]
**Defeat/Retreat:** [What happens otherwise]

> **DM Note:** [Any scaling notes or alternative outcomes]
```

## Length targets

- **Single scene file**: 200–1500 words total (including mechanics). If you're going longer, consider splitting into sub-scenes (`01a`, `01b`).
- **Read-aloud opening**: 40–150 Danish words. Longer than that and the players tune out.
- **NPC dialogue line**: 1–3 sentences per turn. Never a monologue.

## What not to write

- **Don't describe what players feel.** "I er bange" is wrong. The players decide if they're afraid. Show the cause (the temperature drop, the sound) and stop.
- **Don't narrate PC actions.** "I træder ind og trækker sværdet" is wrong. Describe the room, not the players.
- **Don't resolve dice for them.** Read-aloud describes the world, not the outcome of checks.
- **Don't monologue through NPCs.** Break NPC exposition into short exchanges. If the players don't ask, don't dump.
- **Don't explain mechanics in Danish read-aloud.** DCs, HP, conditions — all English, all in DM notes.

## Cross-references

- `scaffold-scene` — creates the scene file and updates the canvas. Use this BEFORE writing prose, so the file exists in the right place.
- `write-character` — for NPC voice and dialogue specifically.
- `brainstorm` — for generating scene options before committing to one.
