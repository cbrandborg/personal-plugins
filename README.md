# Personal Plugins

A Git-backed personal plugin marketplace for **Claude Code and Codex**. Each
plugin lives once in `plugins/<name>/`; its shared `skills/` content is shipped
to both agents through provider-specific manifests.

`AGENTS.md` is the source of project instructions. `CLAUDE.md` points directly
to it, so Claude Code and Codex work from the same guidance.

## Install

### Claude Code

```text
/plugin marketplace add https://github.com/cbrandborg/personal-plugins
/plugin install mattpocock-productivity@personal-plugins
```

### Codex

```bash
codex plugin marketplace add cbrandborg/personal-plugins
codex plugin add mattpocock-productivity@personal-plugins
```

For local Codex development from a clone, run `codex plugin marketplace add .`
at the repository root.

## Marketplace layout

```text
.claude-plugin/marketplace.json     # Claude Code marketplace
.agents/plugins/marketplace.json    # Codex marketplace
plugins/<name>/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  skills/
```

Plugin content is bundled by **provider and cohesive capability**. The first
sync-managed bundle is `mattpocock-productivity`, rather than five tiny
plugins: it has one upstream, one release cadence, and a clearly related set of
productivity workflows. A future source can be one plugin per provider, or a
provider/category bundle when that better matches how its upstream is released.

## Managed imports

`sources.json` declares imported Git sources. `sources.lock.json` records the
exact commit and source path for each skill currently shipped. Imported files
are vendored into the plugin, so a Git commit in this repository is
self-contained and reviewable.

Add a collection from a repository:

```bash
just add-skill mattpocock/skills skills/productivity mattpocock-productivity
```

Add one skill from a `skills.sh` page; the script resolves the backing GitHub
repository and discovers the skill's nested source path automatically:

```bash
just add-skills-sh https://skills.sh/mattpocock/skills/grill-me mattpocock-grill-me
```

If a skills.sh page maps ambiguously to a repository, pass an explicit source
path with the repository form:

```bash
just add-skill owner/repo skills/category/skill owner-skill
```

Check and apply updates:

```bash
just sync-skills --check
just sync-skills --apply
PYTHON=python3.13 just validate
just ci
```

An applied update compares every tracked skill directory independently. It
replaces **only** a skill whose normalized content differs upstream; it neither
touches sibling skills nor bumps a version when a source commit has no skill
content change. If one or more skills in the same bundle changed, the bundle is
bumped exactly once and its changelog names every changed skill. The marketplace
files do not duplicate plugin versions; the manifests are the single version
source.

## Automated weekly sync

`.github/workflows/sync-skills.yml` runs every Monday at 07:17 UTC and is also
available through **Run workflow**. It performs the same sync, validates the
marketplace, and commits content/version updates directly to `main`. If no
upstream skill content changed, it exits without making a commit.

## Current dual-agent plugins

| Plugin | Purpose |
| --- | --- |
| `mattpocock-productivity` | Five vendored productivity skills: `grill-me`, `grilling`, `handoff`, `teach`, and `writing-great-skills`. |
| `dm-kit` | D&D campaign authoring workflows for Obsidian. |
| `env-guard` | `.env` protection hooks. |
| `gemini-images` | Gemini image-generation workflows. |
| `xmind-campaign` | Turn XMind campaign maps into structured Obsidian vaults. |
