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

    def test_ci_runs_real_hermes_validation_and_security_scans(self):
        text = (WORKFLOWS / "ci.yml").read_text()
        self.assertIn(
            "git -C /tmp/hermes-agent fetch --depth 1 origin "
            "939e45c91d751fadd94dcd1b873ac3cb44846213",
            text,
        )
        self.assertIn("uv sync --locked --project /tmp/hermes-agent --no-dev", text)
        self.assertIn("hermes plugins doctor", text)
        self.assertIn("pytest plugins/gemini-images/tests -m 'not integration'", text)
        self.assertIn("unittest discover -s plugins/dm-kit/tests", text)
        self.assertIn(
            "gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7",
            text,
        )
        self.assertIn("pull-requests: read", text)
        self.assertIn('GITLEAKS_ENABLE_COMMENTS: "false"', text)
        self.assertIn(
            "github/codeql-action/init@faaca9a8f6edddba5725ffe5adefdab6669a2eca",
            text,
        )
        self.assertIn(
            "github/codeql-action/analyze@faaca9a8f6edddba5725ffe5adefdab6669a2eca",
            text,
        )
        self.assertIn("codeql:", text)
        self.assertIn("if: github.event.repository.private == false", text)

    def test_local_ci_runs_hermes_and_locked_gemini_checks(self):
        text = (ROOT / "justfile").read_text()
        self.assertIn("hermes plugins doctor", text)
        self.assertIn("uv run --locked --project plugins/gemini-images", text)
        self.assertIn("pytest plugins/gemini-images/tests -m 'not integration'", text)
        self.assertIn("unittest discover -s plugins/dm-kit/tests", text)


if __name__ == "__main__":
    unittest.main()
