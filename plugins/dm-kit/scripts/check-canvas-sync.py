#!/usr/bin/env python3
"""Warn on a missing exact file-node reference; never block an agent tool."""
import json
import sys
from pathlib import Path
from canvas_utils import vault_root, read_canvas, references


def main():
    try:
        payload = json.load(sys.stdin)
        inputs = payload.get('tool_input') or {}
        raw = inputs.get('file_path') or inputs.get('path')
        if not raw:
            return
        scene = Path(raw)
        if not scene.is_absolute():
            scene = Path(payload.get('cwd') or Path.cwd()) / scene
        scene = scene.resolve()
        if scene.suffix != '.md' or scene.parent.name != 'Scenes' or 'Chapters' not in scene.parts:
            return
        canvases = list(scene.parent.parent.glob('*.canvas'))
        if len(canvases) != 1:
            print('dm-kit canvas-sync: expected exactly one chapter canvas; check manually.')
            return
        canvas = canvases[0]
        if not references(read_canvas(canvas), scene, vault_root(canvas)):
            print(f'dm-kit canvas-sync: no file node references {scene.name}; add the scene to {canvas.name}.')
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(f'dm-kit canvas-sync: could not verify canvas ({error}).')


if __name__ == '__main__':
    main()
