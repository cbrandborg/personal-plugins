"""Regression checks for scene-to-canvas workflow paths."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "scripts" / "add-scene-to-canvas.py"
SKILLS = PLUGIN_ROOT / "skills"


class SceneCanvasPathTest(unittest.TestCase):
    def test_scaffold_workflows_pass_paths_relative_to_detected_vault(self):
        expectations = {
            "scaffold-scene": "Chapters/<NN - Chapter>/Scenes/<NN - Title>.md",
            "scaffold-chapter": "Chapters/<NN - Name>/Scenes/01 - Arrival.md",
        }

        for skill, relative_scene in expectations.items():
            with self.subTest(skill=skill):
                text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f'  "{relative_scene}"', text)
                self.assertIn('  --vault-root "$VAULT"', text)
                self.assertNotIn('"DnD/<campaign-name>/Chapters/', text)

    def test_helper_accepts_campaign_relative_path_with_explicit_vault_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            chapter = root / "Chapters/09 - Refugee Camp"
            scene = chapter / "Scenes/01 - Arrival.md"
            scene.parent.mkdir(parents=True)
            scene.write_text("Scene", encoding="utf-8")
            canvas = chapter / "Refugee Camp.canvas"
            canvas.write_text('{"nodes": [], "edges": []}', encoding="utf-8")
            relative_scene = scene.relative_to(root).as_posix()

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(canvas),
                    relative_scene,
                    "--vault-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(canvas.read_text(encoding="utf-8"))
            self.assertEqual(data["nodes"][0]["file"], relative_scene)


if __name__ == "__main__":
    unittest.main()
