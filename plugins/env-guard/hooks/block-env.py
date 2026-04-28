#!/usr/bin/env python3
"""PreToolUse hook: block tool calls whose path arguments resolve to .env.

Tokenizes the command, expands globs, and checks if any resolved basename
is a protected .env file. Cleaner than string-matching: `ls .eslintrc*`,
`cat *.py`, and `grep .env docs.txt` don't get blocked.

Allowed: .env.example, .env.sample, .env.template, .env.dist, .envrc.
Blocked: .env, .env.local, .env.production, .env.<anything-else>.

Extra suffixes can be allowed via the ENV_GUARD_EXTRA_ALLOWED_TAILS env var
(comma-separated, no leading dot), e.g. "shared,public" allows .env.shared
and .env.public.

Residual risk (not caught by design): python3 -c / node -e / eval / $(...) -
runtime code can't be statically analyzed without breaking normal usage.
Use `chmod 400 .env` for real defense.
"""
import glob, json, os, re, shlex, sys

DEFAULT_ALLOWED_TAILS = {"example", "sample", "template", "dist"}
_extra = os.environ.get("ENV_GUARD_EXTRA_ALLOWED_TAILS", "")
ALLOWED_TAILS = DEFAULT_ALLOWED_TAILS | {
    t.strip().lstrip(".") for t in _extra.split(",") if t.strip()
}
NESTED_SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash"}
FILE_TOOLS = {"Read", "Edit", "Write", "MultiEdit", "NotebookEdit"}
ASSIGN_RE = re.compile(r"^(?:[A-Za-z_]\w*|--?[A-Za-z][\w-]*)=(.+)$")


def is_protected(base: str) -> bool:
    if base == ".env":
        return True
    if not base.startswith(".env."):
        return False
    return base.rsplit(".", 1)[-1] not in ALLOWED_TAILS


def resolve(tok: str, cwd: str):
    m = ASSIGN_RE.match(tok)
    if m:
        tok = m.group(1)
    if tok.startswith("file://"):
        tok = tok[len("file://"):]
    tok = os.path.expanduser(os.path.expandvars(tok))
    if not tok:
        return []
    abs_path = tok if os.path.isabs(tok) else os.path.join(cwd, tok)
    if any(c in tok for c in "*?["):
        return glob.glob(abs_path) or [abs_path]
    return [abs_path]


def scan(cmd: str, cwd: str, depth: int = 0):
    if depth > 2 or not cmd:
        return None
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return None

    for i, tok in enumerate(tokens):
        if os.path.basename(tok) in NESTED_SHELLS:
            for j in range(i + 1, len(tokens) - 1):
                if tokens[j] == "-c":
                    r = scan(tokens[j + 1], cwd, depth + 1)
                    if r:
                        return f"nested {tok} -c -> {r}"
                    break

    for tok in tokens:
        for path in resolve(tok, cwd):
            if is_protected(os.path.basename(path)):
                return f"{tok!r} resolves to {path}"
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    name = payload.get("tool_name", "")
    inp = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()

    reason = None
    if name == "Bash":
        reason = scan(inp.get("command", "") or "", cwd)
    elif name in FILE_TOOLS:
        p = inp.get("file_path") or inp.get("notebook_path") or ""
        if p and is_protected(os.path.basename(p)):
            reason = f"{name} on {p}"

    if reason:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f".env blocked: {reason}",
            }
        }))


if __name__ == "__main__":
    main()
