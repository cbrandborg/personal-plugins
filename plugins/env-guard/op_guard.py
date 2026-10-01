"""1Password CLI (`op`) rules shared by the Claude Code, Codex, and Hermes adapters.

Every `op` invocation in a shell command is classified as deny, ask, or pass.
Deny covers only commands known to put a secret where an agent can read it:
printing values, writing them to files, sharing items, or creating tokens.
Every other op command that contacts 1Password asks, because the 1Password
approval prompt doesn't say which command is asking; a Claude Code prompt is
the only place the user sees it. Commands the hook cannot verify also ask.
Only commands that never contact 1Password, such as `op whoami`, pass.

The rules come from testing op 2.32 with 1Password desktop app integration:
plain `op item get` prints one-time codes, `--format json` on get, create, and
edit prints passwords and TOTP seeds without `--reveal`, and `op run` masking
only hides exact matches of the secret.

Matching is order-independent on purpose. op skips unknown `--flag value`
pairs while looking up subcommands, so `op --vault whoami item get x` runs
`item get`. Any positional word can therefore be the real subcommand, and a
rule fires when its words appear anywhere before `--`.
"""

from __future__ import annotations

import codecs
import os
import re
import shlex
from typing import Any, Iterable, Iterator, Mapping, Optional, Tuple

DENY = "deny"
ASK = "ask"

Decision = Tuple[str, str]

# Same tool names as env_guard.COMMAND_TOOLS. Kept separate so this module
# loads both from the Claude hook script and from the Hermes package.
COMMAND_TOOLS = {"Bash", "terminal"}
NESTED_SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash", "fish"}

MAX_COMMAND_LENGTH = 100_000
MAX_ARGS = 64
MAX_DEPTH = 3

# Global flags that consume the next token unless written as --flag=value.
VALUE_FLAGS = {"--account", "--config", "--encoding", "--format", "--session"}

# `op` as a command word: not part of op_guard, op://, op.json, or ~/.config/op/.
OP_WORD = re.compile(r"(?i)(?<![\w.-])op(?:\.exe)?(?![\w:./-])")
SHELL_COMMAND_FLAG = re.compile(r"-[A-Za-z]*c[A-Za-z]*")
REDIRECT = re.compile(r"\d*(?:[<>]+&?|&>+)\d*")
# Shell features that can build or hide an op call the hook cannot evaluate.
DYNAMIC = re.compile(
    r"\$'|\$\{|\$\(|`|<<|<\(|\b(?:eval|xargs|source|alias)\b"
    r"|(?:^|[\s;&|(])\.\s"
    r"|\benv\b[^\n;&|]{0,200}?\s-[A-Za-z]*S"
    r"|\|\s*(?:sudo\s+)?(?:[\w./-]{0,100}/)?(?:sh|bash|zsh|dash|ksh|ash|fish)\b"
    r"|\(\)\s*\{"
    r"|\{[^{}\s]*,[^{}\s]*\}"
)
OP_FORMAT_ENV = re.compile(r"\bOP_FORMAT\b")
ANSI_C_STRING = re.compile(r"\$'((?:[^'\\]|\\.)*)'")

# op accepts plural group names and short subcommand aliases.
ALIASES = {
    "items": "item",
    "documents": "document",
    "vaults": "vault",
    "users": "user",
    "groups": "group",
    "accounts": "account",
    "ls": "list",
    "rm": "delete",
    "remove": "delete",
}
TRUE_VALUES = {"", "1", "t", "true"}
USE_RUN = "Pass secrets to programs with `op run` and op:// references instead."


def _is_separator(token: str) -> bool:
    if not token or not set(token) <= set("();|&\n<>"):
        return False
    return token in {"&", "&&"} or any(character in token for character in ";|()\n")


def _flag_name(arg: str) -> str:
    return arg.split("=", 1)[0]


def _archived(head: list[str]) -> bool:
    """True only when every --archive is unambiguous and truthy.

    Relaxing a deny must not depend on text bash ignores, so --archive after
    a comment or redirection does not count. pflag keeps the last value of a
    repeated flag and reads f/false/0 as false, so any falsy copy cancels it.
    """
    cut = next(
        (
            index
            for index, arg in enumerate(head)
            if arg.startswith("#") or REDIRECT.fullmatch(arg)
        ),
        len(head),
    )
    positions = [i for i, arg in enumerate(head) if _flag_name(arg) == "--archive"]
    if not positions:
        return False
    return all(
        index < cut and head[index].partition("=")[2].lower() in TRUE_VALUES
        for index in positions
    )


def _json_output(head: list[str], json_env: bool) -> bool:
    if json_env:
        return True
    for index, arg in enumerate(head):
        lowered = arg.lower()
        if lowered == "--format=json":
            return True
        if lowered == "--format" and index + 1 < len(head):
            if head[index + 1].lower() == "json":
                return True
    return False


# op commands that never contact 1Password, so they cannot trigger its
# approval prompt. Matched exactly, after dropping global flag values.
LOCAL_COMMANDS = {("whoami",), ("signout",), ("update",), ("account", "list")}


def _exposes(
    words: set[str],
    flags: set[str],
    json_output: bool,
) -> Iterator[Decision]:
    """Deny tier: commands known to put a secret where an agent can read it."""
    if "read" in words:
        yield DENY, f"`op read` prints secret values into the transcript. {USE_RUN}"
    if "inject" in words:
        yield DENY, (
            "`op inject` writes resolved secrets to stdout or a plaintext file. "
            f"{USE_RUN}"
        )
    if "run" in words and "--no-masking" in flags:
        yield DENY, "`op run --no-masking` prints secrets unmasked."
    if "signin" in words and "--raw" in flags:
        yield DENY, "`op signin --raw` prints a session token."
    if "create" in words:
        for group in ("service-account", "connect", "events-api"):
            if group in words:
                yield DENY, (
                    f"`op {group} ... create` prints or writes a new access token "
                    "or credentials file."
                )
    if "item" in words:
        if "get" in words:
            yield DENY, (
                "`op item get` prints secrets even without --reveal: plain "
                "output shows one-time codes and --format json shows "
                f"passwords and TOTP seeds. {USE_RUN}"
            )
        if "share" in words:
            yield DENY, "`op item share` creates a link anyone with the URL can open."
        if json_output:
            for sub in ("create", "edit", "move"):
                if sub in words:
                    yield DENY, (
                        f"`op item {sub}` with JSON output prints passwords and "
                        "TOTP seeds."
                    )
    if "document" in words and "get" in words:
        yield DENY, "`op document get` downloads a stored file."


def _needs_approval(words: set[str], archived: bool) -> Iterator[Decision]:
    """Ask tier with a specific reason. Unlisted commands get a generic one."""
    if "run" in words:
        if "plugin" in words:
            yield ASK, "`op plugin run` hands stored credentials to another CLI."
        else:
            yield ASK, (
                "`op run` hands secrets to a program that can still print them. "
                "Masking only hides exact matches."
            )
    for group in ("item", "document"):
        if group not in words:
            continue
        if "delete" in words:
            if archived:
                yield ASK, f"`op {group} delete --archive` moves it to the Archive."
            else:
                yield ASK, f"`op {group} delete` deletes permanently."
        for sub in ("create", "edit", "move"):
            if sub in words:
                yield ASK, f"`op {group} {sub}` changes vault contents."
        if "list" in words:
            yield ASK, f"`op {group} list` shows every title in the vault."
    if words & {"grant", "revoke"}:
        yield ASK, "`op ... grant/revoke` changes who can open a vault or group."
    changes = words & {"create", "edit", "delete"}
    for group in ("vault", "group"):
        if group in words and changes:
            yield ASK, f"`op {group} create/edit/delete` changes 1Password {group}s."
    if "user" in words and words & {
        "provision",
        "confirm",
        "edit",
        "suspend",
        "reactivate",
        "delete",
    }:
        yield ASK, "`op user` changes 1Password users."
    if "account" in words and words & {"add", "forget"}:
        yield ASK, "`op account add/forget` changes which accounts op can use."


def _local_only(head: list[str]) -> bool:
    """True for op commands that never contact 1Password.

    Passing is a relaxation, so this matches exact command shapes only. Values
    of global flags are dropped first, as op itself consumes them
    (`op whoami --account x`).
    """
    words: list[str] = []
    skip_value = False
    for arg in head:
        if skip_value:
            skip_value = False
            continue
        if arg.startswith("-"):
            skip_value = _flag_name(arg).lower() in VALUE_FLAGS and "=" not in arg
            continue
        words.append(ALIASES.get(arg.lower(), arg.lower()))
    if tuple(words) in LOCAL_COMMANDS:
        return True
    return len(words) <= 2 and bool(words) and words[0] == "completion"


def _strictest(decisions: Iterable[Optional[Decision]]) -> Optional[Decision]:
    strictest: Optional[Decision] = None
    for decision in decisions:
        if decision is None:
            continue
        if decision[0] == DENY:
            return decision
        if strictest is None:
            strictest = decision
    return strictest


def _head(args: list[str]) -> list[str]:
    """Return op's own arguments, without the child command after `--`.

    A `--` right after a bare flag may be that flag's value (pflag consumes
    it in `op --account -- read`), so it does not end op's arguments.
    """
    for index, arg in enumerate(args):
        if arg != "--":
            continue
        previous = args[index - 1] if index else ""
        if previous.startswith("-") and "=" not in previous:
            continue
        return args[:index]
    return args


def classify(args: list[str], json_env: bool = False) -> Optional[Decision]:
    """Classify the arguments that follow `op`.

    The child command of `op run` after `--` is not classified here; any `op`
    in it is classified on its own by the scanner.
    """
    head = _head(args)
    words = {ALIASES.get(arg.lower(), arg.lower()) for arg in head if not arg.startswith("-")}
    if not words:
        return None
    flags = {_flag_name(arg).lower() for arg in head if arg.startswith("-")}
    denied = _strictest(_exposes(words, flags, _json_output(head, json_env)))
    if denied:
        return denied
    asked = _strictest(_needs_approval(words, _archived(head)))
    if asked:
        return asked
    if _local_only(head):
        return None
    return ASK, (
        "This op command contacts 1Password, whose approval prompt doesn't say "
        "which command is asking."
    )


def _tokens(command: str) -> list[str]:
    # Nested shell source can carry its own backslash-newlines.
    lexer = shlex.shlex(
        command.replace("\\\n", ""), posix=True, punctuation_chars="();<>|&\n"
    )
    lexer.whitespace_split = True
    # Newlines end commands, so they are punctuation rather than whitespace.
    lexer.whitespace = " \t\r"
    # Bash only starts a comment at a word boundary; shlex would also start
    # one inside `a#` and hide the rest of the line.
    lexer.commenters = ""
    return list(lexer)


def _probe(command: str) -> str:
    """Approximate the words bash builds, for the cheap "is op here?" check.

    Decodes $'...' escapes and drops quotes and backslashes, so `o''p`,
    `o\\p`, and `$'\\x6fp'` all show up as `op`.
    """

    def decode(match: re.Match) -> str:
        try:
            return codecs.decode(
                match.group(1).encode("latin-1", "backslashreplace"),
                "unicode_escape",
            )
        except Exception:
            return match.group(1)

    return re.sub(r"[\"'\\]", "", ANSI_C_STRING.sub(decode, command))


def _command_name(token: str) -> str:
    name = os.path.basename(token.strip("`")).lower()
    return name[:-4] if name.endswith(".exe") else name


def _scan(
    command: str, json_env: bool, depth: int
) -> tuple[Optional[Decision], bool, bool]:
    """Return (strictest decision, op invocation found, op hidden in a word).

    A word hides op when it contains op but is neither an op invocation nor
    shell source the scanner recursed into, for example a Python -c string.
    """
    if depth > MAX_DEPTH:
        return (ASK, "This command nests shells too deeply to check."), True, False
    try:
        tokens = _tokens(command)
    except ValueError:
        return (ASK, "This command uses quoting the hook can't parse."), True, False

    # Index of the next separator at or after each position, for linear scans.
    next_separator = [len(tokens)] * (len(tokens) + 1)
    for index in range(len(tokens) - 1, -1, -1):
        next_separator[index] = (
            index if _is_separator(tokens[index]) else next_separator[index + 1]
        )

    decisions: list[Optional[Decision]] = []
    found = False
    hidden = False
    seen_shell = False
    for index, token in enumerate(tokens):
        name = _command_name(token)
        if name == "op":
            found = True
            end = next_separator[index + 1]
            if end - index - 1 > MAX_ARGS:
                decisions.append((ASK, "This command passes too many arguments to op to check."))
            else:
                decisions.append(classify(tokens[index + 1 : end], json_env))

        previous = tokens[index - 1] if index else ""
        nested = None
        if previous == "eval" or (seen_shell and SHELL_COMMAND_FLAG.fullmatch(previous)):
            nested = token
        elif "$(" in token or "`" in token:
            nested = token.replace("$(", " ; ").replace("`", " ; ").replace(")", " ; ")
        if nested is not None and OP_WORD.search(_probe(nested)):
            decision, nested_found, nested_hidden = _scan(nested, json_env, depth + 1)
            decisions.append(decision)
            found = found or nested_found
            hidden = hidden or nested_hidden
        elif name != "op" and OP_WORD.search(_probe(token)):
            # op:// references are only suspicious without a real op call,
            # which the "not found" check in scan_command covers.
            hidden = True

        if name in NESTED_SHELLS:
            seen_shell = True
        if decisions and decisions[-1] and decisions[-1][0] == DENY:
            break
    return _strictest(decisions), found, hidden


def scan_command(command: str) -> Optional[Decision]:
    """Return the strictest decision for any `op` call in a shell command."""
    # bash drops backslash-newline before splitting words, so `o\<newline>p`
    # is `op`.
    command = command.replace("\\\n", "") if command else command
    if not command:
        return None
    probe = _probe(command)
    if not OP_WORD.search(probe) and "op://" not in probe.lower():
        return None
    if len(command) > MAX_COMMAND_LENGTH:
        return ASK, "This command is too long to check for op calls."
    json_env = bool(OP_FORMAT_ENV.search(command)) or (
        os.environ.get("OP_FORMAT", "").lower() == "json"
    )
    decision, found, hidden = _scan(command, json_env, 0)
    if decision and decision[0] == DENY:
        return decision
    if hidden or not found:
        return ASK, (
            "This command mentions op where the hook can't verify it, such as "
            "inside a quoted string or another language."
        )
    if DYNAMIC.search(command):
        return decision or (
            ASK,
            "This command runs op with shell expansion the hook can't evaluate.",
        )
    return decision


def tool_decision(
    tool_name: str,
    args: Optional[Mapping[str, Any]],
) -> Optional[Decision]:
    """Return (decision, reason) for a command tool call that runs `op`."""
    if tool_name not in COMMAND_TOOLS or not isinstance(args, Mapping):
        return None
    command = args.get("command")
    return scan_command(command) if isinstance(command, str) else None
