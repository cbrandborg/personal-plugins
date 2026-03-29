"""MCP server for generating and modifying images via Google Gemini."""

import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gemini-images")

# Default output structure
_DEFAULT_OUTPUT_DIR = "gemini-assets/outputs"
_DEFAULT_INPUT_DIR = "gemini-assets/inputs"

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

# Variation letters
_VARIATION_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


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
        "/image-settings for help."
    )


def _client() -> genai.Client:
    return genai.Client(api_key=_resolve_api_key())


def _slugify(text: str) -> str:
    """Turn a short descriptive name into a filename slug.

    Example: 'Cozy Cabin Sunset' -> 'cozy-cabin-sunset'
    """
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60] if slug else "image"


def _next_variation(output_dir: Path, slug: str) -> str:
    """Find the next available variation letter for a slug in output_dir.

    If cozy-cabin-sunset-A.png and cozy-cabin-sunset-B.png exist,
    returns 'C'.
    """
    existing = set()
    for f in output_dir.iterdir():
        match = re.match(rf"^{re.escape(slug)}-([A-Z])(?:-v\d+)?\.\w+$", f.name)
        if match:
            existing.add(match.group(1))

    for letter in _VARIATION_LETTERS:
        if letter not in existing:
            return letter
    return "Z"


def _next_sequence(output_dir: Path, slug: str, variation: str) -> int | None:
    """Find the next sequence number for an iteration on a specific variation.

    If cozy-cabin-sunset-A.png exists, returns 2 (for -v2).
    If cozy-cabin-sunset-A-v2.png exists, returns 3.
    Returns None if this is the first generation (no -vN suffix needed).
    """
    base_pattern = rf"^{re.escape(slug)}-{re.escape(variation)}(?:-v(\d+))?\.\w+$"
    max_seq = 0
    for f in output_dir.iterdir():
        match = re.match(base_pattern, f.name)
        if match:
            seq = int(match.group(1)) if match.group(1) else 1
            max_seq = max(max_seq, seq)

    return max_seq + 1 if max_seq > 0 else None


def _build_filename(slug: str, variation: str, sequence: int | None, ext: str) -> str:
    """Build a filename from components.

    Examples:
        cozy-cabin-sunset-A.png       (first generation)
        cozy-cabin-sunset-A-v2.png    (first iteration)
        cozy-cabin-sunset-B.png       (second variation)
    """
    if sequence and sequence > 1:
        return f"{slug}-{variation}-v{sequence}.{ext}"
    return f"{slug}-{variation}.{ext}"


def _save_images(
    response,
    output_dir: str,
    name: str,
    variation: str | None = None,
    is_iteration: bool = False,
) -> list[str]:
    """Extract images from a Gemini response and save with naming convention."""
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    slug = _slugify(name)
    saved = []

    for _i, part in enumerate(response.candidates[0].content.parts):
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            ext = part.inline_data.mime_type.split("/")[-1]
            if ext == "jpeg":
                ext = "jpg"

            if variation and is_iteration:
                seq = _next_sequence(out, slug, variation)
                filename = _build_filename(slug, variation, seq, ext)
            else:
                var = variation or _next_variation(out, slug)
                filename = _build_filename(slug, var, None, ext)

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
    name: str,
    model: str = "gemini-3.1-flash-image-preview",
    aspect_ratio: str = "1:1",
    output_dir: str = _DEFAULT_OUTPUT_DIR,
) -> str:
    """Generate an image from a text prompt using Gemini.

    Args:
        prompt: Detailed text description of the image to generate.
        name: Short descriptive name for the image (3-5 words, used in filename).
              Example: 'cozy cabin sunset' -> saves as cozy-cabin-sunset-A.png
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

        saved = _save_images(response, output_dir, name)
        if not saved:
            return json.dumps({"error": "No image returned by Gemini. The prompt may have been filtered."})

        _track(model, len(saved))

        text_parts = [
            p.text for p in response.candidates[0].content.parts if p.text
        ]

        return json.dumps({
            "images": saved,
            "model": model,
            "prompt": prompt,
            "name": name,
            "text": " ".join(text_parts) if text_parts else None,
            "session_generation_count": _session_stats["generation_count"],
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def modify_image(
    image_path: str,
    instruction: str,
    name: str | None = None,
    model: str = "gemini-3.1-flash-image-preview",
    output_dir: str = _DEFAULT_OUTPUT_DIR,
) -> str:
    """Modify an existing image based on text instructions.

    The output is saved as a new sequence version of the source image.
    For example, if the source is cozy-cabin-sunset-A.png, the modified
    version becomes cozy-cabin-sunset-A-v2.png.

    Args:
        image_path: Path to the source image to modify.
        instruction: Text description of the desired modification.
        name: Short descriptive name (auto-detected from source filename if omitted).
        model: Gemini model to use.
        output_dir: Directory to save the modified image.

    Returns:
        JSON with output file path and details.
    """
    try:
        src = Path(image_path).expanduser().resolve()
        if not src.exists():
            return json.dumps({"error": f"Image not found: {src}"})

        # Auto-detect name and variation from source filename
        detected_name = name
        detected_variation = None
        if not detected_name:
            match = re.match(r"^(.+)-([A-Z])(?:-v\d+)?$", src.stem)
            if match:
                detected_name = match.group(1)
                detected_variation = match.group(2)
            else:
                detected_name = src.stem

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

        saved = _save_images(
            response,
            output_dir,
            detected_name,
            variation=detected_variation,
            is_iteration=True,
        )
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
    name: str,
    count: int = 3,
    image_path: str | None = None,
    model: str = "gemini-3.1-flash-image-preview",
    aspect_ratio: str = "1:1",
    output_dir: str = _DEFAULT_OUTPUT_DIR,
) -> str:
    """Generate multiple variations of an image prompt or reference image.

    Each variation gets the next available letter (A, B, C, D...).

    Args:
        prompt: Text description for the variations.
        name: Short descriptive name for the images (3-5 words).
        count: Number of variations to generate (1-4).
        image_path: Optional reference image path to base variations on.
        model: Gemini model to use.
        aspect_ratio: Image aspect ratio.
        output_dir: Directory to save generated images.

    Returns:
        JSON with all file paths and details.
    """
    try:
        count = max(1, min(4, count))
        client = _client()
        all_saved = []

        for i in range(count):
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
                        aspect_ratio=aspect_ratio,
                    ),
                ),
            )

            saved = _save_images(response, output_dir, name)
            all_saved.extend(saved)

        _track(model, len(all_saved))

        return json.dumps({
            "images": all_saved,
            "count": len(all_saved),
            "prompt": prompt,
            "name": name,
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
