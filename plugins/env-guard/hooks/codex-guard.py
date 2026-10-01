#!/usr/bin/env python3
"""Codex PreToolUse adapter for the shared env-guard and op matchers.

Codex hooks can block but not ask: an "ask" reply, a timeout, or any exit
code other than 2 lets the command run. So this adapter turns every ask into
a block and blocks when a check crashes, instead of failing open.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Codex invokes this file directly, so expose the plugin root for the shared modules.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env_guard import blocked_reason  # noqa: E402
from op_guard import ASK, tool_decision  # noqa: E402

CODEX_CANNOT_ASK = (
    " Codex hooks can't ask for approval, so env-guard blocks it. Ask the user "
    "to run the command themselves if it is needed."
)


def block(reason: str) -> None:
    print(reason, file=sys.stderr)
    sys.exit(2)


def check(payload: dict) -> None:
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd")
    cwd = cwd if isinstance(cwd, str) and cwd else None
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return

    if tool_name == "apply_patch":
        reason = blocked_reason("patch", {"mode": "patch", "patch": command}, cwd)
        if reason:
            block(f".env blocked: {reason}")
        return

    op_decision = tool_decision(tool_name, {"command": command})
    if op_decision:
        decision, why = op_decision
        block(f"1Password CLI blocked: {why}" + (CODEX_CANNOT_ASK if decision == ASK else ""))

    reason = blocked_reason(tool_name, {"command": command}, cwd)
    if reason:
        block(f".env blocked: {reason}")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if not isinstance(payload, dict):
        return
    try:
        check(payload)
    except Exception:
        block("env-guard could not check this command, so it is blocked.")


if __name__ == "__main__":
    main()
