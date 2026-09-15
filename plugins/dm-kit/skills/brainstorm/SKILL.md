---
name: brainstorm
description: "Use when the user wants a list of options to choose from, or is stuck on a decision about any D&D campaign element. Trigger phrases include: 'brainstorm', 'give me options', 'give me options for', 'I need options for', 'give me a bunch', 'give me a bunch of options', 'give me ideas', 'I need ideas', 'I need ideas for', 'I need ideas for what', 'what could happen if', 'what could [X] do', 'what are some ways', 'help me decide', 'help me decide between', 'give me alternatives', 'come up with X options', 'I want alternatives', 'I'm stuck on', 'give me X [options/ideas/versions/alternatives]', 'I'll pick from a list'. Also triggers for any request for a set of scene hooks, plot twists, NPC backstories, item mechanics, dialogue options, chapter openings, or encounter ideas where the user wants to pick from multiple possibilities before committing to one. Enforces structured ideation: generates 5-10 options with tradeoffs before committing."
argument-hint: "[optional: topic to brainstorm]"
allowed-tools: "Read Glob Grep Bash"
---

# Brainstorm

Most creative dead-ends in campaign authoring come from committing to the first idea. This skill forces the pattern: **generate many, tag tradeoffs, cut ruthlessly, then pick.**

## Step 1: Ask the mode

Open every brainstorm session with this question:

> **Inline** (narrative only) or **Grounded** (narrative plus rules lookup for mechanical elements)?

- **Inline** is for narrative choices: scene hooks, NPC backstories, plot twists, dialogue options, place names, atmospheric variations. The agent's judgment is stronger than any RNG here.
- **Grounded** is for anything mechanical: encounter composition, DCs, spell effects, monster selection. Grounded mode invokes `dnd-lookup` for every number or rules reference.

Wait for the user's answer before generating. If they don't specify, default to **inline** unless the request is obviously mechanical.

## Step 2: Generate at least 5, ideally 8–10 options

**The number matters.** Fewer than 5 isn't a brainstorm — it's a first-draft. Force yourself past the obvious answers:

- The first 3 options will be obvious (what anyone would think of)
- Options 4–6 are where interesting variations start
- Options 7–10 are the weird ones, and the weird ones are often what the table remembers

Don't filter yourself mid-generation. Write all of them, even the bad ones. You'll cut them in step 4.

**Numbering matters too.** Label each option (1, 2, 3...) so the user can reference them by number in discussion.

## Step 3: Tag each option with tradeoffs

For every option, write one line under it covering:

- **What it costs** (party resources, session time, NPCs spent, plot threads closed)
- **What it signals** to the players about the campaign's direction
- **What it gives up** (other options it forecloses)

Format:

```
### 1. [Option name]
[One sentence describing the option.]
**Cost:** [what it takes]  **Signal:** [what it tells the party]  **Forecloses:** [what it rules out]
```

This is where the brainstorm gets useful. An option without tradeoffs is a sales pitch, not a choice.

## Step 4: Cut ruthlessly

After presenting the full list, **explicitly prompt the user to eliminate 3–5 options** before picking. Don't skip this. Phrasing:

> Of these [N] options, which 3–5 can we cut immediately? Not the best ones — the ones that don't fit the campaign's current direction.

This forces the user into discrimination mode rather than selection mode. Cutting is easier than picking, and the surviving options are stronger candidates.

## Step 5: Let the user pick

After cuts, there should be 3–5 options left. The user picks one (or asks for a synthesis of two). At this point, hand off to the relevant execution skill:

- Scene hook chosen → `write-scene` for the prose
- NPC picked → `scaffold-character` + `write-character`
- Encounter chosen → `scaffold-scene` with `--type encounter`
- Plot twist picked → write it into `_Campaign Overview.md` active threads

## When to brainstorm vs commit

Brainstorm when:
- The user is early in the creative process and open to directions
- There's a stuck point where the obvious answer feels wrong
- The user explicitly asks for options
- Multiple valid directions exist and the tradeoffs matter

**Don't brainstorm when:**
- The user has already picked a direction and wants execution
- The task is mechanical and has a right answer (use `dnd-lookup` directly)
- Time pressure is obvious — this session is about getting a scene written, not generating alternatives

## Example session

> User: *"I need ideas for how chapter 10 opens. The party just left Greyhaven, they're riding to the ruined monastery, and I don't know what to put on the road."*

**Step 1 (mode):** "Inline or grounded? A road-opening scene probably doesn't need mechanical grounding — inline means I pull from narrative craft rather than querying monster stats. Grounded would matter if you want specific creatures or environmental hazards with RAW DCs. Your call."

*User: "Inline."*

**Step 2 (generate):**

### 1. The scarecrow that turns its head
The party rides past a field with scarecrows. As they pass the last one, its head follows them. Nothing else. Don't explain.
**Cost:** free — pure atmosphere.  **Signal:** the threat extends beyond Greyhaven.  **Forecloses:** nothing — this can be a one-off.

### 2. A child, alone
A lone child sits on a stone by the road. Says her parents told her to wait here. Will not move. Has been there two days.
**Cost:** a real moral choice — what do they do with her?  **Signal:** the world is breaking; strangers are responsible for strangers now.  **Forecloses:** clean-moral-victory tones for a session or two.

### 3. Bells in the distance
They hear a monastery bell faintly on the wind. The road isn't close enough to any monastery to hear one. The bell stops when anyone looks at the horizon. Starts again when they don't.
**Cost:** free atmosphere, builds toward chapter 10.  **Signal:** the ruined monastery is reaching out to them.  **Forecloses:** a quiet opening — this one is eerie.

[...continue to 8-10]

**Step 3 (cuts):** "Which 3–5 can we cut right now? Not your favorites — the ones that don't fit the tone of what chapter 9 just ended on."

## What this skill is NOT

- **Not a random generator.** Use creative judgment, not an RNG feed or external tables.
- **Not a final answer machine.** Brainstorm ends when the user picks, not when the agent picks.
- **Not a substitute for execution.** Once picked, hand off to the skill that actually writes the thing.
