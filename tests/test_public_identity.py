"""Public marketplace identity regressions."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_OWNER = "Christian Brandborg"


class PublicIdentityTest(unittest.TestCase):
    def test_claude_marketplace_uses_personal_identity(self):
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text()
        )
        self.assertEqual(marketplace["owner"], {"name": PUBLIC_OWNER})
        for plugin in marketplace["plugins"]:
            with self.subTest(plugin=plugin["name"]):
                self.assertEqual(plugin["author"], {"name": PUBLIC_OWNER})


if __name__ == "__main__":
    unittest.main()
