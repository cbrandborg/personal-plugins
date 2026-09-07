#!/usr/bin/env bash
# Best-effort warning hook; Python validates actual file-node references.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$script_dir/check-canvas-sync.py" || true
