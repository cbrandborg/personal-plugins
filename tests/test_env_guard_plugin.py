"""Regression tests for the native Hermes and Claude env-guard adapters."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "env-guard"


def load_plugin():
    name = "env_guard_plugin"
    spec = importlib.util.spec_from_file_location(
        name,
        PLUGIN_ROOT / "__init__.py",
        submodule_search_locations=[str(PLUGIN_ROOT)],
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class RecordingContext:
    def __init__(self):
        self.hooks = {}

    def register_hook(self, name, callback):
        self.hooks[name] = callback


class HermesAdapterTest(unittest.TestCase):
    def setUp(self):
        self.ctx = RecordingContext()
        load_plugin().register(self.ctx)
        self.guard = self.ctx.hooks["pre_tool_call"]

    def test_registers_guard_and_blocks_native_file_tools(self):
        for tool_name, args in (
            ("read_file", {"path": ".env"}),
            ("write_file", {"path": ".env.production", "content": "secret"}),
            ("patch", {"path": ".env.local", "old_string": "a", "new_string": "b"}),
            ("search_files", {"path": ".env", "pattern": "secret"}),
        ):
            with self.subTest(tool_name=tool_name):
                decision = self.guard(tool_name=tool_name, args=args)
                self.assertEqual(decision["action"], "block")
                self.assertIn(".env blocked", decision["message"])

    def test_terminal_uses_its_workdir_and_allows_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("SYNTHETIC=example", encoding="utf-8")
            (root / "alias.txt").symlink_to(root / ".env")

            blocked = self.guard(
                tool_name="terminal",
                args={"command": "cat alias.txt", "workdir": directory},
            )
            allowed = self.guard(
                tool_name="read_file",
                args={"path": str(root / ".env.example")},
            )

            self.assertEqual(blocked["action"], "block")
            self.assertIsNone(allowed)

    def test_preserves_claude_tool_names_and_argument_keys(self):
        decision = self.guard(tool_name="Read", args={"file_path": ".env"})
        self.assertEqual(decision["action"], "block")

    def test_blocks_v4a_patch_and_search_file_glob(self):
        v4a = self.guard(
            tool_name="patch",
            args={
                "mode": "patch",
                "patch": "*** Begin Patch\n*** Update File: .env.local\n@@\n-a\n+b\n*** End Patch",
            },
        )
        search = self.guard(
            tool_name="search_files",
            args={"path": ".", "target": "content", "file_glob": ".env.*"},
        )
        self.assertEqual(v4a["action"], "block")
        self.assertEqual(search["action"], "block")

    def test_blocks_v4a_header_without_space_after_marker(self):
        decision = self.guard(
            tool_name="patch",
            args={
                "mode": "patch",
                "patch": "*** Begin Patch\n***Update File: .env.local\n@@\n-a\n+b\n*** End Patch",
            },
        )

        self.assertEqual(decision["action"], "block")

    def test_blocks_v4a_flexible_header_and_move_whitespace(self):
        headers = (
            "*** Update  File: .env.local",
            "*** Update\tFile: .env.local",
            "*** Move  File: safe.txt -> .env.local",
            "*** Move File: safe.txt->.env.local",
        )
        for header in headers:
            with self.subTest(header=header):
                decision = self.guard(
                    tool_name="patch",
                    args={
                        "mode": "patch",
                        "patch": f"*** Begin Patch\n{header}\n*** End Patch",
                    },
                )
                self.assertEqual(decision["action"], "block")

    def test_blocks_v4a_move_from_protected_source(self):
        decision = self.guard(
            tool_name="patch",
            args={
                "mode": "patch",
                "patch": "*** Begin Patch\n*** Move File: .env.local -> safe.txt\n*** End Patch",
            },
        )

        self.assertEqual(decision["action"], "block")

    def test_blocks_v4a_move_to_protected_destination(self):
        decision = self.guard(
            tool_name="patch",
            args={
                "mode": "patch",
                "patch": "*** Begin Patch\n*** Move File: safe.txt -> .env.local\n*** End Patch",
            },
        )

        self.assertEqual(decision["action"], "block")

    def test_blocks_search_file_glob_with_unlisted_env_prefix(self):
        decision = self.guard(
            tool_name="search_files",
            args={"path": ".", "target": "content", "file_glob": ".env.a*"},
        )

        self.assertEqual(decision["action"], "block")

    def test_native_relative_symlink_uses_terminal_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env.secret").write_text("SYNTHETIC=example", encoding="utf-8")
            (root / "alias.txt").symlink_to(root / ".env.secret")
            with mock.patch.dict(os.environ, {"TERMINAL_CWD": directory}):
                decision = self.guard(tool_name="read_file", args={"path": "alias.txt"})
            self.assertEqual(decision["action"], "block")

    def test_native_relative_path_uses_hermes_task_cwd(self):
        task_id = "env-guard-task-cwd-test"
        with (
            tempfile.TemporaryDirectory() as task_directory,
            tempfile.TemporaryDirectory() as terminal_directory,
        ):
            task_root = Path(task_directory)
            (task_root / ".env.secret").write_text(
                "SYNTHETIC=example", encoding="utf-8"
            )
            (task_root / "alias.txt").symlink_to(task_root / ".env.secret")
            terminal_tool = types.SimpleNamespace(
                get_session_cwd=lambda requested: (
                    task_directory if requested == task_id else None
                )
            )

            with (
                mock.patch.object(importlib, "import_module", return_value=terminal_tool),
                mock.patch.dict(os.environ, {"TERMINAL_CWD": terminal_directory}),
            ):
                decision = self.guard(
                    tool_name="read_file",
                    args={"path": "alias.txt"},
                    task_id=task_id,
                )

            self.assertEqual(decision["action"], "block")


class ClaudeCommandHookTest(unittest.TestCase):
    def test_command_hook_still_emits_claude_deny_shape(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "cat .env"}}
        result = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "hooks" / "block-env.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
