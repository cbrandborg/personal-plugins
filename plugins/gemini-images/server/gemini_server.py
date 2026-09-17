"""MCP server for generating and modifying images via Google Gemini."""

import base64
import io
import json
import os
import re
import stat
import subprocess
import sys
import warnings
from pathlib import Path

from PIL import Image as PIL_Image

from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gemini-images")

# Default output structure
_DEFAULT_OUTPUT_DIR = "gemini-assets/outputs"
_DEFAULT_INPUT_DIR = "gemini-assets/inputs"
_MAX_INPUT_IMAGE_BYTES = 10 * 1024 * 1024
_SUPPORTED_INPUT_MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
_OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd

# Session-level stats
_session_stats = {
    "generation_count": 0,
    "cost_estimate": 0.0,
    "last_model": None,
}

from image_helpers import (
    GenerationLimiter, _SUPPORTED_MODELS, _validate_model, _slugify,
    _next_variation, _next_sequence, _build_filename,
)

_generation_limiter = GenerationLimiter()

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
    op_ref = os.environ.get("OP_GEMINI_API_KEY_REF")
    if op_ref:
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


def _absolute_input_path(value: str, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{label} must be an absolute path.")
    return Path(os.path.normpath(os.fspath(path)))


def _directory_open_flags() -> int:
    required = ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    if any(not hasattr(os, name) for name in required) or not _OPEN_SUPPORTS_DIR_FD:
        raise RuntimeError(
            "Secure local image uploads are unavailable on this platform."
        )
    return (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | os.O_NONBLOCK
        | getattr(os, "O_CLOEXEC", 0)
    )


def _open_directory_no_follow(path: Path) -> int:
    """Open every directory component without following a symlink."""
    flags = _directory_open_flags()
    descriptor = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _load_allowed_input(
    image_path: str, allowed_input_root: str
) -> tuple[Path, bytes, str]:
    """Validate and descriptor-read an image within an approved local root."""
    root = _absolute_input_path(allowed_input_root, "allowed_input_root")
    source = _absolute_input_path(image_path, "image_path")
    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Image path is outside allowed_input_root: {source}") from exc

    try:
        directory_descriptor = _open_directory_no_follow(root)
    except OSError as exc:
        raise ValueError(
            "allowed_input_root must be a directory without symlink components."
        ) from exc
    if not relative.parts:
        os.close(directory_descriptor)
        raise ValueError("Input image path must identify a regular file.")

    try:
        directory_flags = _directory_open_flags()
        for component in relative.parts[:-1]:
            try:
                next_descriptor = os.open(
                    component, directory_flags, dir_fd=directory_descriptor
                )
            except OSError as exc:
                raise ValueError(
                    "Image paths may not contain symlink or non-directory components."
                ) from exc
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor

        file_flags = (
            os.O_RDONLY
            | os.O_NOFOLLOW
            | os.O_NONBLOCK
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            file_descriptor = os.open(
                relative.parts[-1], file_flags, dir_fd=directory_descriptor
            )
        except OSError as exc:
            raise ValueError(
                "Input image must be a regular file and may not be a symlink."
            ) from exc
        with os.fdopen(file_descriptor, "rb") as image_file:
            file_stat = os.fstat(image_file.fileno())
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                raise ValueError(
                    "Input image path must identify a regular file with one link."
                )
            if file_stat.st_size > _MAX_INPUT_IMAGE_BYTES:
                raise ValueError("Input image exceeds the 10 MiB upload limit.")
            image_data = image_file.read(_MAX_INPUT_IMAGE_BYTES + 1)
    finally:
        os.close(directory_descriptor)

    if len(image_data) > _MAX_INPUT_IMAGE_BYTES:
        raise ValueError("Input image exceeds the 10 MiB upload limit.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", PIL_Image.DecompressionBombWarning)
            with PIL_Image.open(io.BytesIO(image_data)) as image:
                image_format = image.format
                image.verify()
            mime_type = _SUPPORTED_INPUT_MIME_TYPES.get(image_format or "")
            if mime_type is None:
                raise ValueError("unsupported image format")
            with PIL_Image.open(io.BytesIO(image_data)) as image:
                image.load()
    except Exception as exc:
        raise ValueError("Input must be a valid supported image (PNG, JPEG, or WebP).") from exc
    return source, image_data, mime_type


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

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            if variation and is_iteration:
                seq = _next_sequence(out, slug, variation)
                filename = _build_filename(slug, variation, seq, "png")
            else:
                var = variation or _next_variation(out, slug)
                filename = _build_filename(slug, var, None, "png")

            filepath = out / filename
            pil_image = PIL_Image.open(io.BytesIO(part.inline_data.data))
            pil_image.save(str(filepath), format="PNG")
            saved.append(str(filepath))

    return saved


def _track(model: str, count: int = 1) -> None:
    """Update session stats after a generation."""
    _session_stats["generation_count"] += count
    _session_stats["last_model"] = model
    cost = _SUPPORTED_MODELS.get(model, 0.05) * count
    _session_stats["cost_estimate"] = round(
        _session_stats["cost_estimate"] + cost, 3
    )


@mcp.tool()
def generate_image(
    prompt: str,
    name: str,
    model: str = "gemini-3.1-flash-lite-image",
    aspect_ratio: str = "1:1",
    reference_image_path: str | None = None,
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    max_generations: int = 5,
    allowed_input_root: str | None = None,
) -> str:
    """Generate an image from a text prompt using Gemini.

    Args:
        prompt: Detailed text description of the image to generate.
        name: Short descriptive name for the image (3-5 words, used in filename).
              Example: 'cozy cabin sunset' -> saves as cozy-cabin-sunset-A.png
        model: Gemini model to use. Options: gemini-3.1-flash-lite-image,
               gemini-3.1-flash-image, gemini-3-pro-image.
        aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3).
        reference_image_path: Optional path to a reference image for style/composition guidance.
        output_dir: Directory to save the generated image.
        max_generations: Maximum billable generation attempts for this server session.
        allowed_input_root: Required root boundary when reference_image_path is used.

    Returns:
        JSON with file paths, model used, and prompt.
    """
    try:
        if err := _validate_model(model):
            return err

        contents: list = []
        if reference_image_path:
            if not allowed_input_root:
                return json.dumps({"error": "allowed_input_root is required for local image uploads."})
            _ref, raw_image_data, mime_type = _load_allowed_input(
                reference_image_path, allowed_input_root
            )
            image_data = base64.b64encode(raw_image_data).decode("utf-8")
            contents.append(
                types.Part(
                    inline_data=types.Blob(mime_type=mime_type, data=image_data)
                )
            )
        contents.append(types.Part(text=prompt))

        if limit_error := _generation_limiter.reserve(1, max_generations):
            return json.dumps({"error": limit_error})

        client = _client()
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
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
    model: str = "gemini-3.1-flash-lite-image",
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    max_generations: int = 5,
    allowed_input_root: str | None = None,
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
        max_generations: Maximum billable generation attempts for this server session.
        allowed_input_root: Required root boundary for the local source image.

    Returns:
        JSON with output file path and details.
    """
    try:
        if err := _validate_model(model):
            return err
        if not allowed_input_root:
            return json.dumps({"error": "allowed_input_root is required for local image uploads."})
        src, raw_image_data, mime_type = _load_allowed_input(
            image_path, allowed_input_root
        )

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

        image_data = base64.b64encode(raw_image_data).decode("utf-8")

        if limit_error := _generation_limiter.reserve(1, max_generations):
            return json.dumps({"error": limit_error})
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
    model: str = "gemini-3.1-flash-lite-image",
    aspect_ratio: str = "1:1",
    output_dir: str = _DEFAULT_OUTPUT_DIR,
    max_generations: int = 5,
    allowed_input_root: str | None = None,
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
        max_generations: Maximum billable generation attempts for this server session.
        allowed_input_root: Required root boundary when image_path is used.

    Returns:
        JSON with all file paths and details.
    """
    try:
        if err := _validate_model(model):
            return err
        count = max(1, min(4, count))
        source_image = None
        source_image_data = None
        source_mime_type = None
        if image_path:
            if not allowed_input_root:
                return json.dumps({"error": "allowed_input_root is required for local image uploads."})
            source_image, raw_image_data, source_mime_type = _load_allowed_input(
                image_path, allowed_input_root
            )
            source_image_data = base64.b64encode(raw_image_data).decode("utf-8")
        if limit_error := _generation_limiter.reserve(count, max_generations):
            return json.dumps({"error": limit_error})
        client = _client()
        all_saved = []

        for i in range(count):
            variation_prompt = prompt if i == 0 else f"{prompt} (variation {i + 1}, explore a different composition)"

            contents: list = []
            if source_image is not None:
                contents.append(
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=source_mime_type,
                            data=source_image_data,
                        )
                    )
                )

            contents.append(types.Part(text=variation_prompt))

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(
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
    return json.dumps(
        {**_session_stats, "generation_attempt_count": _generation_limiter.attempt_count}
    )


if __name__ == "__main__":
    mcp.run()
