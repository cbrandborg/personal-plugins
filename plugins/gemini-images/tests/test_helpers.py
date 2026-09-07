"""Unit tests for server helper functions. No API calls."""

import sys
from pathlib import Path

# Add server dir to path so we can import helpers
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server"))

from image_helpers import (
    _slugify, _next_variation, _next_sequence, _build_filename, _validate_model,
)


# ── slugify ──────────────────────────────────────────────


class TestSlugify:
    def test_basic(self):
        assert _slugify("Cozy Cabin Sunset") == "cozy-cabin-sunset"

    def test_special_chars(self):
        assert _slugify("Hello! World? #1") == "hello-world-1"

    def test_underscores(self):
        assert _slugify("product_shot_hero") == "product-shot-hero"

    def test_extra_spaces(self):
        assert _slugify("  lots   of   spaces  ") == "lots-of-spaces"

    def test_empty(self):
        assert _slugify("") == "image"
        assert _slugify("!!!") == "image"

    def test_truncation(self):
        long = "a " * 100
        assert len(_slugify(long)) <= 60

    def test_preserves_numbers(self):
        assert _slugify("version 2 draft 3") == "version-2-draft-3"


# ── build_filename ───────────────────────────────────────


class TestBuildFilename:
    def test_first_generation(self):
        assert _build_filename("hero-image", "A", None, "png") == "hero-image-A.png"

    def test_variation_b(self):
        assert _build_filename("hero-image", "B", None, "png") == "hero-image-B.png"

    def test_iteration_v2(self):
        assert _build_filename("hero-image", "A", 2, "png") == "hero-image-A-v2.png"

    def test_iteration_v5(self):
        assert _build_filename("hero-image", "A", 5, "png") == "hero-image-A-v5.png"

    def test_sequence_1_no_suffix(self):
        # sequence=1 means first version, no -v1 suffix
        assert _build_filename("hero-image", "A", 1, "png") == "hero-image-A.png"


# ── next_variation ───────────────────────────────────────


class TestNextVariation:
    def test_empty_dir(self, tmp_path):
        assert _next_variation(tmp_path, "hero") == "A"

    def test_a_exists(self, tmp_path):
        (tmp_path / "hero-A.png").touch()
        assert _next_variation(tmp_path, "hero") == "B"

    def test_a_and_b_exist(self, tmp_path):
        (tmp_path / "hero-A.png").touch()
        (tmp_path / "hero-B.png").touch()
        assert _next_variation(tmp_path, "hero") == "C"

    def test_ignores_other_slugs(self, tmp_path):
        (tmp_path / "other-A.png").touch()
        assert _next_variation(tmp_path, "hero") == "A"

    def test_ignores_iterations(self, tmp_path):
        (tmp_path / "hero-A.png").touch()
        (tmp_path / "hero-A-v2.png").touch()
        # A is taken (original exists), next should be B
        assert _next_variation(tmp_path, "hero") == "B"

    def test_non_contiguous(self, tmp_path):
        # A and C exist, B is free
        (tmp_path / "hero-A.png").touch()
        (tmp_path / "hero-C.png").touch()
        assert _next_variation(tmp_path, "hero") == "B"


# ── next_sequence ────────────────────────────────────────


class TestNextSequence:
    def test_no_files(self, tmp_path):
        # No files at all → None (first generation, no -vN)
        assert _next_sequence(tmp_path, "hero", "A") is None

    def test_base_exists(self, tmp_path):
        (tmp_path / "hero-A.png").touch()
        assert _next_sequence(tmp_path, "hero", "A") == 2

    def test_v2_exists(self, tmp_path):
        (tmp_path / "hero-A.png").touch()
        (tmp_path / "hero-A-v2.png").touch()
        assert _next_sequence(tmp_path, "hero", "A") == 3

    def test_different_variation(self, tmp_path):
        (tmp_path / "hero-B.png").touch()
        (tmp_path / "hero-B-v2.png").touch()
        # Asking about A, not B
        assert _next_sequence(tmp_path, "hero", "A") is None

    def test_gap_in_sequence(self, tmp_path):
        (tmp_path / "hero-A.png").touch()
        (tmp_path / "hero-A-v3.png").touch()
        # Max is 3, so next is 4
        assert _next_sequence(tmp_path, "hero", "A") == 4


# ── validate_model ───────────────────────────────────────


class TestValidateModel:
    def test_valid_model(self):
        assert _validate_model("gemini-3.1-flash-image-preview") is None

    def test_valid_model_25(self):
        assert _validate_model("gemini-2.5-flash-image") is None

    def test_valid_model_pro(self):
        assert _validate_model("gemini-3-pro-image-preview") is None

    def test_invalid_model(self):
        result = _validate_model("gemini-2.0-flash-preview-image-generation")
        assert result is not None
        assert "Unknown model" in result

    def test_empty_string(self):
        result = _validate_model("")
        assert result is not None

    def test_close_but_wrong(self):
        result = _validate_model("gemini-3.1-flash-image")
        assert result is not None
