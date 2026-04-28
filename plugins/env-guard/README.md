# env-guard

A `PreToolUse` hook that blocks Claude Code from reading, writing, or editing `.env` files. Stops accidental exposure of secrets to the model and prevents the assistant from echoing them back into chat, logs, or commits.

## What gets blocked

- `.env`
- `.env.local`, `.env.production`, `.env.staging`, ... (any `.env.<x>` not in the allow list)

## What passes through

- `.env.example`
- `.env.sample`
- `.env.template`
- `.env.dist`
- `.envrc` (direnv)

These are the conventional names for committed-to-VCS templates that should never contain real secrets.

### Adding your own safe suffixes

If your project uses a non-standard convention (e.g. `.env.shared`, `.env.public`), extend the allow list with the `ENV_GUARD_EXTRA_ALLOWED_TAILS` environment variable. Comma-separated, no leading dots:

```json
// ~/.claude/settings.json
{
  "env": {
    "ENV_GUARD_EXTRA_ALLOWED_TAILS": "shared,public"
  }
}
```

That allows `.env.shared` and `.env.public` while keeping everything else blocked.

## How it works

The hook fires on `Bash`, `Read`, `Edit`, `Write`, `MultiEdit`, and `NotebookEdit`. For Bash it tokenises the command with `shlex`, expands globs, and unwraps env-var assignments and `file://` prefixes. For file tools it inspects the `file_path` argument directly. If any resolved basename matches a protected pattern, the call is denied with `permissionDecision: "deny"`.

It also recurses into nested shells (`sh -c "..."`, `bash -c "..."`, ...) up to depth 2, so wrapping a `cat .env` inside a subshell does not bypass it.

### What it does not catch (by design)

Runtime code execution that produces filenames dynamically: `python3 -c "open('.env')"`, `node -e "..."`, `eval`, `$(...)`. Statically analysing these would require breaking normal usage. For real defence, also run `chmod 400 .env`.

## Installation

```bash
/plugin marketplace add https://github.com/cbrandborg/personal-plugins
/plugin install env-guard@personal-plugins
```

Requires Python 3 on PATH (it is, on every macOS and most Linux dev boxes).

## Relationship to `permissions.deny`

If you previously protected `.env` files via `permissions.deny` patterns in `~/.claude/settings.json` (e.g. `"Read(.env*)"`, `"Bash(cat *.env*)"`, ...), this hook supersedes them. The hook is more thorough: it understands globs, env-var assignments, and nested shells, where the deny patterns rely on string matching against the literal command.

You can either:
- **Remove** the deny patterns once this plugin is installed (cleaner).
- **Keep** them as defense-in-depth (the hook will still take precedence when active, the deny patterns kick in if the plugin is ever disabled).

## Development

The hook script lives at `hooks/block-env.py` and is referenced from `hooks/hooks.json` via `${CLAUDE_PLUGIN_ROOT}`, so it works regardless of where the plugin is installed.

To test changes locally, edit the script and trigger a matching tool call - denied calls return a JSON `permissionDecisionReason` that names the resolving token and path.
