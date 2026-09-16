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


def test_workflows_use_flash_lite_default_and_current_stable_models():
    paths = [
        PLUGIN_ROOT / "server" / "gemini_server.py",
        PLUGIN_ROOT / "commands" / "image-settings.md",
        PLUGIN_ROOT / "commands" / "generate-image.md",
        PLUGIN_ROOT / "skills" / "image-settings" / "SKILL.md",
        PLUGIN_ROOT / "skills" / "generate-image" / "SKILL.md",
        PLUGIN_ROOT / "skills" / "modify-image" / "SKILL.md",
    ]
    for path in paths:
        text = path.read_text()
        assert "gemini-3.1-flash-image-preview" not in text
        assert "gemini-3-pro-image-preview" not in text
        assert "gemini-2.5-flash-image" not in text
    assert 'model: str = "gemini-3.1-flash-lite-image"' in paths[0].read_text()
    assert "default_model: gemini-3.1-flash-lite-image" in paths[3].read_text()
