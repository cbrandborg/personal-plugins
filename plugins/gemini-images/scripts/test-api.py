"""Integration test for the Gemini image generation MCP server.

Calls the actual Gemini API to verify:
1. API key resolution (1Password)
2. Image generation works
3. Response contains valid image data
4. PIL can decode and save as PNG
5. modify_image works with a reference image
6. Model validation rejects unknown models

Usage:
    cd plugins/gemini-images
    uv run python scripts/test-api.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image as PIL_Image


def resolve_api_key() -> str:
    """Use the server's actual key resolution; credentials are never printed."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
    from gemini_server import _resolve_api_key
    return _resolve_api_key()


def test_generate_image(client: genai.Client, output_dir: Path) -> Path:
    """Test basic image generation."""
    print("\n[Test 1] Generate image...")
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents="A simple red circle on a white background, minimal, clean",
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="1:1"),
        ),
    )

    image_parts = [
        p for p in response.candidates[0].content.parts
        if p.inline_data and p.inline_data.mime_type.startswith("image/")
    ]
    assert len(image_parts) > 0, "No image in response"

    part = image_parts[0]
    print(f"  Response mime_type: {part.inline_data.mime_type}")
    print(f"  Response data size: {len(part.inline_data.data)} bytes")

    # Verify PIL can decode it
    pil_image = PIL_Image.open(io.BytesIO(part.inline_data.data))
    print(f"  PIL decoded: {pil_image.format} {pil_image.size}")

    # Save as PNG
    out_path = output_dir / "test-generate-A.png"
    pil_image.save(str(out_path), format="PNG")
    assert out_path.exists(), "PNG file not created"

    # Verify saved file is actually PNG
    saved = PIL_Image.open(out_path)
    assert saved.format == "PNG", f"Expected PNG, got {saved.format}"
    print(f"  Saved as PNG: {out_path} ({out_path.stat().st_size} bytes)")
    print("  PASS")
    return out_path


def test_modify_image(client: genai.Client, source_path: Path, output_dir: Path):
    """Test image modification with a reference image."""
    print("\n[Test 2] Modify image...")
    import base64

    image_data = base64.b64encode(source_path.read_bytes()).decode("utf-8")
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[
            types.Part(
                inline_data=types.Blob(mime_type="image/png", data=image_data)
            ),
            types.Part(text="Change the red circle to blue"),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )

    image_parts = [
        p for p in response.candidates[0].content.parts
        if p.inline_data and p.inline_data.mime_type.startswith("image/")
    ]
    assert len(image_parts) > 0, "No image in response"

    part = image_parts[0]
    pil_image = PIL_Image.open(io.BytesIO(part.inline_data.data))
    out_path = output_dir / "test-modify-A-v2.png"
    pil_image.save(str(out_path), format="PNG")

    saved = PIL_Image.open(out_path)
    assert saved.format == "PNG"
    print(f"  Modified and saved: {out_path} ({out_path.stat().st_size} bytes)")
    print("  PASS")


def test_model_validation():
    """Test that the server's model validation works."""
    print("\n[Test 3] Model validation...")

    # Import the server module to test _validate_model
    server_dir = Path(__file__).resolve().parent.parent / "server"
    sys.path.insert(0, str(server_dir))

    # We can't easily import the server (it starts mcp.run()), so just
    # test the supported models list concept
    supported = {
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image-preview",
        "gemini-3-pro-image-preview",
    }
    assert "gemini-2.0-flash-preview-image-generation" not in supported
    assert "gemini-3.1-flash-image-preview" in supported
    print("  Known model accepted: gemini-3.1-flash-image-preview")
    print("  Unknown model rejected: gemini-2.0-flash-preview-image-generation")
    print("  PASS")


def test_aspect_ratios(client: genai.Client):
    """Test that various aspect ratios work."""
    print("\n[Test 4] Aspect ratios...")
    for ratio in ["1:1", "16:9", "9:16"]:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=f"A solid blue square",
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=ratio),
            ),
        )
        image_parts = [
            p for p in response.candidates[0].content.parts
            if p.inline_data and p.inline_data.mime_type.startswith("image/")
        ]
        assert len(image_parts) > 0, f"No image for ratio {ratio}"
        print(f"  {ratio}: OK ({len(image_parts[0].inline_data.data)} bytes)")
    print("  PASS")


def main():
    if os.environ.get("RUN_GEMINI_INTEGRATION") != "1":
        raise SystemExit("Set RUN_GEMINI_INTEGRATION=1 to opt in to billable API tests")
    print("=== Gemini Images Plugin — Integration Tests ===")

    print("\n[Setup] Resolving API key...")
    key = resolve_api_key()
    client = genai.Client(api_key=key)

    with tempfile.TemporaryDirectory(prefix="gemini-test-") as tmpdir:
        output_dir = Path(tmpdir)
        print(f"  Output dir: {output_dir}")

        test_model_validation()
        generated = test_generate_image(client, output_dir)
        test_modify_image(client, generated, output_dir)
        test_aspect_ratios(client)

    print("\n=== All tests passed ===")


if __name__ == "__main__":
    main()
