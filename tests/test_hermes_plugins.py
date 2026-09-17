"""End-to-end validation against the installed Hermes plugin runtime."""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAMES = (
    "dm-kit",
    "env-guard",
    "gemini-images",
    "mattpocock-productivity",
    "xmind-campaign",
)


@unittest.skipUnless(shutil.which("hermes"), "Hermes CLI is required")
class HermesPluginValidationTest(unittest.TestCase):
    def test_every_bundle_passes_real_hermes_validation(self):
        for name in PLUGIN_NAMES:
            with self.subTest(plugin=name):
                result = subprocess.run(
                    ["hermes", "plugins", "doctor", str(ROOT / "plugins" / name), "--ci"],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("WARN:", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
