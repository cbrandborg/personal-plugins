# Personal Plugin Marketplace

Personal Claude Code plugins by cbrandborg.

## Adding this marketplace

```bash
/plugin marketplace add https://github.com/cbrandborg/personal-plugins
```

## Installing plugins

```bash
/plugin install <plugin-name>@personal-plugins
```

## Available plugins

| Plugin | Description | Category |
|--------|-------------|----------|
| `dm-kit` | D&D campaign authoring toolkit: scaffolds scenes/chapters/characters with canvas sync, writing guidance, structured brainstorming, and 5e rules lookup | productivity |
| `xmind-campaign` | Convert XMind mind maps into structured Obsidian vaults for DnD campaigns (legacy — superseded by dm-kit for new authoring work) | productivity |

## Adding a plugin

1. Create a directory under `plugins/your-plugin/` with the standard plugin structure
2. Add an entry to `.claude-plugin/marketplace.json`
3. Bump the version in `marketplace.json` on every change — this is how Claude Code knows to update the cache
