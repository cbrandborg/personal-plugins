## 0.4.0 - 2026-10-01

- Deny only op commands known to expose a secret. Every other op command that
  contacts 1Password now asks, including `op vault list`, permanent deletes,
  and vault, user, group, and account changes, which used to pass or be denied.
  Only local commands such as `op whoami` and `op account list` pass.
- Add a Codex adapter (`hooks/codex-guard.py`, `hooks/codex-hooks.json`) that
  blocks both the deny and ask tiers, checks `apply_patch` edits to env files,
  and blocks when a check crashes.
- Keep the specific `op run` reason when an `op://` reference sits next to the
  call, instead of the generic "can't verify" message.

## 0.3.1 - 2026-10-01

- Stop the `.env` command tokenizer from treating `a#` as a comment, which hid
  the rest of the line (`echo a#; cat .env`).
- Recognize combined shell flags such as `bash -lc` and `sh -ec`, quoted `eval`
  arguments, `$(...)`, and backticks when looking for nested commands.
- Fall back to plain words on unbalanced quotes instead of skipping the check.
- Check the Claude Code Grep tool's `path` and `glob`.
- Deny instead of allowing when the `.env` check crashes on its input.

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

