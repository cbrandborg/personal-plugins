# xmind-campaign

Convert XMind mind maps into structured Obsidian vaults for DnD campaigns.

## Features

- Full XMind extraction handling both `attached` and `summary` (bracket) children
- Rule-based content classification: scenes, NPCs, locations, items, encounters, puzzles
- Image routing: NPC images → Characters/, places → Locations/, items → Items/
- Danish read-aloud / English mechanics writing rules
- Completeness auditing — every notes node and summary subtree must have output
- Guard hook: asks before overwriting existing vault files
- Obsidian Canvas generation

## Prerequisites

- Python 3.10+
- Obsidian vault with DnD campaign structure

## Installation

Copy or symlink this plugin directory, then enable it in Claude Code.

## Usage

### 1. Extract

```
/xmind-campaign:extract
```

Point Claude at your `.xmind` file. Extracted JSON is saved to `_extracted/` next to the source file. Extraction is staged before replacing an existing output directory and rejects unsafe archive paths, special files, name collisions, members larger than 64 MiB, or archives larger than 512 MiB uncompressed.

### 2. Audit

```
/xmind-campaign:audit-tree
```

Review the full node tree before generating anything. Flags nodes with notes, images, and summary subtrees.

### 3. Generate

```
/xmind-campaign:generate
```

Processes branch-by-branch, classifies content, writes scene/NPC/location/item files to the vault. Runs completeness audit automatically.

### 4. Create Canvas

```
/xmind-campaign:create-canvas
```

Generates an Obsidian Canvas JSON linking all scenes in a chapter.

## Settings

The plugin remembers your last-used vault path per campaign. Settings are stored in `.claude/xmind-campaign.local.md`.

## Vault Structure Expected

```
DnD/
└── Campaign Name/
    ├── CLAUDE.md
    ├── Chapters/
    │   └── XX - Name - Canvas/
    │       ├── Name.canvas
    │       └── Scenes/
    ├── Characters/
    ├── Locations/
    ├── Items/
    ├── Concepts/
    └── _import-log.md
```

## Content Types & Folder Mapping

| XMind Node Type | Obsidian Folder |
|----------------|-----------------|
| Scene / Encounter / Puzzle | Chapters/XX/Scenes/ |
| NPC | Characters/ |
| Location | Locations/ |
| Item | Items/ |
| Concept / Mechanic | Concepts/ |

## Image Routing

Images embedded in XMind nodes are routed based on node type:
- NPC node → `Characters/`
- Location node → `Locations/`
- Item node → `Items/`
- Ambiguous → ask user
