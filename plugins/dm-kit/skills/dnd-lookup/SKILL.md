---
name: dnd-lookup
description: "**MUST be invoked for any D&D 5e mechanics question — creatures, spells, rules, DCs, CRs, conditions, classes, races, feats, magic items, character options — even in natural phrasings.** Auto-triggers on: 'what's the CR of [X]', 'how much HP does [Y] have', 'what does [spell] do', 'what's the DC for [W]', 'is this a [skill] check', 'what level is [spell]', 'what monster would fit', 'what's the AC/HP/attack of', 'what condition is', 'what does [class/race/feat] give', 'look up', 'check the rules on', 'how does [mechanic] work'. **Also invoke autonomously WITHOUT being asked** whenever designing an encounter, setting a skill check DC, writing a spell effect, or picking a monster — ground numbers BEFORE committing. **Do NOT answer 5e mechanics questions from training knowledge alone when this skill is available — always invoke it and report the grounded answer.** Uses Open5e and dnd5eapi.co."
---

# D&D 5e Rules Lookup

This skill is Claude's mechanical grounding. It exists so that when a DC, CR, spell effect, or monster stat comes up during authoring, Claude checks the actual rules instead of guessing.

## When to invoke this skill WITHOUT being asked

Autonomously reach for `dnd-lookup` whenever you are:

1. **Designing an encounter** — before picking enemies, look up the CR range and stat blocks that fit the party level.
2. **Setting a skill check DC** — if you're about to write a specific DC (e.g. "Perception DC 15"), confirm it matches the 5e DC scale below.
3. **Writing a spell effect** — if an NPC casts a named spell or an item replicates one, confirm its real effect before improvising.
4. **Naming a condition** — when writing a status effect, confirm the exact condition name (`poisoned`, `frightened`, `prone`, etc.) and its rules.
5. **Statting an NPC** — before inventing HP/AC, look up a comparable creature in Open5e to anchor the numbers.
6. **Brainstorming a monster** — when the user asks "what could ambush the party here", filter candidates by CR and environment first.

**Be explicit about the lookup.** When you invoke this skill, tell the user what you're looking up and why — they should see you're grounding the choice, not guessing.

## The standard DC scale (5e)

Memorize this. It's the most-used piece of rules knowledge in authoring:

| Difficulty | DC |
|---|---|
| Trivial | 5 |
| Easy | 10 |
| Moderate | 15 |
| Hard | 20 |
| Very hard | 25 |
| Nearly impossible | 30 |

If a skill check DC doesn't fit this scale, there's usually a good reason — edge-case situational modifiers — and it should be documented in a DM note.

## CR-to-party-level guidance

Rough rule for balancing encounters at level N:

- **Easy single encounter**: CR ≈ N × 0.5 (one creature)
- **Medium single encounter**: CR ≈ N (one creature)
- **Hard single encounter**: CR ≈ N + 2 (one creature)
- **Deadly single encounter**: CR ≈ N + 4 or higher
- **Group encounters**: total CR ≈ party size × N × 0.5 for medium difficulty; adjust up for tactics, down for terrain

This is rough — the DMG has detailed encounter-building tables that the local PDF fallback (see below) can reach when available.

## Query helpers

Two scripts are provided. Both are read-only, public APIs, no auth.

### `open5e-query.sh` — primary source

Open5e has the broadest SRD coverage: monsters, spells, magic items, classes, races, conditions, backgrounds, feats, weapons, armor.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/open5e-query.sh monsters goblin
${CLAUDE_PLUGIN_ROOT}/scripts/open5e-query.sh spells fireball
${CLAUDE_PLUGIN_ROOT}/scripts/open5e-query.sh magicitems "bag of holding"
```

Endpoints: `monsters`, `spells`, `magicitems`, `classes`, `races`, `conditions`, `backgrounds`, `feats`, `weapons`, `armor`.

The script formats top 5 results. Search is fuzzy — use specific names for exact matches.

### `dnd5eapi-query.sh` — secondary/overlap source

Different API, sometimes has different or cleaner data. Particularly good for **skills** and **ability score** details, which Open5e doesn't expose as cleanly.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/dnd5eapi-query.sh skills athletics
${CLAUDE_PLUGIN_ROOT}/scripts/dnd5eapi-query.sh conditions poisoned
${CLAUDE_PLUGIN_ROOT}/scripts/dnd5eapi-query.sh monsters goblin
```

Endpoints: `monsters`, `spells`, `skills`, `conditions`, `rules`, `magic-items`, `classes`.

dnd5eapi uses slug lookups (`adult-red-dragon`, not "Adult Red Dragon"). The script tries slug-first and falls back to a name-contains filter on the endpoint's full list.

## What these sources do NOT cover

- **Non-SRD content**: most class subclasses beyond the basic (Hexblade, Twilight Cleric, Bladesinger, etc.), the Monsters of the Multiverse versions of monsters, Tasha's optional class features.
- **Books you own (PHB, DMG)**: there is no public API for copyrighted WotC text. If the user has PDFs, see the "Local PDF fallback" section.
- **Adventure-specific content**: published modules, their monsters, NPCs, etc.

When Open5e / dnd5eapi don't have what you need, **say so explicitly** and offer the alternatives (user provides the detail, you improvise and flag it as non-RAW, etc.).

## Context Hub (chub) is NOT a source

Verified: `chub search dnd` returns only `react-beautiful-dnd` (a TypeScript library). Context Hub has no D&D 5e documentation. Do not attempt to use chub for rules lookup.

## Local PDF fallback (future / optional)

If the user has PHB.pdf and DMG.pdf available, we can index them once with `pdftotext` and grep for keywords. This is deferred to a future version of dm-kit. If the user asks about non-SRD content today, the honest answer is "I can't look that up without your books — what does your copy say?"

## Worked examples

**Example 1: Setting a DC**

> User: *"Add a climb check for the cliff path in chapter 9."*

Before writing `Climb DC 12` or `DC 16`, check the scale: moderate cliff = DC 15, treacherous loose footing = DC 20. Write DC 15 and note in a DM comment: "DC 20 if raining or pursued."

**Example 2: Picking a monster for an ambush**

> User: *"I need something to ambush the party on the forest road. Level 5 party, 4 PCs."*

Before suggesting "wolves" or "bandits", run `open5e-query.sh monsters wolf`, `open5e-query.sh monsters bandit`, and check CRs. Pack of 4 Wolves (CR 1/4 each) = easy. 2 Dire Wolves (CR 1) + 4 Wolves = medium. Report the numbers, let the user pick the intensity.

**Example 3: An NPC casts a spell**

> User: *"The wizard NPC uses Misty Step to escape."*

Run `open5e-query.sh spells "misty step"` to confirm: 2nd-level, bonus action, 30 ft teleport. Note in the scene that this uses the NPC's bonus action and that they must see the destination point.

## Cross-references

- `brainstorm` — when brainstorming encounters, invoke this skill in "grounded" mode for mechanical accuracy.
- `write-scene` — for DCs embedded in scene files (use the DC scale above).
- `write-character` — for NPC stat blocks (anchor to a real creature's numbers).
