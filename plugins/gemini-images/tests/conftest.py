"""Shared fixtures for gemini-images tests."""

import subprocess
import sys

import pytest
from google import genai


@pytest.fixture(scope="session")
def api_key() -> str:
    """Resolve Gemini API key from 1Password. Skips if unavailable."""
    ref = "op://Vanir Labs/GEMINI_IMAGE_CLI_KEY/credential"
    try:
        result = subprocess.run(
            ["op", "read", ref], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    pytest.skip("1Password CLI not available or key not found")


@pytest.fixture(scope="session")
def client(api_key: str) -> genai.Client:
    """Authenticated Gemini client."""
    return genai.Client(api_key=api_key)
