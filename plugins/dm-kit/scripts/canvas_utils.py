"""Validate and update Obsidian canvas references without losing existing content."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def vault_root(canvas: Path, explicit: Path | None = None) -> Path:
    if explicit is not None:
        root = explicit.resolve()
        canvas.resolve().relative_to(root)
        return root
    for parent in canvas.resolve().parents:
        if (parent / 'Chapters').is_dir() or (parent / '.obsidian').is_dir():
            return parent
    raise ValueError('Cannot detect vault root; pass --vault-root')


def read_canvas(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Canvas must be a JSON object')
    for field in ('nodes', 'edges'):
        if not isinstance(data.get(field), list) or not all(isinstance(x, dict) for x in data[field]):
            raise ValueError(f'Canvas {field} must be an array of objects')
    return data


def references(data: dict, scene: Path, root: Path) -> list[dict]:
    return [node for node in data['nodes'] if node.get('type') == 'file'
            and isinstance(node.get('file'), str)
            and (root / node['file']).resolve() == scene.resolve()]


def write_canvas(path: Path, data: dict) -> None:
    # Atomic replacement prevents readers seeing truncated JSON. One writer at a time.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix='.canvas-', delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
