---
name: write-character
description: "Use when developing an NPC or PC's voice, personality, dialogue, mannerisms, signature phrase, or narrative function in a D&D campaign vault. Helps make characters distinctive in play with minimum viable details, Danish speech patterns, major-versus-minor guidance, dialogue templates, faction context, and advice on when a stat block is needed."
---

# Writing Characters

The difference between a forgettable NPC and a memorable one is usually one detail the players will remember when the name comes up six sessions later. This skill teaches how to find that detail and make it land.

## The minimum viable NPC

Every named NPC — even a shopkeeper with three lines — should have:

1. **One physical detail** that sticks. Not a full description. One thing: a crooked eye, a limp, ink-stained fingers, a crow tattoo, a voice that cracks on consonants.
2. **One mannerism**. A repeated gesture or verbal tic. They pray before sentences. They count coins while they talk. They never sit down. They translate everything into farm metaphors.
3. **One registered voice**. High / low, formal / vulgar, fast / slow, blunt / indirect, educated / folk. Pick one extreme, not the middle.
4. **One secret motivation**. What they want that the players don't know about yet. This is the hook that makes them feel alive — even if it never comes out.

That's the baseline. Anything more is bonus. Major NPCs need more; minor NPCs should have exactly this.

## Major vs minor NPCs

Mark characters as **major** or **minor** in their file (via a `major: true|false` field). The two get different treatment.

**Major NPC** (recurring, named in multiple chapters, has an arc):
- Full backstory
- Clear faction alignment and shifts over time
- Named mannerisms and voice profile
- Stat block if combat-relevant
- DM notes on hidden motivations and secret plans
- Cross-references to the scenes they appear in
- Optional portrait image

**Minor NPC** (appears once, filler for a town or encounter):
- Just the minimum viable NPC (above)
- No stat block unless they fight
- No image
- Do not inflate minor NPCs into major ones retroactively — if a minor NPC gets a second chapter because players liked them, promote the file then.

## Voice principles

### Write speech, not writing

Spoken Danish is messier than written. People:
- Start sentences and abandon them
- Use filler (*øh*, *ja...*, *nå*)
- Contract aggressively (*ska'*, *ka'*, *no'en*)
- Interrupt themselves
- Repeat words for emphasis (*nej, nej, nej*)

Written dialogue that reads "correct" sounds wrong at the table. Let it be broken.

Weak (written):
> *"Jeg har ikke set nogen som dem i landsbyen i mange år, det må jeg sige."*

Stronger (spoken):
> *"Nej... nej. Så'en nogen som dem? I landsbyen? Ikke i mange år."*

### One voice signature per NPC

Pick one thing that's always there:
- **A filler word**: *"Aye"*, *"Altså..."*, *"Forstår I."* Let it appear every third or fourth line.
- **A grammatical tic**: They drop the *-er* ending on verbs. They never use past tense. They speak in the third person about themselves.
- **A metaphor bank**: Everything they say is a farming analogy, or a military one, or a religious one.
- **A physical pattern**: They never finish sentences when standing. They only speak while doing a task.

Whatever you pick, be consistent. The players will notice the pattern before they can name it, and that's the point.

### Read it aloud

If you're writing dialogue, whisper the line to yourself. If it feels weird to say, it'll feel weird at the table. Cut it.

## NPC types and their narrative functions

Not every NPC is the same kind of piece on the board. Knowing the function makes the voice easier to find.

| Type | Function | Voice hint |
|---|---|---|
| **Mentor** | Gives the party a hook, a warning, or a name. Usually doesn't travel with them. | Older, calmer, uses fewer words than they need |
| **Obstacle** | Blocks progress through bureaucracy, prejudice, or fear. Not evil — just in the way. | Nervous, procedural, hides behind rules |
| **Rival** | Parallel to the party. Different methods, similar goals. A mirror to the PCs. | Sharp, direct, slightly contemptuous |
| **Ally** | Fights with or for the party. Not a replacement PC — they follow, they don't lead. | Earnest, loyal, occasionally questioning |
| **Victim** | The people the story is about saving. Individual faces for the plague / war / collapse. | Exhausted, grieving, small voice. Never a monologue. |
| **Informant** | Gives information for a price. Never for free. Always wants something back. | Evasive, amused, pleased with themselves |
| **Villain** | Wants something the party must stop. The best villains have a cause the party can almost sympathize with. | Calm when winning, articulate when cornered. Rarely raises voice. |

## Faction and first-met

Every NPC file should record:

- **Faction**: `enemy` / `ally` / `neutral` / `contested`. "Contested" is the most interesting label — NPCs whose loyalty the players are fighting over or whose alignment has shifted.
- **First met**: which chapter and ideally which scene. Link to the scene file. This matters because the agent in future sessions needs to know WHEN the party met this character to gauge how much history is shared.
- **Appearances**: growing list of chapters. Add one every time the character shows up in play.

## When an NPC needs a stat block

**Yes, give them a stat block when:**
- The party might fight them
- They cast spells that affect the party
- They might be subject to the party's spells (a saving throw comes up)

**No stat block needed when:**
- They only talk
- They only give information
- They exist to deliver a moral choice, not a combat one
- They're a crowd of anonymous villagers or guards (use generic Guard / Commoner blocks if needed)

When in doubt, leave it off. You can always add one later; you can't easily remove it once it's in the file.

## Dialogue template

```markdown
## Dialogue

### [Topic or scene]
> "[Danish line in their voice]"

### [Another topic]
> "[Another Danish line]"

### If asked about [X]
> "[Line — keep short]"
```

Write 3–5 topics for a major NPC, 1–2 for a minor. Don't write out every possible conversation — pick the topics the players are most likely to raise.

## Cross-references

- `scaffold-character` — creates the character file with the right template fields. Use this first.
- `write-scene` — for the scene-level prose that the NPC appears in.
- `brainstorm` — if you're deciding between multiple voices or backstories, generate options first.
- `dnd-lookup` — for stat blocks and class feature details when the NPC needs them.
