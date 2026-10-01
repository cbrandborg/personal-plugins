## 0.3.0 - 2026-10-01

- Guard 1Password CLI (`op`) commands, shared by the Claude Code and Hermes adapters.
- Deny commands that print or leak secrets: `op read`, `op inject`, `op item get`,
  item create/edit/move with JSON output, `op run --no-masking`, `op item share`,
  `op document get`, `op signin --raw`, permanent deletes, token and admin commands.
- Ask in Claude Code before `op run`, `op plugin run`, item or document list,
  create, edit, move, and archive, and any `op` use the hook cannot verify.
  Hermes passes ask-tier calls through.
- Match op rules by word rather than position, because op skips unknown
  `--flag value` pairs when it looks up subcommands. `--help` no longer exempts.
- Run the op check before the `.env` check and isolate both, so a crash or slow
  scan in one cannot skip the other.
- Quote `${CLAUDE_PLUGIN_ROOT}` in `hooks/hooks.json` so plugin paths with spaces work.

## 0.2.0 - 2026-09-15

- Add a native Hermes `pre_tool_call` plugin guard.
- Share matching logic between native Hermes and Claude Code adapters.
- Cover Hermes file and terminal tool names and argument keys.

## 0.1.1 - 2026-09-07

- Check symlink targets and correct best-effort protection claims.

