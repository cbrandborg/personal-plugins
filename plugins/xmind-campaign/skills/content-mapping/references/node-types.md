# Node Type Classification — Edge Cases & Detailed Criteria

## Classification Decision Tree

```
Node has notes or image?
├── NO → skip (unless children are meaningful — then structural, still skip)
└── YES → classify:
    ├── Title signals NPC name/role? → npc
    ├── Title signals encounter/combat? → encounter
    ├── Title signals puzzle/trap/challenge? → puzzle
    ├── Title signals item/loot? → item
    ├── Title signals named place (recurring)? → location
    ├── Title signals mechanic/faction/lore? → concept
    ├── Notes open with Danish atmospheric prose? → scene
    └── Still unclear? → ASK USER
```

## Edge Cases

### NPC inside a scene node
A node titled "Market Square" (clearly a scene) has a child "Merchant Bram" with dialogue notes.

**Resolution**: Generate `Market Square.md` as a `scene`. If Bram has more than 3 lines of dialogue or a stat block, also generate `Merchant Bram.md` as an `npc` and cross-link. If Bram has only a one-line note, merge into the scene as a brief NPC mention.

### Location that is also a chapter scene
A node titled "The Old Mill" appears both as a location (general description in notes) and as the setting for a specific scene (chapter-specific events in children).

**Resolution**: Generate `The Old Mill.md` in `Locations/` for the general description. Generate scene files in `Chapters/` for the chapter-specific events. Link the scene files to `[[The Old Mill]]`.

### Summary child with no title
Some summary nodes in XMind have an empty or generic title like "Summary" but contain detailed stat blocks.

**Resolution**: Classify based on content. Stat blocks → `encounter` or `npc`. Mechanic descriptions → `concept`. Use the parent's title to construct the filename: `[Parent Title] - Summary.md`.

### Node with only an image (no notes)
An image node with no text notes.

**Resolution**: Do not skip. Generate a file with frontmatter, the image embed, and an empty body. Add `needs-content` tag. Log it.

### Structural nodes with meaningful titles
Nodes like "Act 1", "Chapter 3: The Plague Spreads", "Encounter List" — clearly organizational.

**Resolution**: Skip (no file generated). But check all children carefully — organizational wrappers often contain important summary_children.

### Danish-only nodes
Some nodes contain only Danish text with no English mechanics.

**Resolution**: Classify by content type as normal. Do not add English translations. Write the file in Danish as-is. Add a DM note stub in English only if the context requires DM guidance not present in the notes.

## Confidence Levels

When logging classification decisions, include confidence:

| Confidence | Meaning | Action |
|------------|---------|--------|
| `HIGH` | Two or more signals agree | Proceed without asking |
| `MEDIUM` | One clear signal | Proceed, note in log |
| `LOW` | Signals conflict or absent | Ask user |

Always log `LOW` confidence classifications in the import log regardless of user's answer, so they can be reviewed later.

## Multi-File Nodes: When to Split

Split one node into multiple files when:
- The node contains content that logically belongs in two different vault sections (e.g. scene description + NPC stat block)
- The node notes length exceeds 1500 words and covers distinct scenes
- The node has both a general location description and chapter-specific events

Do NOT split when:
- The secondary content is a brief mention (< 5 lines)
- The secondary content only makes sense in context of the primary file
- Splitting would create an orphaned file with no useful standalone content
