"""Exercise failed imports and conflicts against isolated repository state."""
import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_skill_sync import skills, write_json, write_skill


class ImportTransactionsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plugins = self.root / 'plugins'
        self.upstream = self.root / 'upstream'
        self.lock = self.root / 'lock.json'
        self.sources = self.root / 'sources.json'
        self.claude = self.root / 'claude.json'
        self.codex = self.root / 'codex.json'
        self.source = dict(id='example', plugin='bundle', path='skills', git='unused', ref='main')
        self.target = self.plugins / 'bundle' / 'skills'
        old = {}
        for name in ['a', 'b']:
            write_skill(self.target / name, name, 'old')
            write_skill(self.upstream / name, name, 'new')
            old[name] = dict(content_sha256=skills.tree_digest(self.target / name), commit='old')
        write_json(self.lock, {'sources': {'example': {'skills': old}}})
        write_json(self.sources, {'sources': [self.source]})
        for path in [self.claude, self.codex]:
            write_json(path, {'plugins': [{'name': 'bundle'}]})
        for provider in ['.claude-plugin', '.codex-plugin']:
            write_json(self.plugins / 'bundle' / provider / 'plugin.json', {'name': 'bundle', 'version': '1.0.0'})
        write_skill(self.target / 'b', 'b', 'local edit')
        self.addCleanup(patch.stopall)
        patch.multiple(skills, ROOT=self.root, PLUGINS=self.plugins, LOCK=self.lock,
            SOURCES=self.sources, CLAUDE_MARKETPLACE=self.claude, CODEX_MARKETPLACE=self.codex).start()
        patch.object(skills, 'clone_source', return_value=(self.upstream, 'new')).start()

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_later_leaf_conflict_leaves_entire_source_unchanged(self):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'both changed'):
            skills.sync_source(self.source, apply=True)
        self.assertEqual(before, self.snapshot())

    def test_conflict_check_fails_without_claiming_no_changes(self):
        write_skill(self.upstream / 'a', 'a', 'old')
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch.object(skills.sys, 'argv', ['skills.py', 'sync', '--check']):
            self.assertEqual(skills.main(), 1)
        self.assertNotIn('No upstream skill content changed', output.getvalue())

    def test_later_source_failure_rolls_back_earlier_source(self):
        write_skill(self.target / 'b', 'b', 'old')
        write_json(self.sources, {'sources': [self.source, {**self.source, 'id': 'broken'}]})
        before = self.snapshot()
        with patch.object(skills, 'clone_source', side_effect=[(self.upstream, 'new'), ValueError('fetch failed')]):
            with self.assertRaisesRegex(ValueError, 'fetch failed'):
                skills.sync(argparse.Namespace(apply=True))
        self.assertEqual(before, self.snapshot())

    def test_failed_add_leaves_no_registration_or_manifest(self):
        before = self.snapshot()
        args = argparse.Namespace(plugin='new-bundle', id=None, source='owner/repo',
            path='missing', ref='main', category='Productivity', description=None)
        with patch.object(skills, 'clone_source', side_effect=ValueError('missing path')):
            with self.assertRaisesRegex(ValueError, 'missing path'):
                skills.add(args)
        self.assertEqual(before, self.snapshot())

    def test_success_commits_payload_lock_and_version_together(self):
        write_skill(self.target / 'b', 'b', 'old')
        self.assertEqual(skills.sync(argparse.Namespace(apply=True)), 0)
        self.assertIn('new', (self.target / 'a' / 'SKILL.md').read_text())
        self.assertEqual(json.loads(self.lock.read_text())['sources']['example']['skills']['a']['commit'], 'new')
        for provider in ['.claude-plugin', '.codex-plugin']:
            self.assertEqual(json.loads((self.plugins / 'bundle' / provider / 'plugin.json').read_text())['version'], '1.0.1')

    def test_validation_failure_rolls_back(self):
        write_skill(self.target / 'b', 'b', 'old')
        before = self.snapshot()
        with patch.object(skills, 'validate', return_value=1):
            with self.assertRaisesRegex(ValueError, 'validation failed'):
                skills.sync(argparse.Namespace(apply=True))
        self.assertEqual(before, self.snapshot())

    def test_commit_io_failure_restores_original_files(self):
        write_skill(self.target / 'b', 'b', 'old')
        before = self.snapshot()
        original_copy = skills.shutil.copy2
        failed = False
        def fail_lock_once(source, destination, *args, **kwargs):
            nonlocal failed
            if Path(destination) == self.lock and not failed:
                failed = True
                raise OSError('simulated disk write failure')
            return original_copy(source, destination, *args, **kwargs)
        with patch.object(skills.shutil, 'copy2', side_effect=fail_lock_once):
            with self.assertRaisesRegex(OSError, 'simulated disk write failure'):
                skills.sync(argparse.Namespace(apply=True))
        self.assertTrue(failed)
        self.assertEqual(before, self.snapshot())
