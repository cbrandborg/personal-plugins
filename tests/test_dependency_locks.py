"""Dependency lock and reproducibility checks."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEMINI = ROOT / "plugins" / "gemini-images"


class DependencyLockTest(unittest.TestCase):
    def test_dev_dependencies_are_hash_locked_in_ci(self):
        lock = ROOT / "requirements-dev.lock"
        self.assertTrue(lock.is_file())
        text = lock.read_text()
        self.assertIn("--hash=sha256:", text)
        for workflow in ("ci.yml", "sync-skills.yml"):
            workflow_text = (ROOT / ".github" / "workflows" / workflow).read_text()
            self.assertIn(
                "pip install --require-hashes -r requirements-dev.lock",
                workflow_text,
            )
            self.assertIn("uv pip compile requirements-dev.txt", workflow_text)
            self.assertIn("cmp -s requirements-dev.lock", workflow_text)
            self.assertIn("uv lock --check --project plugins/gemini-images", workflow_text)

        readme = (ROOT / "README.md").read_text()
        testing = (ROOT / "docs" / "testing.md").read_text()
        self.assertIn("pip install --require-hashes -r requirements-dev.lock", readme)
        self.assertIn("pip install --require-hashes -r requirements-dev.lock", testing)

    def test_gemini_runtime_uses_committed_uv_lock(self):
        self.assertTrue((GEMINI / "uv.lock").is_file())
        ignored = (GEMINI / ".gitignore").read_text().splitlines()
        self.assertNotIn("uv.lock", ignored)
        config = json.loads((GEMINI / ".mcp.json").read_text())
        args = config["mcpServers"]["gemini-images"]["args"]
        self.assertIn("--locked", args)
        self.assertIn("uv run --locked", (GEMINI / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
