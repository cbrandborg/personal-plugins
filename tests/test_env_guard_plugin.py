"""Regression tests for the native Hermes and Claude env-guard adapters."""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
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


def run_claude_hook(command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    return subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / "hooks" / "block-env.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )


class ClaudeCommandHookTest(unittest.TestCase):
    def test_command_hook_still_emits_claude_deny_shape(self):
        result = run_claude_hook("cat .env")

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")

    def test_command_hook_denies_and_asks_for_op(self):
        for command, decision in (
            ("op read op://Employee/item/password", "deny"),
            ("op run -- ./deploy.sh", "ask"),
        ):
            with self.subTest(command=command):
                result = run_claude_hook(command)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual(output["permissionDecision"], decision)
                self.assertIn("1Password CLI", output["permissionDecisionReason"])

    def test_command_hook_is_silent_for_harmless_op(self):
        result = run_claude_hook("op vault list")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_env_check_crash_cannot_skip_op_denial(self):
        for command in (
            "echo \u0000; op read op://v/i/f",
            "echo \ud800; op read op://v/i/f",
        ):
            with self.subTest(command=repr(command)):
                result = run_claude_hook(command)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual(output["permissionDecision"], "deny")


def load_op_guard():
    spec = importlib.util.spec_from_file_location(
        "env_guard_op_guard", PLUGIN_ROOT / "op_guard.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OpGuardTest(unittest.TestCase):
    """Rules from testing op 2.32 against a dummy 1Password item."""

    def setUp(self):
        self.op = load_op_guard()

    def decision(self, command):
        result = self.op.scan_command(command)
        return result[0] if result else None

    def assert_decisions(self, expected, commands):
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), expected)

    def test_denies_commands_that_print_or_leak_secrets(self):
        self.assert_decisions(
            "deny",
            (
                "op read op://Employee/item/password",
                "op item get item --vault Employee",
                "op item get item --format json",
                "op item get item --otp",
                "op --format json item get item",
                "op items get item",
                "/opt/homebrew/bin/op read op://v/i/f",
                "OP_ACCOUNT=team op read op://v/i/f",
                "op --account team read op://v/i/f",
                "echo 'pw={{ op://v/i/f }}' | op inject",
                "op inject -i tpl.yml -o out.yml",
                "op run --no-masking -- printenv TOKEN",
                "op item share item --expires-in 1h",
                "op item delete item",
                "op item rm item",
                "op document get doc --out-file contract.pdf",
                "op signin --raw",
                "op service-account create bot",
                "op connect token create t --server s",
                "op events-api create e",
                "op vault create v",
                "op vault user grant --vault v --user u",
                "op group user grant --group g --user u",
                "op user delete u",
                "op account forget team",
            ),
        )

    def test_help_flags_do_not_exempt_commands(self):
        self.assert_decisions(
            "deny",
            (
                "op read --help",
                "op item get -h",
                "op read op://v/i/f # --help",
                "op read op://v/i/f\necho --help",
                "op read op://v/i/f >--help",
                "op read op://v/i/f --help=false",
                "op run --no-masking --help=false -- printenv X",
                "op signin --raw -h=false",
            ),
        )

    def test_flag_values_cannot_pose_as_subcommands(self):
        # op skips unknown `--flag value` pairs while finding subcommands.
        self.assert_decisions(
            "deny",
            (
                "op item --vault Employee get item",
                "op --vault whoami item get x --vault Private",
                "op item --vault template get x --vault Private",
                "op item --vault list get x --vault Private",
                "op --file-mode whoami read op://v/i/f --file-mode 0600",
                "op vault --name list edit v --name new",
                "op group --description list delete g",
            ),
        )

    def test_archive_must_be_unambiguous_to_relax_delete(self):
        self.assert_decisions(
            "deny",
            (
                "op item delete item --archive=false",
                "op item delete item --archive=f",
                "op item delete item --archive=F",
                "op item delete item --archive --archive=false",
                "op item delete item # --archive",
                "op item delete item >--archive",
            ),
        )
        self.assert_decisions("ask", ("op item delete item --archive 2>&1",))

    def test_denies_json_output_from_item_changes(self):
        self.assert_decisions(
            "deny",
            (
                "op item edit item --format json password=y",
                "op item create --category password --title t --format=json",
                "OP_FORMAT=json op item create --category password --title t",
                "op --format json item move item --destination-vault b",
            ),
        )

    def test_denies_op_hidden_inside_other_commands(self):
        self.assert_decisions(
            "deny",
            (
                "sh -c 'op read op://v/i/f'",
                'bash -lc "op item get item"',
                "bash -ce 'op read op://v/i/f'",
                'echo "$(op read op://v/i/f)"',
                "echo $(op read op://v/i/f)",
                "echo `op read op://v/i/f`",
                'eval "op read op://v/i/f"',
                "op vault list && op read op://v/i/f",
                "op vault list\nop read op://v/i/f",
                "op run -- printenv X; op read op://v/i/f",
                "op run -- op read op://v/i/f",
                "echo a#; op read op://v/i/f",
                "OP read op://v/i/f",
                "op.exe read op://v/i/f",
                "o\\\np read op://v/i/f",
                "o''p read op://v/i/f",
                'o""p read op://v/i/f',
                "o\\p read op://v/i/f",
                "op --account -- read op://v/i/f",
                "op --account -- item get item",
            ),
        )

    def test_asks_before_using_or_changing_secrets(self):
        self.assert_decisions(
            "ask",
            (
                "op run -- printenv TOKEN",
                "TOKEN=op://v/i/f op run --account team -- ./deploy.sh",
                "op plugin run -- gh auth token",
                "op item list --vault Employee",
                "op item ls",
                "op item create --category password --title t",
                "op item edit item password=x",
                "op item move item --current-vault a --destination-vault b",
                "op item delete item --archive",
                "op document create file.pdf",
                "op document list",
            ),
        )

    def test_asks_when_op_cannot_be_verified(self):
        nested = "op read op://v/i/f"
        for _ in range(5):
            nested = "sh -c " + shlex.quote(nested)
        self.assert_decisions(
            "ask",
            (
                "$'op' read op://v/i/f",
                "op $'read' op://v/i/f",
                "op ${X:-read} op://v/i/f",
                "op r${X}ead op://v/i/f",
                "op $(echo read) op://v/i/f",
                "echo 'op read op://v/i/f' | bash",
                "bash <<< 'op read op://v/i/f'",
                "printf 'read op://v/i/f' | xargs op",
                "env -S 'op read op://v/i/f'",
                'f(){ op "$@"; }; f read op://v/i/f',
                "op {read,} op://v/i/f",
                "python3 -c \"import os; os.system('op read op://v/i/f')\"",
                "bash -c -- 'op read op://v/i/f'",
                "true # don't\ntrue; op read op://v/i/f",
                'grep -rn "op read" docs/',
                'git commit -m "op read is denied"',
                "op whoami; python3 -c \"import os; os.system('op read op://v/i/f')\"",
                "op vault list && ssh host 'op read op://v/i/f'",
                "$'\\x6fp' read op://v/i/f",
                "${X}p read op://v/i/f",
                "echo 'API_KEY=op://v/i/f' >> app.env",
                nested,
                "op vault list; " + "x" * 200_000,
            ),
        )

    def test_long_commands_are_checked_quickly(self):
        for command, expected in (
            ("op " * 20_000 + "; op read op://v/i/f", "deny"),
            ("x " + "-c " * 20_000 + "op read op://v/i/f", "deny"),
            ("op vault list; " + "env " * 20_000, None),
            ("op vault list | " + "a/" * 40_000, None),
        ):
            with self.subTest(length=len(command), expected=expected):
                started = time.monotonic()
                self.assertEqual(self.decision(command), expected)
                self.assertLess(time.monotonic() - started, 2)

    def test_passes_metadata_and_unrelated_commands(self):
        self.assert_decisions(
            None,
            (
                "op whoami",
                "op account list",
                "op vault list",
                "op signout",
                "op signin",
                "op --version",
                "op vault user list --vault v",
                "which op",
                "brew upgrade op",
                "cat ~/.config/op/config",
                "python3 -m unittest plugins/env-guard/op_guard.py",
                "jq . op.json",
                "echo opera",
            ),
        )

    def test_hermes_blocks_deny_tier_and_passes_ask_tier(self):
        ctx = RecordingContext()
        load_plugin().register(ctx)
        guard = ctx.hooks["pre_tool_call"]

        for command in (
            "op item get item --format json",
            "op read op://v/i/f # --help",
        ):
            with self.subTest(command=command):
                blocked = guard(tool_name="terminal", args={"command": command})
                self.assertEqual(blocked["action"], "block")
                self.assertIn("1Password CLI blocked", blocked["message"])
        asked = guard(tool_name="terminal", args={"command": "op run -- ./deploy.sh"})
        self.assertIsNone(asked)


if __name__ == "__main__":
    unittest.main()
