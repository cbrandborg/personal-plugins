"""Server-side billable-generation limit tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

SERVER = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER))

import gemini_server  # noqa: E402
from image_helpers import GenerationLimiter  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_limiter(monkeypatch):
    monkeypatch.setattr(gemini_server, "_generation_limiter", GenerationLimiter())


def _client_must_not_run():
    raise AssertionError("API client should not be created after validation blocks a call")


def _write_png(path: Path) -> None:
    Image.new("RGB", (2, 2), "red").save(path, format="PNG")


def test_reference_upload_requires_allowed_input_root(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    _write_png(source)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_image(
            "test prompt", "test", reference_image_path=str(source)
        )
    )

    assert "allowed_input_root" in result["error"]


def test_reference_upload_must_be_inside_allowed_root(tmp_path, monkeypatch):
    allowed = tmp_path / "project"
    allowed.mkdir()
    source = tmp_path / "outside.png"
    _write_png(source)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_image(
            "test prompt",
            "test",
            reference_image_path=str(source),
            allowed_input_root=str(allowed),
        )
    )

    assert "outside allowed_input_root" in result["error"]


def test_allowed_input_root_must_be_directory(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    _write_png(source)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_image(
            "test prompt",
            "test",
            reference_image_path=str(source),
            allowed_input_root=str(source),
        )
    )

    assert "allowed_input_root must be a directory" in result["error"]


def test_reference_upload_rejects_symlink_file(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    link = tmp_path / "linked.png"
    _write_png(source)
    link.symlink_to(source)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_image(
            "test prompt",
            "test",
            reference_image_path=str(link),
            allowed_input_root=str(tmp_path),
        )
    )

    assert "symlink" in result["error"].lower()


def test_reference_upload_rejects_symlink_directory_component(tmp_path, monkeypatch):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    source = real_dir / "source.png"
    _write_png(source)
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir, target_is_directory=True)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_image(
            "test prompt",
            "test",
            reference_image_path=str(linked_dir / "source.png"),
            allowed_input_root=str(tmp_path),
        )
    )

    assert "symlink" in result["error"].lower()


def test_reference_upload_rejects_files_over_byte_limit(tmp_path, monkeypatch):
    source = tmp_path / "oversized.png"
    with source.open("wb") as image_file:
        image_file.truncate(10 * 1024 * 1024 + 1)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_image(
            "test prompt",
            "test",
            reference_image_path=str(source),
            allowed_input_root=str(tmp_path),
        )
    )

    assert "10 MiB" in result["error"]


def test_reference_upload_rejects_non_image_bytes(tmp_path, monkeypatch):
    source = tmp_path / "fake.png"
    source.write_bytes(b"not an image")
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_image(
            "test prompt",
            "test",
            reference_image_path=str(source),
            allowed_input_root=str(tmp_path),
        )
    )

    assert "valid supported image" in result["error"]


def test_reference_upload_fully_decodes_image(tmp_path, monkeypatch):
    source = tmp_path / "truncated.jpg"
    Image.new("RGB", (20, 20), "blue").save(source, format="JPEG")
    source.write_bytes(source.read_bytes()[:-20])
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_image(
            "test prompt",
            "test",
            reference_image_path=str(source),
            allowed_input_root=str(tmp_path),
        )
    )

    assert "valid supported image" in result["error"]


def test_reference_upload_uses_detected_mime_not_extension(tmp_path, monkeypatch):
    source = tmp_path / "actually-png.jpg"
    _write_png(source)
    captured = {}

    class CapturingModels:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            raise RuntimeError("stop after request capture")

    class CapturingClient:
        models = CapturingModels()

    monkeypatch.setattr(gemini_server, "_client", CapturingClient)

    gemini_server.generate_image(
        "test prompt",
        "test",
        reference_image_path=str(source),
        allowed_input_root=str(tmp_path),
    )

    assert captured["contents"][0].inline_data.mime_type == "image/png"


def test_modify_requires_allowed_input_root(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    _write_png(source)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(gemini_server.modify_image(str(source), "test instruction"))

    assert "allowed_input_root" in result["error"]


def test_variations_with_image_require_allowed_input_root(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    _write_png(source)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)

    result = json.loads(
        gemini_server.generate_variations(
            "test prompt", "test", image_path=str(source)
        )
    )

    assert "allowed_input_root" in result["error"]


def test_generate_blocks_before_api_client(monkeypatch):
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)
    result = json.loads(
        gemini_server.generate_image("test prompt", "test", max_generations=0)
    )
    assert result["error"].startswith("Generation count")


def test_modify_blocks_before_api_client(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    _write_png(source)
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)
    result = json.loads(
        gemini_server.modify_image(
            str(source),
            "test instruction",
            max_generations=0,
            allowed_input_root=str(tmp_path),
        )
    )
    assert result["error"].startswith("Generation count")


def test_variations_reserve_the_whole_batch_before_api_client(monkeypatch):
    monkeypatch.setattr(gemini_server, "_client", _client_must_not_run)
    result = json.loads(
        gemini_server.generate_variations(
            "test prompt", "test", count=2, max_generations=1
        )
    )
    assert result["error"].startswith("Generation count")


def test_local_upload_paths_must_be_absolute(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    _write_png(source)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="absolute"):
        gemini_server._load_allowed_input("source.png", ".")


def test_fifo_is_rejected_without_blocking(tmp_path):
    fifo = tmp_path / "image.png"
    os.mkfifo(fifo)
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(SERVER)!r}); "
        "import gemini_server; "
        f"gemini_server._load_allowed_input({str(fifo)!r}, {str(tmp_path)!r})"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=1,
        check=False,
    )

    assert result.returncode != 0
    assert "regular file" in result.stderr


def test_directory_swap_cannot_redirect_open_outside_root(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    held = tmp_path / "held"
    allowed.mkdir()
    outside.mkdir()
    source = allowed / "source.png"
    outside_source = outside / "source.png"
    _write_png(source)
    Image.new("RGB", (2, 2), "blue").save(outside_source, format="PNG")
    expected = source.read_bytes()
    unexpected = outside_source.read_bytes()
    original_open = os.open
    swapped = False

    def swapping_open(path, flags, *args, **kwargs):
        nonlocal swapped
        if not swapped and Path(os.fspath(path)).name == "source.png":
            allowed.rename(held)
            allowed.symlink_to(outside, target_is_directory=True)
            swapped = True
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swapping_open)
    _source, data, mime = gemini_server._load_allowed_input(
        str(source), str(allowed)
    )

    assert swapped
    assert data == expected
    assert data != unexpected
    assert mime == "image/png"
