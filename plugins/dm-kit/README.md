# dm-kit

D&D campaign authoring toolkit for Obsidian vaults. Works across any campaign in the `DnD/` parent directory as long as the vault follows the structure below.

## What it does

- **Scaffolds scenes, chapters, and characters** with the correct file layout and canvas integration. Canvas and scene file stay in sync automatically.
- **Guides Danish / English read-aloud writing** with principles, patterns, and templates for scene prose and NPC voice.
- **Structures brainstorming** — forces ≥5 options with tradeoffs before committing to one.
- **Looks up D&D 5e rules** (monsters, spells, conditions, DCs, CRs) via Open5e and dnd5eapi.co whenever mechanics come up.
- **Reviews scenes** against vault conventions via a proactive agent.
- **Warns on canvas desync** via a PostToolUse hook.

## Vault structure it expects

Every campaign vault must have:

```
<vault>/
├── CLAUDE.md                      # Vault conventions
├── _Campaign Overview.md          # Live state (single source of truth)
├── Chapters/
│   ├── 01 - <Name>/               # Flat markdown OK for lore chapters
│   ├── 02 - <Name>/
│   │   ├── <Name>.canvas          # Obsidian canvas JSON
│   │   └── Scenes/                # Atomic scene markdown files
│   └── ...
├── Characters/                    # One .md per NPC/PC
├── Items/                         # Magic items
├── Ideas/                         # Drafts and in-progress notes
└── Outdated/                      # Frozen archive
```

Hard rules the plugin enforces:

1. **Canvas + scene sync**: every scene file has a matching node in the chapter's `.canvas`. The `scaffold-scene` skill guarantees this; the `canvas-sync` hook warns on manual Writes that bypass it.
2. **Danish / English split**: player-facing prose in Danish, mechanics in English.
3. **No `# Title` H1 in scene files**: Obsidian canvas cards use the filename as the label.
4. **Canvas node heights 250–600**: smaller renders empty.
5. **Path quoting**: chapter folders contain spaces and apostrophes.

## Installation

```bash
# Option A: local development mode (recommended while iterating)
claude --plugin-dir "~/My Drive/sync/private-obsidian/DnD/dm-kit"

# Option B: install to personal-plugins cache
cp -r "~/My Drive/sync/private-obsidian/DnD/dm-kit" \
      "~/.claude/plugins/cache/personal-plugins/dm-kit/0.1.0"
```

After installation, `cd` into any D&D campaign vault (`DnD/The Plague of Myrkul`, `DnD/The Fractured Crown`, etc.) and start a Claude Code session. The plugin auto-detects the vault via the nearest `CLAUDE.md` that has a sibling `Chapters/` folder.

## Components

### Skills

| Skill | Type | Use when |
|---|---|---|
| `vault-navigate` | knowledge | Auto-loads whenever working inside any D&D vault |
| `scaffold-scene` | user-invoked | Creating a new scene file + canvas node |
| `scaffold-chapter` | user-invoked | Creating a new chapter from scratch |
| `scaffold-character` | user-invoked | Creating an NPC or PC file |
| `write-scene` | knowledge | Writing read-aloud prose, atmosphere, scene structure |
| `write-character` | knowledge | Writing NPC voice, dialogue, mannerisms |
| `brainstorm` | user-invoked | Generating options before committing to a direction |
| `dnd-lookup` | knowledge + scripts | Looking up D&D 5e rules, monsters, spells, DCs |

Invoke user-invoked skills as slash commands: `/dm-kit:scaffold-scene 09 "Refugee Camp"`.

### Agent

- **`scene-reviewer`** — proactive. Reviews a scene file for frontmatter, no-H1, language split, canvas sync, length, DM note format, wiki-links. Triggers after Write/Edit to scene files and on explicit review requests.

### Hook

- **`canvas-sync`** (PostToolUse on Write/Edit) — warns if a scene file just written is not referenced in the chapter canvas. Warning only, never blocks.

### Scripts

- **`scripts/detect-vault.sh`** — walks up from `$PWD` to find the nearest vault root (directory with both `CLAUDE.md` and `Chapters/`).
- **`scripts/add-scene-to-canvas.py`** — surgically adds a file node to an Obsidian `.canvas` JSON. Respects the 250–600 height rule and auto-positions below the last existing node.
- **`scripts/open5e-query.sh`** — queries the Open5e API (monsters, spells, magic items, classes, races, conditions, backgrounds, feats, weapons, armor).
- **`scripts/dnd5eapi-query.sh`** — queries dnd5eapi.co (alternative source with better coverage for skills and conditions).

## Configuration

None required for v1. The plugin is stateless and auto-detects the vault per session.

**Deferred to v2:**
- Per-campaign config via `.dm-kit.local.md` (default DC policy, tone, language pair)
- Local PDF indexing for PHB / DMG lookups (when Open5e and dnd5eapi don't cover the rule)

## What this plugin does NOT do

- Does not scrape D&D Beyond. PC files store the URL; fetching is manual.
- Does not integrate with Obsidian plugins or sync. It writes plain files that Obsidian reads.
- Does not manage dice rolls or initiative. Use a VTT or a dice roller for those.
- Does not generate random tables. Claude's narrative judgment is used for brainstorming, not RNG.
- Does not cover non-SRD content (class subclasses beyond basic, Tasha's, Monsters of the Multiverse). These need your owned books.

## Relationship to `xmind-campaign`

`dm-kit` replaces the need for the older `xmind-campaign` plugin going forward. XMind → Obsidian migration is done. `xmind-campaign` will be retired after `dm-kit` is proven in 2–3 sessions. Keep both installed for now if you still need the old migration pipeline.

## Verification

See the plan at `/Users/priv/.claude/plans/gleaming-doodling-tide.md` for the full end-to-end test checklist.

Quick smoke test:
```bash
cd "~/My Drive/sync/private-obsidian/DnD/The Plague of Myrkul/Ideas/"
~/My Drive/sync/private-obsidian/DnD/dm-kit/scripts/detect-vault.sh
# should print: ~/My Drive/sync/private-obsidian/DnD/The Plague of Myrkul
```
