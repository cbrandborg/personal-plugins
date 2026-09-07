# One skill, from upstream to plugin

Run `python3.13 scripts/demo-import.py` from the repository root. The example
runs the real CLI against temporary local Git repositories and checks its output
files. No external repository or installed plugin is changed.

1. Create an upstream `skills/example/SKILL.md` with a summarization instruction.
2. Import it with `add <local-upstream> --path skills/example --plugin demo-bundle`.
3. Observe the generated bundle:

```text
plugins/demo-bundle/
  .claude-plugin/plugin.json   version 0.1.0
  .codex-plugin/plugin.json    version 0.1.0
  skills/example/SKILL.md
  CHANGELOG.md
sources.json                  local upstream and source path
sources.lock.json             resolved commit and payload hash
```

4. Commit an additional instruction upstream, then run `sync --check`.
   This lists the change without modifying installed content.
5. Run `sync --apply`. The example prints this diff:

```diff
 Summarize the supplied text.
+
+Include a short list of unresolved questions.
```

Both manifests move from `0.1.0` to `0.1.1`; the lock records the new upstream
commit and hash. An unchanged second sync leaves the version at `0.1.1`.

For real sources, the same process applies, with upstream attribution and
license notices preserved in the bundle. If you edit the local skill and
upstream changes it too, both `--check` and `--apply` report a conflict. Resolve
it deliberately before rerunning; the tool does not merge conflicting prose.
