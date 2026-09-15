"""Static checks for safe image workflow guidance."""

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "relative_path",
    [
        "commands/generate-image.md",
        "commands/modify-image.md",
        "skills/generate-image/SKILL.md",
        "skills/modify-image/SKILL.md",
        "agents/variation-agent.md",
        "agents/iteration-agent.md",
    ],
)
def test_local_image_workflows_scope_uploads_to_confirmed_roots(relative_path):
    text = (PLUGIN_ROOT / relative_path).read_text()
    assert "current project root as `allowed_input_root` by default" in text
    assert "external root only after explicit user confirmation" in text


def test_variation_agent_passes_configured_max_generations():
    text = (PLUGIN_ROOT / "agents" / "variation-agent.md").read_text()
    assert "Pass the configured `max_generations`" in text
    assert "every `generate_image` and `generate_variations` call" in text
