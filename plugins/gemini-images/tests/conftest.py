"""Shared fixtures for gemini-images tests."""

import os
import subprocess
import sys

import pytest


@pytest.fixture(scope="session")
def api_key() -> str:
    """Resolve Gemini API key from 1Password. Skips if unavailable."""
    if os.environ.get("RUN_GEMINI_INTEGRATION") != "1":
        pytest.skip("Set RUN_GEMINI_INTEGRATION=1 to opt in to billable API tests")
    if key := os.environ.get("GEMINI_API_KEY"):
        return key
    ref = os.environ.get("OP_GEMINI_API_KEY_REF")
    if not ref:
        pytest.skip("Set GEMINI_API_KEY or OP_GEMINI_API_KEY_REF")
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
def client(api_key: str):
    """Authenticated Gemini client."""
    from google import genai
    return genai.Client(api_key=api_key)
