#!/usr/bin/env python3
"""Claude Code PreToolUse adapter for the shared env-guard matcher."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Claude invokes this file directly, so expose the plugin root for the shared module.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env_guard import blocked_reason  # noqa: E402


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd")
    reason = blocked_reason(
        tool_name,
        tool_input,
        cwd if isinstance(cwd, str) and cwd else None,
    )
    if reason:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f".env blocked: {reason}",
                    }
                }
            )
        )


if __name__ == "__main__":
    main()
