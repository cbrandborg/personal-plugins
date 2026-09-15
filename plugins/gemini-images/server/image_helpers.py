"""Dependency-free helpers shared by the server and offline tests."""

import json
import re
import threading
from pathlib import Path

_VARIATION_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Supported models and approximate per-image cost
_SUPPORTED_MODELS = {
    "gemini-2.5-flash-image": 0.039,
    "gemini-3.1-flash-image-preview": 0.10,
    "gemini-3-pro-image-preview": 0.19,
}


class GenerationLimiter:
    """Reserve billable generation attempts under a process-session limit."""

    def __init__(self) -> None:
        self._attempt_count = 0
        self._session_maximum: int | None = None
        self._lock = threading.Lock()

    @property
    def attempt_count(self) -> int:
        with self._lock:
            return self._attempt_count

    def reserve(self, count: int, maximum: int) -> str | None:
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or count < 1
            or isinstance(maximum, bool)
            or not isinstance(maximum, int)
            or maximum < 1
            or count > maximum
        ):
            return "Generation count and max_generations must be positive integers within the limit."
        with self._lock:
            if self._session_maximum is None:
                self._session_maximum = maximum
            effective_maximum = self._session_maximum
            if count > effective_maximum or self._attempt_count + count > effective_maximum:
                return (
                    f"Generation limit reached: {self._attempt_count}/{effective_maximum} attempts used; "
                    f"request needs {count}."
                )
            self._attempt_count += count
        return None


def _validate_model(model: str) -> str | None:
    """Return an error JSON string if the model is not supported, else None."""
    if model not in _SUPPORTED_MODELS:
        return json.dumps({
            "error": f"Unknown model: {model}. Supported models: {', '.join(_SUPPORTED_MODELS)}",
        })
    return None

def _slugify(text: str) -> str:
    """Turn a short descriptive name into a filename slug.

    Example: 'Cozy Cabin Sunset' -> 'cozy-cabin-sunset'
    """
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9\s_-]", "", slug)
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


