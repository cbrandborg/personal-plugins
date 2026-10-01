#!/usr/bin/env python3
"""Claude Code PreToolUse adapter for the shared env-guard and op matchers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Claude invokes this file directly, so expose the plugin root for the shared module.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env_guard import blocked_reason  # noqa: E402
from op_guard import ASK, DENY, tool_decision  # noqa: E402


def emit(decision: str, reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd")

    # Run the cheap op check first and isolate both checks, so a crash or a
    # slow .env scan cannot skip an op denial.
    try:
        op_decision = tool_decision(tool_name, tool_input)
    except Exception:
        op_decision = (ASK, "This command could not be checked for op calls.")
    if op_decision and op_decision[0] == DENY:
        emit(DENY, f"1Password CLI blocked: {op_decision[1]}")
        return

    try:
        reason = blocked_reason(
            tool_name,
            tool_input,
            cwd if isinstance(cwd, str) and cwd else None,
        )
    except Exception:
        reason = None
    if reason:
        emit(DENY, f".env blocked: {reason}")
        return

    if op_decision:
        emit(ASK, f"1Password CLI: {op_decision[1]}")


if __name__ == "__main__":
    main()
