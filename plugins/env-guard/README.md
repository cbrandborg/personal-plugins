# env-guard

Experimental native Hermes plugin and Claude Code hook for catching accidental
reads and edits of `.env` files and 1Password CLI (`op`) commands that expose
secrets. This is a best-effort check, **not a security boundary**. Keep your
existing permission rules and sandbox restrictions.

## Behavior

The hook checks supported file-tool paths and tokenizes Bash commands. It checks
both the supplied basename and the resolved symlink target. It can recognize
nested shell commands and expand path variables and globs.

Protected names: `.env`, `.envrc`, and `.env.*`, except `.env.example`,
`.env.sample`, `.env.template`, and `.env.dist`. Never put credentials in these
allowed template files.

`ENV_GUARD_EXTRA_ALLOWED_TAILS=shared,public` adds explicitly allowed suffixes.

## 1Password CLI (`op`)

Bash and Hermes `terminal` commands that mention `op` are classified into three
tiers. The rules come from testing op 2.32 with desktop app integration against
a dummy item: plain `op item get` prints one-time codes, `--format json` on
`get`, `create`, and `edit` prints passwords and TOTP seeds without `--reveal`,
and `op run` masking only hides exact matches, so piping through `rev` reveals
the secret.

| Tier | Commands | Claude Code | Hermes |
|---|---|---|---|
| Deny | `op read`, `op inject`, `op item get`, item create/edit/move with JSON output (`--format json` or `OP_FORMAT`), `op run --no-masking`, `op item share`, `op document get`, `op signin --raw`, `item`/`document delete` without an unambiguous `--archive`, `service-account`, `connect`, `events-api`, vault create/edit/delete, grant/revoke, user changes, `account add`/`forget` | Blocked | Blocked |
| Ask | `op run`, `op plugin run`, item and document list/create/edit/move, `delete --archive`, and any `op` use the hook cannot verify | Permission prompt showing the command | Passes |
| Pass | Other `op` commands, such as `whoami`, `account list`, `vault list`, `signout` | Passes | Passes |

The ask tier matters because the 1Password approval prompt does not show which
command is asking, so a Claude Code prompt is the only place you see it. Use
`op run` with `op://` references when a program needs a secret. Keep reference
files under a name the `.env` check allows, such as `app.env`, because
`op run --env-file .env` is blocked as `.env` access.

### How `op` calls are matched

op skips unknown `--flag value` pairs while it looks up subcommands, so
`op --vault whoami item get x` runs `item get`. The matcher therefore ignores
word order: a rule fires when its words appear anywhere among the arguments
before `--`. This also covers op aliases (`items`, `ls`, `rm`), global flags,
full paths, `op.exe`, uppercase `OP`, env-var prefixes, newlines, pipes and
chains. `--help` does not exempt a command.

Calls inside `sh -c`/`bash -lc`, quoted `eval`, `$(...)`, and backticks are
parsed and get the same rules. When `op` appears where the hook cannot evaluate
it, the result is ask: inside quoted strings or other languages, with `$'...'`,
`${...}`, unquoted `$(...)`, brace expansion, `xargs`, `env -S`, here-strings,
pipes into a shell, function definitions, unparseable quoting, more than three
nested shells, or commands over 100,000 characters.

`--archive` relaxes a delete from deny to ask only when every copy is truthy
and comes before any `#` or redirection, because pflag keeps the last value and
bash ignores comments.

## Limitations

This is not a complete shell parser. Dynamic code, directory-wide reads, hard
links, unsupported tools, and file changes after the check can bypass it.
False positives are possible when a command argument resembles a filename.
The hook cannot protect against a process that already has filesystem access.
`chmod 400` still allows the file's owner to read it.

The `op` checks cannot see calls made from script files or aliases, or names
built at runtime without any visible trace of op: `o=op; $o read` asks because
`op` appears, and a command with an `op://` reference asks, but a glob such as
`/opt/homebrew/bin/o? item get x` passes. An `op run` program you approve can
still print the secret. The 1Password app's approval prompt remains the real gate. Hermes
passes everything in the ask tier, including commands the hook cannot verify.

Matching on words rather than order trades precision for safety. Expect false
positives: `op item template get` is denied, `op item template list` asks, a
vault or item named `read` or `get` can trigger a denial, and commands that
only mention op, such as `grep "op read" docs/` or a commit message, ask.

Do not replace `permissions.deny` rules with this hook. Use it only as an
additional convenience check; host permissions and process isolation remain
separate responsibilities.

## Install in Hermes

Copy this directory to `~/.hermes/plugins/env-guard`, then enable it:

```text
hermes plugins enable env-guard
```

The root `plugin.yaml` and `__init__.py` register the native `pre_tool_call`
guard. It covers Hermes `read_file`, `write_file`, `patch`, `search_files`, and
`terminal` calls using their native `path`, `command`, and `workdir` arguments.

## Install in Claude Code

```text
/plugin marketplace add https://github.com/cbrandborg/personal-plugins
/plugin install env-guard@personal-plugins
```

Requires Python 3. Claude hook configuration remains in `hooks/hooks.json` and
uses the same matching logic as the native Hermes guard. Run regressions from
the repository root with `python3 -m unittest discover -s tests -v` or `just ci`.
