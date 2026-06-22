# Personal Plugins Marketplace

This repository is a Git-backed marketplace for **both Claude Code and Codex**.

`CLAUDE.md` is intentionally only a pointer to this file so both agents use the
same project guidance.

## Layout

Each installable plugin lives once under `plugins/<plugin-name>/`:

```text
plugins/<plugin-name>/
  .claude-plugin/plugin.json  # Claude Code metadata
  .codex-plugin/plugin.json   # Codex metadata
  skills/                     # portable Agent Skills payload
  agents/, commands/, hooks/  # optional shared components
```

The marketplace registries are provider-specific:

- `.claude-plugin/marketplace.json` for Claude Code.
- `.agents/plugins/marketplace.json` for Codex.

Plugin names and semantic versions must match between the two plugin manifests.
Keep skill instructions portable: use the Agent Skills `name` and `description`
frontmatter fields, and keep provider-only hooks or UI metadata outside the
skill instructions.

## Imported skills

Imported skills are vendored inside their provider bundle under `plugins/`.
`sources.json` declares the upstream Git source; `sources.lock.json` records
the exact revision currently shipped. Do not hand-edit a vendored source bundle
without also deciding whether it should remain sync-managed.

The importer removes Claude-only `disable-model-invocation` frontmatter while
vendoring. This is the one intentional normalization: it leaves a portable
`SKILL.md` payload that both Codex and Claude can load.

Use these commands:

```bash
just add-skill <source> <path> <plugin>
just sync-skills --check
just sync-skills --apply
just validate
```

The scheduled GitHub Action runs the same sync operation weekly. It bumps a
plugin's patch version and both manifests only when the vendored skill content
actually changes, then commits the reviewed-by-CI result to `main`.

## Validation

Run `just ci` before publishing. It validates the two marketplace registries,
provider-manifest consistency, source declarations, and every `SKILL.md`.
