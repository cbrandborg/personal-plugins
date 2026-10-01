"""Native Hermes env-guard plugin registration."""

from __future__ import annotations

import importlib
from typing import Any, Mapping, Optional

from .env_guard import blocked_reason
from .op_guard import DENY, tool_decision


def _hermes_session_cwd(task_id: Any) -> Optional[str]:
    """Best-effort lookup of Hermes' authoritative per-task working directory."""
    if not isinstance(task_id, str) or not task_id:
        return None
    try:
        terminal_tool = importlib.import_module("tools.terminal_tool")
        cwd = terminal_tool.get_session_cwd(task_id)
    except Exception:
        return None
    return cwd if isinstance(cwd, str) and cwd else None


def _pre_tool_call(
    tool_name: str = "",
    args: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
):
    """Block .env access and deny-tier 1Password CLI calls.

    Hermes hooks can only block, so ask-tier `op` calls pass through to the
    1Password app's own approval prompt.
    """
    try:
        op_decision = tool_decision(tool_name, args)
    except Exception:
        op_decision = None
    if op_decision and op_decision[0] == DENY:
        return {"action": "block", "message": f"1Password CLI blocked: {op_decision[1]}"}
    cwd = kwargs.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        cwd = _hermes_session_cwd(kwargs.get("task_id") or kwargs.get("session_id"))
    try:
        reason = blocked_reason(tool_name, args, cwd if isinstance(cwd, str) else None)
    except Exception:
        reason = "the .env check failed on this input"
    if reason:
        return {"action": "block", "message": f".env blocked: {reason}"}
    return None


def register(ctx):
    """Register the native Hermes pre-tool guard."""
    ctx.register_hook("pre_tool_call", _pre_tool_call)
