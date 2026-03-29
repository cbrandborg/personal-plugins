"""MCP server for generating and modifying images via Google Gemini."""

import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gemini-images")

# Session-level stats
_session_stats = {
    "generation_count": 0,
    "cost_estimate": 0.0,
    "last_model": None,
}

# Approximate per-image cost by model
_MODEL_COST = {
    "gemini-2.5-flash-image": 0.039,
    "gemini-3.1-flash-image-preview": 0.10,
    "gemini-3-pro-image-preview": 0.19,
}

# 1Password secret reference for the API key.
# Override with OP_GEMINI_API_KEY_REF env var if your vault/item differs.
_OP_DEFAULT_REF = "op://Vanir Labs/GEMINI_IMAGE_CLI_KEY/credential"

# Resolved API key, cached after first lookup
_api_key_cache: str | None = None


def _resolve_api_key() -> str:
    """Resolve the Gemini API key from multiple sources, in priority order:

    1. GEMINI_API_KEY env var (explicit override, always wins)
    2. 1Password CLI (`op read`) using a secret reference
    3. .env file in the plugin root

    The result is cached for the lifetime of the server process.
    """
    global _api_key_cache
    if _api_key_cache:
        return _api_key_cache

    # 1. Environment variable
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        _api_key_cache = key
        return key

    # 2. 1Password CLI
    op_ref = os.environ.get("OP_GEMINI_API_KEY_REF", _OP_DEFAULT_REF)
    try:
        result = subprocess.run(
            ["op", "read", op_ref],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            key = result.stdout.strip()
            _api_key_cache = key
            return key
        else:
            print(
                f"[gemini-images] 1Password lookup failed: {result.stderr.strip()}",
                file=sys.stderr,
            )
    except FileNotFoundError:
        print(
            "[gemini-images] 1Password CLI (op) not found, skipping.",
            file=sys.stderr,
        )
    except subprocess.TimeoutExpired:
        print(
            "[gemini-images] 1Password CLI timed out.",
            file=sys.stderr,
        )

    # 3. .env file in plugin root
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                key = line.split("=", 1)[1].strip().strip("\"'")
                if key:
                    _api_key_cache = key
                    return key

    raise RuntimeError(
        "GEMINI_API_KEY not found. Checked: env var, 1Password CLI "
        f"({op_ref}), .env file. Set one of these or run "
        "/gemini-images:settings for help."
    )


def _client() -> genai.Client:
    return genai.Client(api_key=_resolve_api_key())


def _save_images(response, output_dir: str) -> list[str]:
    """Extract images from a Gemini response and save to disk."""
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    saved = []
    ts = time.strftime("%Y%m%d_%H%M%S")

    for i, part in enumerate(response.candidates[0].content.parts):
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            ext = part.inline_data.mime_type.split("/")[-1]
            if ext == "jpeg":
                ext = "jpg"
            filename = f"gemini_{ts}_{i}.{ext}"
            filepath = out / filename
            filepath.write_bytes(base64.b64decode(part.inline_data.data))
            saved.append(str(filepath))

    return saved


def _track(model: str, count: int = 1) -> None:
    """Update session stats after a generation."""
    _session_stats["generation_count"] += count
    _session_stats["last_model"] = model
    cost = _MODEL_COST.get(model, 0.05) * count
    _session_stats["cost_estimate"] = round(
        _session_stats["cost_estimate"] + cost, 3
    )


@mcp.tool()
def generate_image(
    prompt: str,
    model: str = "gemini-2.5-flash-image",
    aspect_ratio: str = "1:1",
    output_dir: str = ".",
) -> str:
    """Generate an image from a text prompt using Gemini.

    Args:
        prompt: Detailed text description of the image to generate.
        model: Gemini model to use. Options: gemini-2.5-flash-image,
               gemini-3.1-flash-image-preview, gemini-3-pro-image-preview.
        aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3).
        output_dir: Directory to save the generated image.

    Returns:
        JSON with file paths, model used, and prompt.
    """
    try:
        client = _client()
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_generation_config=types.ImageGenerationConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
        )

        saved = _save_images(response, output_dir)
        if not saved:
            return json.dumps({"error": "No image returned by Gemini. The prompt may have been filtered."})

        _track(model, len(saved))

        # Extract any text response
        text_parts = [
            p.text for p in response.candidates[0].content.parts if p.text
        ]

        return json.dumps({
            "images": saved,
            "model": model,
            "prompt": prompt,
            "text": " ".join(text_parts) if text_parts else None,
            "session_generation_count": _session_stats["generation_count"],
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def modify_image(
    image_path: str,
    instruction: str,
    model: str = "gemini-2.5-flash-image",
    output_dir: str = ".",
) -> str:
    """Modify an existing image based on text instructions.

    Args:
        image_path: Path to the source image to modify.
        instruction: Text description of the desired modification.
        model: Gemini model to use.
        output_dir: Directory to save the modified image.

    Returns:
        JSON with output file path and details.
    """
    try:
        src = Path(image_path).expanduser().resolve()
        if not src.exists():
            return json.dumps({"error": f"Image not found: {src}"})

        # Determine MIME type
        suffix = src.suffix.lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
        mime_type = mime_map.get(suffix, "image/png")

        image_data = base64.b64encode(src.read_bytes()).decode("utf-8")

        client = _client()
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=image_data,
                    )
                ),
                types.Part(text=instruction),
            ],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        saved = _save_images(response, output_dir)
        if not saved:
            return json.dumps({"error": "No image returned. The modification may have been filtered."})

        _track(model, len(saved))

        text_parts = [
            p.text for p in response.candidates[0].content.parts if p.text
        ]

        return json.dumps({
            "images": saved,
            "source": str(src),
            "instruction": instruction,
            "model": model,
            "text": " ".join(text_parts) if text_parts else None,
            "session_generation_count": _session_stats["generation_count"],
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def generate_variations(
    prompt: str,
    count: int = 3,
    image_path: str | None = None,
    model: str = "gemini-2.5-flash-image",
    output_dir: str = ".",
) -> str:
    """Generate multiple variations of an image prompt or reference image.

    Args:
        prompt: Text description for the variations.
        count: Number of variations to generate (1-4).
        image_path: Optional reference image path to base variations on.
        model: Gemini model to use.
        output_dir: Directory to save generated images.

    Returns:
        JSON with all file paths and details.
    """
    try:
        count = max(1, min(4, count))
        client = _client()
        all_saved = []

        for i in range(count):
            # Vary the prompt slightly for diversity
            variation_prompt = prompt if i == 0 else f"{prompt} (variation {i + 1}, explore a different composition)"

            contents: list = []
            if image_path:
                src = Path(image_path).expanduser().resolve()
                if not src.exists():
                    return json.dumps({"error": f"Image not found: {src}"})
                suffix = src.suffix.lower()
                mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
                mime_type = mime_map.get(suffix, "image/png")
                image_data = base64.b64encode(src.read_bytes()).decode("utf-8")
                contents.append(
                    types.Part(
                        inline_data=types.Blob(mime_type=mime_type, data=image_data)
                    )
                )

            contents.append(types.Part(text=variation_prompt))

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_generation_config=types.ImageGenerationConfig(
                        aspect_ratio="1:1",
                    ),
                ),
            )

            saved = _save_images(response, output_dir)
            all_saved.extend(saved)

        _track(model, len(all_saved))

        return json.dumps({
            "images": all_saved,
            "count": len(all_saved),
            "prompt": prompt,
            "reference_image": image_path,
            "model": model,
            "session_generation_count": _session_stats["generation_count"],
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_generation_stats() -> str:
    """Get session generation statistics including count and estimated cost.

    Returns:
        JSON with generation count, cost estimate, and last model used.
    """
    return json.dumps(_session_stats)


if __name__ == "__main__":
    mcp.run()
