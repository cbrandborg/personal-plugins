# Personal Plugins

I collect useful agent skills from different places and package them into plugins
for Claude Code and Codex. This repository contains the import and sync tooling,
the resulting bundles, and a few plugins I built for my own workflows.

**Personal tooling, shared as an experiment.** Imported skills retain their
upstream authorship. The marketplace registries are how the agents discover and
install the plugins; running a marketplace is not the purpose of this project.

## What the importer does

- Imports a skill or collection from a Git repository or a `skills.sh` link.
- Packages skills with separate Claude Code and Codex manifests.
- Records each imported skill's source path, revision, and content hash.
- Updates changed skills without rewriting unchanged siblings.
- Preserves local edits when upstream is unchanged; reports a conflict when both change.
- Stages an entire add/sync before applying it, including lock files and versions.
- Bumps each affected plugin once and records changed skills in its changelog.

The importer uses Python's standard library and Git. It assumes one writer at a
time. Recoverable errors are rolled back; applying several files is not an
atomic operation against a machine crash or another concurrent writer.

## Try an import and update locally

Requires Git and Python 3.13+. The example creates a synthetic upstream skill,
imports it, changes the upstream, checks the diff, applies the update, and
verifies the lock and version. It uses temporary directories, no network or keys,
and leaves this checkout unchanged.

```bash
python3.13 scripts/demo-import.py
```

See [the walkthrough](docs/import-example.md) for the resulting files and diff.

## Import your own skills

Install [just](https://github.com/casey/just) to use the shortcuts, or invoke
`python3.13 scripts/skills.py` directly. Use a new plugin name and source ID:

```bash
# Replace owner/repo and path with the upstream you want to import.
just add-skill owner/repo skills/example my-example --id example-source

# Import from a skills.sh page into a new bundle.
just add-skills-sh https://skills.sh/mattpocock/skills/grill-me my-grill-me --id my-grill-me-import

just sync-skills --check
just sync-skills --apply
```

`--id` identifies an upstream registration; `--plugin` identifies the destination
bundle. Multiple sources may share a bundle but must use distinct source IDs and
skill names. Reusing an existing ID is rejected. The source defaults to branch
`main`; use `--ref` for another branch or tag. The sync follows that reference;
the lock records the last imported content, not a command to restore a checkout.

A check is read-only. It exits nonzero on a conflict or fetch failure. Ordinary
available updates exit successfully and are listed for review. Failed adds and
syncs leave the original repository files unchanged for handled errors.

### Invocation policy changes

The importer removes the Claude-specific `disable-model-invocation` frontmatter
field. **This changes behavior:** a skill previously restricted to explicit
invocation may become eligible for automatic selection. This is the current
normalization policy, not a guarantee of equivalent behavior across agents.
Review imported instructions and their invocation policy before installation.

### Attribution

Review each upstream's license before redistributing its skills, including
repository-level notices that may live outside the selected skill directory.
The importer copies skill directories; it does not resolve license obligations
automatically. Preserve required notices inside the resulting plugin bundle.
See [third-party attribution](THIRD_PARTY.md).

## Bundles

| Bundle | Origin and scope | Status |
| --- | --- | --- |
| `mattpocock-productivity` | Matt Pocock's `grill-me`, `grilling`, `handoff`, `teach`, `writing-great-skills`, and `wayfinder`, packaged here | Imported; upstream revisions tracked |
| `dm-kit` | My Obsidian campaign-authoring workflows and canvas scripts | Experimental; offline canvas regressions |
| `gemini-images` | My Gemini MCP integration and image workflows | Experimental; offline helper tests, opt-in live API tests |
| `env-guard` | My accidental `.env` access check | Experimental Claude hook; not a security boundary |
| `xmind-campaign` | My older XMind-to-Obsidian migration workflows | Legacy; not part of the current automated test coverage |

My contribution to the imported bundle is packaging, normalization, and update
management. The skills themselves are credited to their upstream author.

## Install a bundle

These are host-specific entry points. Both manifest formats are validated, but
that is not an end-to-end compatibility guarantee. See [testing and support](docs/testing.md)
for the scope of verified behavior and manual installation checks.

Claude Code:

```text
/plugin marketplace add https://github.com/cbrandborg/personal-plugins
/plugin install mattpocock-productivity@personal-plugins
```

Codex:

```bash
codex plugin marketplace add cbrandborg/personal-plugins
codex plugin add mattpocock-productivity@personal-plugins
```

For Gemini authentication and standalone MCP setup, see [its README](plugins/gemini-images/README.md).

## Development

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-dev.lock
PYTHON=python just ci
```

CI validates the registries and skills, exercises importer failure handling and
bundled scripts, tests actual Gemini helpers, and runs the local import/update
example. It makes no model API calls. [Testing details](docs/testing.md).

The weekly sync job follows upstream, runs offline checks, and opens or updates a
pull request. It never publishes synchronized instructions directly to `main`.
Review every instruction change before merging; disable the schedule in your fork
if you prefer manual updates.

## Layout

```text
scripts/skills.py                   import and sync implementation
sources.json                       upstream registrations
sources.lock.json                  imported revisions and content hashes
plugins/<name>/                     bundled skills and plugin components
.claude-plugin/marketplace.json     Claude Code installation registry
.agents/plugins/marketplace.json    Codex installation registry
```

`AGENTS.md` contains contributor instructions; `CLAUDE.md` points to it.

## License

Original code and plugin content by Christian Brandborg are licensed under
[0BSD](LICENSE): use, modify, and redistribute them, including commercially,
without an attribution requirement.

Imported Matt Pocock skills remain under their [MIT license](plugins/mattpocock-productivity/LICENSE),
which requires retaining its copyright and license notice. The root license does
not replace third-party terms; see [attribution](THIRD_PARTY.md).
