"""Static safety checks for GitHub Actions workflows."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowSafetyTest(unittest.TestCase):
    def test_actions_are_pinned_to_full_commit_sha(self):
        uses_pattern = re.compile(r"^\s*-?\s*uses:\s*([^#\s]+)", re.MULTILINE)
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text()
            for action in uses_pattern.findall(text):
                with self.subTest(workflow=path.name, action=action):
                    self.assertRegex(action, r"^[^@]+@[0-9a-f]{40}$")

    def test_skill_sync_opens_reviewable_pull_request(self):
        text = (WORKFLOWS / "sync-skills.yml").read_text()
        self.assertIn('git status --porcelain --untracked-files=all', text)
        self.assertNotIn("git diff --quiet", text)
        self.assertIn("pull-requests: write", text)
        self.assertIn("ref: main", text)
        self.assertIn("refs/heads/automation/sync-skills", text)
        self.assertIn('gh pr list --state open --head "$branch" --base main', text)
        self.assertIn('gh pr edit "$pr_number"', text)
        self.assertIn("gh pr create", text)
        self.assertNotRegex(text, r"(?m)^\s*git push\s*$")
        self.assertNotRegex(text, r"(?m)^\s*git push\b[^\n]*(?:refs/heads/main|\bmain\b)")


if __name__ == "__main__":
    unittest.main()
