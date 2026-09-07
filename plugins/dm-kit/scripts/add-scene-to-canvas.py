#!/usr/bin/env python3
"""Add an existing scene to a canvas. Repeated calls return its existing node ID.

Usage: add-scene-to-canvas.py CANVAS VAULT_RELATIVE_SCENE [--vault-root ROOT]
The vault is detected from an ancestor with Chapters/ or .obsidian/.
"""
import argparse
import sys
import uuid
from pathlib import Path
from canvas_utils import vault_root, read_canvas, references, write_canvas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('canvas_file', type=Path)
    parser.add_argument('scene_file')
    parser.add_argument('--vault-root', type=Path)
    parser.add_argument('--label', help='Reserved; file nodes use the filename')
    parser.add_argument('--width', type=int, default=400)
    parser.add_argument('--height', type=int, default=300)
    args = parser.parse_args()
    try:
        if not 250 <= args.height <= 600 or args.width <= 0:
            raise ValueError('Height must be 250–600 and width must be positive')
        if Path(args.scene_file).is_absolute():
            raise ValueError('Scene path must be vault-relative')
        root = vault_root(args.canvas_file, args.vault_root)
        scene = (root / args.scene_file).resolve()
        relative = scene.relative_to(root).as_posix()
        if not scene.is_file():
            raise ValueError(f'Scene does not exist: {relative}')
        data = read_canvas(args.canvas_file)
        existing = references(data, scene, root)
        if existing:
            if not existing[0].get('id'):
                raise ValueError('Existing file node has no ID')
            print(existing[0]['id'])
            return 0
        files = [n for n in data['nodes'] if n.get('type') == 'file']
        for node in files:
            if any(not isinstance(node.get(k, default), (int, float))
                   for k, default in [('x', 0), ('y', 0), ('height', 300)]):
                raise ValueError('Existing file node has invalid geometry')
        last = max(files, key=lambda n: n.get('y', 0)) if files else None
        node_id = uuid.uuid4().hex[:16]
        data['nodes'].append(dict(id=node_id, type='file', file=relative,
            x=last.get('x', 0) if last else 0,
            y=last.get('y', 0) + last.get('height', 300) + 100 if last else 0,
            width=args.width, height=args.height))
        write_canvas(args.canvas_file, data)
        print(node_id)
        return 0
    except (OSError, ValueError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
