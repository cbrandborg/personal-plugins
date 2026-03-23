# Agent Task: Personal Plugin Marketplace

## Context

Private Claude Code plugin marketplace at `cbrandborg/personal-plugins` on GitHub. Registered in Claude Code as a local marketplace source.

## Current Plugins

- `xmind-campaign/` — converts XMind DnD campaign maps into structured Obsidian vaults (extraction, classification, scene generation, auditing, Canvas creation)
- `voting-assistant/` — Algocratic voting decision-support pipeline for Danish elections. Combines quantitative party analysis with qualitative voter interview for personalized recommendations.

## Completed

- [x] Clean up test directories
- [x] Create `marketplace.json` with plugin registry
- [x] Initialize git repo
- [x] Create private GitHub repo (`cbrandborg/personal-plugins`) and push
- [x] Register marketplace in Claude Code
- [x] Add xmind-campaign plugin
- [x] Add voting-assistant plugin to marketplace.json
- [x] Add voting-assistant plugin source

## Pending

- [ ] Register marketplace in Claude Code's `known_marketplaces.json` (step 5 from original plan)
- [ ] Install plugins from marketplace via `/plugin install` (step 6 from original plan)

## Notes

- GitHub account: `cbrandborg`, authenticated via `gh`
- After changes, run `/reload-plugins` to pick up updates
- Marketplace format reference: `/Users/priv/.claude/plugins/marketplaces/claude-plugins-official/`
