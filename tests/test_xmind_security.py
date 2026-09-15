"""Security checks for XMind ZIP extraction."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import tempfile
import unittest
from unittest import mock
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "xmind-campaign" / "scripts" / "extract_xmind.py"
SPEC = importlib.util.spec_from_file_location("extract_xmind", SCRIPT)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class XMindArchiveSecurityTest(unittest.TestCase):
    def make_archive(self, root: Path, members: dict[str, bytes]) -> Path:
        archive = root / "sample.xmind"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
            for name, content in members.items():
                handle.writestr(name, content)
        return archive

    def minimal_content(self) -> bytes:
        return json.dumps([{"title": "Sheet", "rootTopic": {"title": "Root"}}]).encode()

    def test_valid_content_and_resource_extract(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = self.make_archive(
                root,
                {"content.json": self.minimal_content(), "resources/image.png": b"image"},
            )
            output = root / "output"

            MODULE.safe_extract_archive(archive, output)

            self.assertEqual((output / "content.json").read_bytes(), self.minimal_content())
            self.assertEqual((output / "resources/image.png").read_bytes(), b"image")

    def test_rejects_traversal_and_archive_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            traversal = self.make_archive(
                root,
                {"content.json": self.minimal_content(), "../outside": b"owned"},
            )
            with self.assertRaises(ValueError):
                MODULE.safe_extract_archive(traversal, root / "traversal-output")
            self.assertFalse((root / "outside").exists())

            symlink = root / "symlink.xmind"
            with zipfile.ZipFile(symlink, "w") as handle:
                handle.writestr("content.json", self.minimal_content())
                entry = zipfile.ZipInfo("resources/link")
                entry.create_system = 3
                entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                handle.writestr(entry, "../../outside")
            with self.assertRaises(ValueError):
                MODULE.safe_extract_archive(symlink, root / "symlink-output")

    def test_rejects_member_and_total_size_limits(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = self.make_archive(
                root,
                {"content.json": self.minimal_content(), "resources/large": b"123456789"},
            )
            original_member = MODULE.MAX_MEMBER_BYTES
            original_total = MODULE.MAX_TOTAL_BYTES
            try:
                setattr(MODULE, "MAX_MEMBER_BYTES", 8)
                with self.assertRaises(ValueError):
                    MODULE.safe_extract_archive(archive, root / "member-output")
                setattr(MODULE, "MAX_MEMBER_BYTES", 20)
                setattr(MODULE, "MAX_TOTAL_BYTES", len(self.minimal_content()) + 8)
                with self.assertRaises(ValueError):
                    MODULE.safe_extract_archive(archive, root / "total-output")
            finally:
                setattr(MODULE, "MAX_MEMBER_BYTES", original_member)
                setattr(MODULE, "MAX_TOTAL_BYTES", original_total)

    def test_replaces_output_without_following_existing_hard_links(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = self.make_archive(root, {"content.json": self.minimal_content()})
            output = root / "output"
            output.mkdir()
            victim = root / "victim"
            victim.write_bytes(b"SAFE")
            os.link(victim, output / "content.json")

            MODULE.safe_extract_archive(archive, output)

            self.assertEqual(victim.read_bytes(), b"SAFE")
            self.assertEqual((output / "content.json").read_bytes(), self.minimal_content())

    def test_collision_failure_leaves_existing_output_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = self.make_archive(
                root,
                {"content.json": self.minimal_content(), "node": b"file", "node/child": b"child"},
            )
            output = root / "output"
            output.mkdir()
            (output / "marker").write_text("preserved")

            with self.assertRaises(ValueError):
                MODULE.safe_extract_archive(archive, output)

            self.assertEqual((output / "marker").read_text(), "preserved")
            self.assertFalse((output / "node").exists())

    def test_rejects_portable_name_collisions_and_windows_unsafe_names(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for index, members in enumerate(
                (
                    {"content.json": self.minimal_content(), "resources/A": b"1", "resources/a": b"2"},
                    {"content.json": self.minimal_content(), "resources/image:stream": b"1"},
                    {"content.json": self.minimal_content(), "resources/CON.txt": b"1"},
                    {"content.json": self.minimal_content(), "resources/name. ": b"1"},
                )
            ):
                with self.subTest(index=index):
                    archive = self.make_archive(root, members)
                    with self.assertRaises(ValueError):
                        MODULE.safe_extract_archive(archive, root / f"output-{index}")

    def test_failed_commit_restores_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = self.make_archive(root, {"content.json": self.minimal_content()})
            output = root / "output"
            output.mkdir()
            (output / "marker").write_text("preserved")
            real_replace = os.replace
            calls = 0

            def fail_final_swap(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("synthetic final swap failure")
                return real_replace(source, destination)

            with mock.patch.object(MODULE.os, "replace", side_effect=fail_final_swap):
                with self.assertRaises(OSError):
                    MODULE.safe_extract_archive(archive, output)

            self.assertEqual((output / "marker").read_text(), "preserved")
            self.assertEqual(list(root.glob(".output.backup-*")), [])

    def test_failed_rollback_preserves_backup_for_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = self.make_archive(root, {"content.json": self.minimal_content()})
            output = root / "output"
            output.mkdir()
            (output / "marker").write_text("recover me")
            real_replace = os.replace
            calls = 0

            def fail_commit_and_rollback(source, destination):
                nonlocal calls
                calls += 1
                if calls in {2, 3}:
                    raise OSError(f"synthetic replace failure {calls}")
                return real_replace(source, destination)

            with mock.patch.object(MODULE.os, "replace", side_effect=fail_commit_and_rollback):
                with self.assertRaisesRegex(RuntimeError, "backup preserved at"):
                    MODULE.safe_extract_archive(archive, output)

            [backup] = root.glob(".output.backup-*")
            self.assertEqual((backup / "marker").read_text(), "recover me")


if __name__ == "__main__":
    unittest.main()
