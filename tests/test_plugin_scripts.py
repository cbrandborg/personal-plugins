"""Offline behavior checks for bundled scripts using synthetic vaults/files."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'plugins/dm-kit/scripts'


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
