#!/usr/bin/env python3
"""Session-scoped generation limit for the Gemini image hook.

This hook is POSIX-only: it relies on directory-relative no-follow opens and
advisory file locking. Unsupported platforms fail closed with a deny result.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

DEFAULT_MAX_GENERATIONS = 5
MAX_COUNTER_DIGITS = 12
MAX_HOOK_INPUT_BYTES = 64 * 1024
MAX_SETTINGS_BYTES = 64 * 1024


def emit(permission: str, reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": permission,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


def read_max_generations(cwd: Path, home: Path) -> int:
    for root in (cwd, home):
        settings = root / ".claude" / "gemini-images.local.md"
        try:
            with settings.open("rb") as handle:
                raw = handle.read(MAX_SETTINGS_BYTES + 1)
            if len(raw) > MAX_SETTINGS_BYTES:
                raise ValueError(f"settings file is larger than {MAX_SETTINGS_BYTES} bytes")
            lines = raw.decode("utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        if not lines or lines[0].strip() != "---":
            continue
        try:
            closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
        except StopIteration:
            continue
        frontmatter = "\n".join(lines[1:closing])
        match = re.search(r"(?m)^max_generations:\s*([0-9]+)\s*$", frontmatter)
        if match and len(match.group(1)) <= MAX_COUNTER_DIGITS:
            return int(match.group(1))
    return DEFAULT_MAX_GENERATIONS


def state_directory(home: Path) -> Path:
    explicit = os.environ.get("CLAUDE_PLUGIN_DATA")
    if explicit:
        return Path(explicit).expanduser()
    state_home = Path(os.environ.get("XDG_STATE_HOME", home / ".local" / "state"))
    return state_home / "personal-plugins" / "gemini-images"


def secure_directory_fd(directory: Path) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory_flag is None or not hasattr(os, "getuid"):
        raise OSError("secure POSIX file flags are unavailable")

    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(directory, os.O_RDONLY | directory_flag | nofollow)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise OSError("state path is not a directory")
        if metadata.st_uid != os.getuid():
            raise OSError("state directory is owned by another user")
        os.fchmod(descriptor, 0o700)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def secure_counter_fd(directory_fd: int, filename: str) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None or not hasattr(os, "getuid"):
        raise OSError("secure POSIX file flags are unavailable")

    flags = os.O_RDWR | os.O_CREAT | os.O_NONBLOCK | nofollow
    descriptor = os.open(filename, flags, 0o600, dir_fd=directory_fd)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("counter is not a regular file")
        if metadata.st_uid != os.getuid():
            raise OSError("counter is owned by another user")
        if metadata.st_nlink != 1:
            raise OSError("counter has multiple hard links")
        os.fchmod(descriptor, 0o600)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def main() -> int:
    try:
        import fcntl
    except ImportError:
        return emit("deny", "Secure generation counting is unavailable on this platform.")

    try:
        raw_input = sys.stdin.buffer.read(MAX_HOOK_INPUT_BYTES + 1)
        if len(raw_input) > MAX_HOOK_INPUT_BYTES:
            return emit("deny", f"Hook input exceeds {MAX_HOOK_INPUT_BYTES} bytes.")
        payload = json.loads(raw_input)
    except (json.JSONDecodeError, UnicodeError, OSError, RecursionError) as exc:
        return emit("deny", f"Invalid hook input: {exc}")
    if not isinstance(payload, dict):
        return emit("deny", "Invalid hook input: expected a JSON object.")

    if "session_id" in payload:
        session_id = payload["session_id"]
    else:
        session_id = os.environ.get("CLAUDE_SESSION_ID")
    if not isinstance(session_id, str) or not session_id.strip() or len(session_id) > 1024:
        return emit("deny", "No session identifier was provided; refusing an unscoped counter.")

    home = Path.home()
    cwd_value = payload.get("cwd")
    if not isinstance(cwd_value, str) or not cwd_value.strip() or len(cwd_value) > 4096:
        return emit("deny", "Invalid hook input: cwd must be a non-empty path string.")
    try:
        cwd = Path(cwd_value)
        maximum = read_max_generations(cwd, home)
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        return emit("deny", f"Cannot read generation settings safely: {exc}")
    directory = state_directory(home)
    directory_fd = None
    counter_fd = None

    try:
        directory_fd = secure_directory_fd(directory)
        key = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
        counter_fd = secure_counter_fd(directory_fd, f"{key}.count")
        with os.fdopen(counter_fd, "r+b") as handle:
            counter_fd = None
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return emit("deny", "Generation counter is busy; retry the request.")
            raw = handle.read(MAX_COUNTER_DIGITS + 2).strip()
            if raw and (not raw.isascii() or not raw.isdigit() or len(raw) > MAX_COUNTER_DIGITS):
                return emit("deny", "Generation counter state is invalid.")
            current = int(raw or b"0")
            if current >= maximum:
                return emit(
                    "deny",
                    f"Generation limit reached ({current}/{maximum}). "
                    "Use image settings to change the limit or start a new session.",
                )
            updated = current + 1
            handle.seek(0)
            handle.write(str(updated).encode("ascii"))
            handle.truncate()
            handle.flush()
            os.fsync(handle.fileno())
    except (OSError, UnicodeError, ValueError) as exc:
        return emit("deny", f"Cannot update generation counter safely: {exc}")
    finally:
        if counter_fd is not None:
            os.close(counter_fd)
        if directory_fd is not None:
            os.close(directory_fd)

    return emit("allow", f"Generation {updated} of {maximum}")


if __name__ == "__main__":
    raise SystemExit(main())
