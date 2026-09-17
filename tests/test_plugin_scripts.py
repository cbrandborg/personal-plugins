"""Offline behavior checks for bundled scripts using synthetic vaults/files."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import fcntl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'plugins/dm-kit/scripts'
GEMINI_HOOKS = ROOT / 'plugins/gemini-images/hooks'


class CanvasTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        chapter = self.root / "Chapters/01 - Miller's House"
        self.scene = chapter / "Scenes/01 - A visitor's arrival.md"
        self.scene.parent.mkdir(parents=True)
        self.scene.write_text('Example scene')
        self.canvas = chapter / 'Chapter.canvas'
        self.original = {'nodes': [{'id': 'note', 'type': 'text', 'text': self.scene.name}], 'edges': []}
        self.canvas.write_text(json.dumps(self.original))

    def add(self, scene=None):
        return subprocess.run([sys.executable, str(SCRIPTS / 'add-scene-to-canvas.py'),
            str(self.canvas), scene or self.scene.relative_to(self.root).as_posix()], capture_output=True, text=True)

    def test_retry_preserves_existing_content_and_node_id(self):
        first = self.add()
        self.assertEqual(first.returncode, 0, first.stderr)
        after = self.canvas.read_bytes()
        second = self.add()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(after, self.canvas.read_bytes())
        data = json.loads(after)
        self.assertEqual(data['nodes'][0], self.original['nodes'][0])
        self.assertEqual(len(data['nodes']), 2)
        self.assertEqual(data['edges'], [])

    def test_missing_and_outside_scene_leave_canvas_unchanged(self):
        before = self.canvas.read_bytes()
        for scene in ['Scenes/missing.md', '../outside.md']:
            self.assertNotEqual(self.add(scene).returncode, 0)
            self.assertEqual(before, self.canvas.read_bytes())

    def test_invalid_canvas_stays_unchanged(self):
        for invalid in ['{bad', '[]', '{"nodes": {}, "edges": []}']:
            self.canvas.write_text(invalid)
            self.assertNotEqual(self.add().returncode, 0)
            self.assertEqual(self.canvas.read_text(), invalid)

    def test_hook_checks_file_nodes_not_text_mentions(self):
        payload = json.dumps({'tool_input': {'file_path': str(self.scene)}})
        def check():
            return subprocess.run(['bash', str(SCRIPTS / 'canvas-sync-hook.sh')], input=payload, capture_output=True, text=True)
        self.assertIn('no file node', check().stdout)
        self.assertEqual(self.add().returncode, 0)
        self.assertEqual(check().stdout, '')


class Dnd5eApiQueryTest(unittest.TestCase):
    def test_network_responses_are_not_piped_into_interpreters(self):
        for name in ("dnd5eapi-query.sh", "open5e-query.sh"):
            with self.subTest(script=name):
                text = (SCRIPTS / name).read_text()
                self.assertNotRegex(text, r"curl[^\n]*\|\s*python")

    def test_query_is_passed_as_data_not_python_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sentinel = root / 'executed'
            fake_bin = root / 'bin'
            fake_bin.mkdir()
            fake_curl = fake_bin / 'curl'
            fake_curl.write_text(
                '#!/usr/bin/env python3\n'
                'import json, sys\n'
                'url = sys.argv[-1]\n'
                'if url.rstrip("/").count("/") > 5:\n'
                '    raise SystemExit(22)\n'
                'json.dump({"results": [{"name": "Goblin", "index": "goblin"}]}, sys.stdout)\n'
            )
            fake_curl.chmod(0o755)
            query = f"'; __import__('pathlib').Path({str(sentinel)!r}).write_text('owned'); q='"
            env = dict(os.environ, PATH=f"{fake_bin}:{os.environ['PATH']}")

            result = subprocess.run(
                ['bash', str(SCRIPTS / 'dnd5eapi-query.sh'), 'monsters', query],
                capture_output=True,
                text=True,
                env=env,
            )

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('No matches for', result.stdout)
            self.assertFalse(sentinel.exists(), result.stdout + result.stderr)


class EnvGuardTest(unittest.TestCase):
    def test_direct_symlink_nested_shell_and_allowed_template(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / '.env').write_text('SYNTHETIC=example')
            (root / 'alias.txt').symlink_to(root / '.env')
            cases = [('Read', {'file_path': '.env'}, True),
                     ('Read', {'file_path': 'alias.txt'}, True),
                     ('Bash', {'command': 'cat alias.txt'}, True),
                     ('Bash', {'command': "bash -c 'cat .env'"}, True),
                     ('Read', {'file_path': '.env.example'}, False),
                     ('Bash', {'command': 'cat README.md'}, False)]
            for name, inputs, denied in cases:
                with self.subTest(name=name, inputs=inputs):
                    result = subprocess.run([sys.executable, str(ROOT / 'plugins/env-guard/hooks/block-env.py')],
                        input=json.dumps({'tool_name': name, 'tool_input': inputs, 'cwd': d}), capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual('deny' in result.stdout, denied)


class GeminiCostTrackerTest(unittest.TestCase):
    def run_tracker(
        self,
        home: Path,
        session_id: str = 'session-a',
        max_generations: int = 2,
        *,
        payload=None,
        extra_env=None,
        script=None,
        settings_text=None,
        raw_input=None,
    ):
        settings = home / '.claude/gemini-images.local.md'
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(settings_text or f'---\nmax_generations: {max_generations}\n---\n')
        env = dict(os.environ, HOME=str(home), XDG_STATE_HOME=str(home / 'state'))
        env.update(extra_env or {})
        if payload is None:
            payload = {'session_id': session_id, 'cwd': str(home)}
        return subprocess.run(
            [sys.executable, str(script or GEMINI_HOOKS / 'cost_tracker.py')],
            input=raw_input if raw_input is not None else json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
        )

    def decision(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)['hookSpecificOutput']
        self.assertEqual(output['hookEventName'], 'PreToolUse')
        return output['permissionDecision']

    def test_counter_is_session_scoped_and_enforces_limit(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            first = self.run_tracker(home, 'session-a')
            second = self.run_tracker(home, 'session-a')
            blocked = self.run_tracker(home, 'session-a')
            other = self.run_tracker(home, 'session-b')

            self.assertEqual(self.decision(first), 'allow')
            self.assertIn('1 of 2', first.stdout)
            self.assertIn('2 of 2', second.stdout)
            self.assertEqual(self.decision(blocked), 'deny')
            self.assertIn('1 of 2', other.stdout)

    def test_counter_refuses_symlink_without_touching_target(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            first = self.run_tracker(home, 'session-a')
            self.assertEqual(first.returncode, 0, first.stderr)
            [counter] = (home / 'state/personal-plugins/gemini-images').glob('*.count')
            counter.unlink()
            victim = home / 'victim'
            victim.write_text('unchanged')
            counter.symlink_to(victim)

            result = self.run_tracker(home, 'session-a')

            self.assertEqual(self.decision(result), 'deny')
            self.assertEqual(victim.read_text(), 'unchanged')

    def test_counter_refuses_hard_link_and_corrupt_state(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            self.assertEqual(self.decision(self.run_tracker(home)), 'allow')
            [counter] = (home / 'state/personal-plugins/gemini-images').glob('*.count')

            counter.unlink()
            victim = home / 'victim'
            victim.write_text('0')
            os.link(victim, counter)
            self.assertEqual(self.decision(self.run_tracker(home)), 'deny')
            self.assertEqual(victim.read_text(), '0')

            counter.unlink()
            counter.write_bytes(b'\xff')
            self.assertEqual(self.decision(self.run_tracker(home)), 'deny')
            counter.write_text('9' * 5000)
            self.assertEqual(self.decision(self.run_tracker(home)), 'deny')

    def test_invalid_payload_and_body_settings_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            self.assertEqual(self.decision(self.run_tracker(home, payload=[])), 'deny')
            self.assertEqual(
                self.decision(self.run_tracker(home, payload={'session_id': 'x', 'cwd': []})),
                'deny',
            )
            self.assertEqual(
                self.decision(
                    self.run_tracker(
                        home,
                        payload={'session_id': [], 'cwd': str(home)},
                        extra_env={'CLAUDE_SESSION_ID': 'environment-session'},
                    )
                ),
                'deny',
            )
            nested = (
                '{"session_id":"x","cwd":'
                + json.dumps(str(home))
                + ',"nested":'
                + '[' * 20000
                + '0'
                + ']' * 20000
                + '}'
            )
            self.assertEqual(
                self.decision(self.run_tracker(home, raw_input=nested)),
                'deny',
            )
            self.assertEqual(
                self.decision(
                    self.run_tracker(
                        home,
                        payload={'session_id': 'x', 'cwd': str(home), 'padding': 'x' * 70000},
                    )
                ),
                'deny',
            )
            settings_text = '---\nmax_generations: 1\n---\nmax_generations: 999\n'
            self.assertEqual(self.decision(self.run_tracker(home, settings_text=settings_text)), 'allow')
            self.assertEqual(self.decision(self.run_tracker(home, settings_text=settings_text)), 'deny')

    def test_lock_contention_fails_closed_without_waiting(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            self.assertEqual(self.decision(self.run_tracker(home)), 'allow')
            [counter] = (home / 'state/personal-plugins/gemini-images').glob('*.count')
            with counter.open('r+') as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                result = self.run_tracker(home)
            self.assertEqual(self.decision(result), 'deny')

    def test_production_hook_timeout_is_ten_seconds(self):
        config = json.loads((GEMINI_HOOKS / 'hooks.json').read_text())
        hook = config['hooks']['PreToolUse'][0]['hooks'][0]
        self.assertEqual(hook['timeout'], 10)

    def test_compatibility_wrapper_handles_plugin_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            plugin = home / 'plugin with spaces'
            shutil.copytree(GEMINI_HOOKS, plugin / 'hooks')
            env = dict(
                os.environ,
                HOME=str(home),
                XDG_STATE_HOME=str(home / 'state'),
                CLAUDE_PLUGIN_ROOT=str(plugin),
            )
            result = subprocess.run(
                ['bash', str(plugin / 'hooks/cost-tracker.sh')],
                input=json.dumps({'session_id': 'session-a', 'cwd': str(home)}),
                capture_output=True,
                text=True,
                env=env,
                timeout=5,
            )
            self.assertEqual(self.decision(result), 'allow')
