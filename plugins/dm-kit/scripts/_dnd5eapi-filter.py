#!/usr/bin/env python3
"""Filter a dnd5eapi collection without evaluating shell input as code."""

from __future__ import annotations

import json
import sys


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: _dnd5eapi-filter.py <query> <endpoint> <script>", file=sys.stderr)
        return 2

    query, endpoint, script = sys.argv[1:]
    q = query.lower()
    data = json.load(sys.stdin)
    results = data.get("results", [])
    matches = [
        item
        for item in results
        if q in item.get("name", "").lower() or q in item.get("index", "").lower()
    ]
    if not matches:
        print(f'No matches for "{q}" in {len(results)} entries at endpoint "{endpoint}".')
        return 1

    print(f'Matches for "{q}":')
    for match in matches[:20]:
        print(f"  - {match.get('name', '?')}  (slug: {match.get('index', '?')})")
    print()
    print(
        f"Re-run with an exact slug to get details, e.g.:  "
        f"{script} {endpoint} {matches[0].get('index', '')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
