# env-guard

Experimental native Hermes plugin and Claude Code hook for catching accidental
reads and edits of `.env` files. This is a best-effort check, **not a security
boundary**. Keep your existing permission rules and sandbox restrictions.

## Behavior

The hook checks supported file-tool paths and tokenizes Bash commands. It checks
both the supplied basename and the resolved symlink target. It can recognize
nested shell commands and expand path variables and globs.

Protected names: `.env`, `.envrc`, and `.env.*`, except `.env.example`,
`.env.sample`, `.env.template`, and `.env.dist`. Never put credentials in these
allowed template files.

`ENV_GUARD_EXTRA_ALLOWED_TAILS=shared,public` adds explicitly allowed suffixes.

## Limitations

This is not a complete shell parser. Dynamic code, directory-wide reads, hard
links, unsupported tools, and file changes after the check can bypass it.
False positives are possible when a command argument resembles a filename.
The hook cannot protect against a process that already has filesystem access.
`chmod 400` still allows the file's owner to read it.

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
uses the same matching logic as the native Hermes guard. Plugin-local regressions
run with `python3 -m unittest discover -s tests -v`; repository regressions run
with `just ci` at the repository root.
