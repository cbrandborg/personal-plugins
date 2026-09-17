# xmind-campaign

A portable Agent Plugins v1 package for extracting XMind maps and turning them into structured, audited Obsidian campaign notes and canvases.

## Included skills

- `extract` — safely extract a `.xmind` archive into `_extracted/` JSON and resources.
- `audit-tree` — review every attached and summary node before generation.
- `generate` — classify nodes and create Obsidian Markdown files with an import log.
- `create-canvas` — create a linear Obsidian Canvas from chapter scene files.
- `content-mapping` — map nodes to scenes, NPCs, locations, items, encounters, puzzles, or concepts.
- `scene-writing` — format campaign content as Obsidian Markdown.
- `completeness-rules` — prove every notes-bearing node and summary subtree is accounted for.

## Requirements

- Python 3.10+
- An XMind file using the JSON-based `.xmind` format
- An Obsidian vault when generating notes or canvases

The extraction script stages output before replacement and rejects traversal, archive special files, portable-name collisions, files larger than 64 MiB, and archives larger than 512 MiB uncompressed.

## Install in Hermes

Install the repository containing this plugin, then enable it:

```bash
hermes plugins install owner/repository --no-enable
hermes plugins list
hermes plugins enable xmind-campaign
```

For a local checkout, symlink or copy this directory into `$HERMES_HOME/plugins/xmind-campaign`, then enable `xmind-campaign`. Use `skills_list` to discover the qualified skill names and `skill_view` to load one.

Validate a checkout with:

```bash
hermes plugins doctor /path/to/xmind-campaign --ci
```

## Workflow

1. Ask Hermes to use the `extract` skill on a `.xmind` file.
2. Use `audit-tree` to inspect the complete extracted hierarchy.
3. Use `generate` for one branch or all branches. Confirm classifications and existing-file decisions before writes.
4. Use `create-canvas` for each generated chapter.
5. Require the `completeness-rules` audit before declaring an import complete.

Runtime skills refer to scripts through a resolved `<plugin-root>`: the directory containing `plugin.json`. They do not depend on provider-specific environment variables.

## Expected vault structure

```text
Campaign Name/
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

| Content type | Output folder |
| --- | --- |
| Scene / encounter / puzzle | `Chapters/XX - Name - Canvas/Scenes/` |
| NPC | `Characters/` |
| Location | `Locations/` |
| Item | `Items/` |
| Concept / mechanic | `Concepts/` |

Images follow the classified node type. Ask before routing an ambiguous image or overwriting any existing file.
