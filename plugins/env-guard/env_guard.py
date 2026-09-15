"""Shared matching logic for Claude Code and native Hermes adapters."""

from __future__ import annotations

import fnmatch
import glob
import os
import re
import shlex
from typing import Any, Mapping, Optional

DEFAULT_ALLOWED_TAILS = {"example", "sample", "template", "dist"}
NESTED_SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash"}
ASSIGN_RE = re.compile(r"^(?:[A-Za-z_]\w*|--?[A-Za-z][\w-]*)=(.+)$")
V4A_PATH_RE = re.compile(
    r"(?m)^\*\*\*\s*(?:Add|Update|Delete)\s+File:\s*(.+?)\s*$"
)
V4A_MOVE_RE = re.compile(
    r"(?m)^\*\*\*\s*Move\s+File:\s*(.+?)\s*->\s*(.+?)\s*$"
)

# Claude Code tool names and path keys remain supported by the command hook.
FILE_TOOL_PATH_KEYS = {
    "Read": ("file_path",),
    "Edit": ("file_path",),
    "Write": ("file_path",),
    "MultiEdit": ("file_path",),
    "NotebookEdit": ("notebook_path", "file_path"),
    # Native Hermes file tools.
    "read_file": ("path",),
    "write_file": ("path",),
    "patch": ("path",),
    "search_files": ("path",),
}
COMMAND_TOOLS = {"Bash", "terminal"}


def allowed_tails() -> set[str]:
    """Return default suffix exceptions plus current environment overrides."""
    extra = os.environ.get("ENV_GUARD_EXTRA_ALLOWED_TAILS", "")
    return DEFAULT_ALLOWED_TAILS | {
        tail.strip().lstrip(".") for tail in extra.split(",") if tail.strip()
    }


def is_protected(base: str) -> bool:
    if base in {".env", ".envrc"}:
        return True
    if not base.startswith(".env."):
        return False
    return base.rsplit(".", 1)[-1] not in allowed_tails()


def resolve(token: str, cwd: str) -> list[str]:
    match = ASSIGN_RE.match(token)
    if match:
        token = match.group(1)
    if token.startswith("file://"):
        token = token[len("file://") :]
    token = os.path.expanduser(os.path.expandvars(token))
    if not token:
        return []
    absolute = token if os.path.isabs(token) else os.path.join(cwd, token)
    if any(character in token for character in "*?["):
        return glob.glob(absolute) or [absolute]
    return [absolute]


def protected_path_reason(path: str, cwd: str) -> Optional[str]:
    for resolved in resolve(path, cwd):
        if is_protected(os.path.basename(resolved)) or is_protected(
            os.path.basename(os.path.realpath(resolved))
        ):
            return f"{path!r} resolves to {resolved}"
    return None


def protected_glob_reason(pattern: str) -> Optional[str]:
    """Return why a filename glob can select protected env files."""
    basename = os.path.basename(pattern.replace("\\", "/"))
    candidates = [".env", ".envrc", ".env.local", ".env.production", ".env.secret"]
    wildcard_indexes = [
        basename.find(character)
        for character in "*?["
        if character in basename
    ]
    if wildcard_indexes:
        literal_prefix = basename[: min(wildcard_indexes)]
        candidates.extend((literal_prefix, f"{literal_prefix}x"))
    if any(
        fnmatch.fnmatchcase(candidate, basename) and is_protected(candidate)
        for candidate in candidates
    ):
        return f"file_glob {pattern!r} can select protected env files"
    return None


def scan_command(command: str, cwd: str, depth: int = 0) -> Optional[str]:
    if depth > 2 or not command:
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None

    for index, token in enumerate(tokens):
        if os.path.basename(token) in NESTED_SHELLS:
            for option_index in range(index + 1, len(tokens) - 1):
                if tokens[option_index] == "-c":
                    reason = scan_command(tokens[option_index + 1], cwd, depth + 1)
                    if reason:
                        return f"nested {token} -c -> {reason}"
                    break

    for token in tokens:
        reason = protected_path_reason(token, cwd)
        if reason:
            return reason
    return None


def blocked_reason(
    tool_name: str,
    args: Optional[Mapping[str, Any]],
    cwd: Optional[str] = None,
) -> Optional[str]:
    """Return why a supported tool call targets a protected env file."""
    arguments = args if isinstance(args, Mapping) else {}
    base_cwd = cwd or os.environ.get("TERMINAL_CWD") or os.getcwd()

    if tool_name in COMMAND_TOOLS:
        command = arguments.get("command", "")
        if not isinstance(command, str):
            return None
        workdir = arguments.get("workdir") if tool_name == "terminal" else None
        command_cwd = workdir if isinstance(workdir, str) and workdir else base_cwd
        return scan_command(command, command_cwd)

    if tool_name == "patch" and arguments.get("mode") == "patch":
        patch_text = arguments.get("patch")
        if isinstance(patch_text, str):
            paths = V4A_PATH_RE.findall(patch_text)
            paths.extend(
                path
                for endpoints in V4A_MOVE_RE.findall(patch_text)
                for path in endpoints
            )
            for path in paths:
                if reason := protected_path_reason(path, base_cwd):
                    return f"patch on {reason}"

    if tool_name == "search_files":
        file_glob = arguments.get("file_glob")
        if isinstance(file_glob, str) and file_glob:
            if reason := protected_glob_reason(file_glob):
                return reason

    for key in FILE_TOOL_PATH_KEYS.get(tool_name, ()):
        path = arguments.get(key)
        if isinstance(path, str) and path:
            reason = protected_path_reason(path, base_cwd)
            if reason:
                return f"{tool_name} on {reason}"
    return None
