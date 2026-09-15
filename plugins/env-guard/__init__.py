"""Native Hermes env-guard plugin registration."""

from __future__ import annotations

import importlib
from typing import Any, Mapping, Optional

from .env_guard import blocked_reason


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
    """Block supported tool calls that resolve to a protected .env file."""
    cwd = kwargs.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        cwd = _hermes_session_cwd(kwargs.get("task_id") or kwargs.get("session_id"))
    reason = blocked_reason(tool_name, args, cwd if isinstance(cwd, str) else None)
    if reason:
        return {"action": "block", "message": f".env blocked: {reason}"}
    return None


def register(ctx):
    """Register the native Hermes pre-tool guard."""
    ctx.register_hook("pre_tool_call", _pre_tool_call)
