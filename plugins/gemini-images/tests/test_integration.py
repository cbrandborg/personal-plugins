"""Integration tests that hit the real Gemini API.

Run with:   uv run pytest tests/test_integration.py
Skip with:  uv run pytest -m "not integration"
"""

import base64
import io

import pytest
from google.genai import types
from PIL import Image as PIL_Image

pytestmark = pytest.mark.integration


class TestGenerateImage:
    def test_basic_generation(self, client):
        """Generate an image and verify we get valid image data back."""
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents="A simple red circle on a white background",
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
        assert len(image_parts[0].inline_data.data) > 10_000, "Image suspiciously small"

    def test_pil_can_decode_response(self, client):
        """Verify PIL can open the image data from the API."""
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents="A solid blue square",
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="1:1"),
            ),
        )

        part = next(
            p for p in response.candidates[0].content.parts
            if p.inline_data and p.inline_data.mime_type.startswith("image/")
        )

        pil_image = PIL_Image.open(io.BytesIO(part.inline_data.data))
        assert pil_image.size[0] > 0
        assert pil_image.size[1] > 0

    def test_save_as_png(self, client, tmp_path):
        """Verify we can save the response as a real PNG file."""
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents="A green triangle on white background",
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="1:1"),
            ),
        )

        part = next(
            p for p in response.candidates[0].content.parts
            if p.inline_data and p.inline_data.mime_type.startswith("image/")
        )

        out = tmp_path / "test.png"
        pil_image = PIL_Image.open(io.BytesIO(part.inline_data.data))
        pil_image.save(str(out), format="PNG")

        assert out.exists()
        assert out.stat().st_size > 10_000

        saved = PIL_Image.open(out)
        assert saved.format == "PNG"


class TestModifyImage:
    def test_modify_with_reference(self, client, tmp_path):
        """Generate an image, then modify it."""
        # First generate
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents="A red circle on white background",
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="1:1"),
            ),
        )

        part = next(
            p for p in response.candidates[0].content.parts
            if p.inline_data and p.inline_data.mime_type.startswith("image/")
        )

        # Save source
        source = tmp_path / "source.png"
        pil_image = PIL_Image.open(io.BytesIO(part.inline_data.data))
        pil_image.save(str(source), format="PNG")

        # Now modify
        image_data = base64.b64encode(source.read_bytes()).decode("utf-8")
        mod_response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[
                types.Part(
                    inline_data=types.Blob(mime_type="image/png", data=image_data)
                ),
                types.Part(text="Change the circle color to blue"),
            ],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        mod_parts = [
            p for p in mod_response.candidates[0].content.parts
            if p.inline_data and p.inline_data.mime_type.startswith("image/")
        ]
        assert len(mod_parts) > 0, "No image in modify response"


class TestAspectRatios:
    @pytest.mark.parametrize("ratio", ["1:1", "16:9", "9:16", "4:3", "3:2"])
    def test_aspect_ratio(self, client, ratio):
        """Verify various aspect ratios produce images."""
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents="A solid blue rectangle",
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


class TestModels:
    @pytest.mark.parametrize("model", [
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image-preview",
    ])
    def test_supported_model_generates(self, client, model):
        """Verify each supported model can generate an image."""
        response = client.models.generate_content(
            model=model,
            contents="A small orange dot",
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="1:1"),
            ),
        )

        image_parts = [
            p for p in response.candidates[0].content.parts
            if p.inline_data and p.inline_data.mime_type.startswith("image/")
        ]
        assert len(image_parts) > 0, f"No image from {model}"
