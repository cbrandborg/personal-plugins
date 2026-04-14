#!/usr/bin/env python3
"""Internal helper for open5e-query.sh — formats the JSON response from
https://api.open5e.com/<endpoint>/?search=... into a human-readable summary.

Reads JSON from stdin. Do not call directly; use open5e-query.sh.
"""
import json
import sys


def trunc(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n] + "..."


def main() -> int:
    data = json.load(sys.stdin)
    results = data.get("results", [])
    if not results:
        print("No results.")
        return 0

    total = data.get("count", len(results))
    shown = min(5, len(results))
    print("Found {} result(s). Showing top {}:\n".format(total, shown))

    for r in results[:shown]:
        name = r.get("name", "(unnamed)")
        print("== {} ==".format(name))

        # Monsters
        if "armor_class" in r:
            print("  AC: {}  HP: {} ({})  Speed: {}".format(
                r.get("armor_class"), r.get("hit_points"),
                r.get("hit_dice", "?"), r.get("speed", {})
            ))
            print("  CR: {}  Type: {}  Size: {}".format(
                r.get("challenge_rating"), r.get("type", "?"), r.get("size", "?")
            ))
            actions = r.get("actions")
            if isinstance(actions, list) and actions:
                print("  Actions: {} listed".format(len(actions)))
                for a in actions[:3]:
                    print("    - {}: {}".format(a.get("name", "?"), trunc(a.get("desc", ""), 120)))

        # Spells
        elif "level" in r and "school" in r:
            print("  Level {} {}  ({})".format(
                r.get("level"), r.get("school", ""), r.get("dnd_class", "?")
            ))
            print("  Casting time: {}  Range: {}  Duration: {}".format(
                r.get("casting_time", "?"), r.get("range", "?"), r.get("duration", "?")
            ))
            print("  {}".format(trunc(r.get("desc", ""), 300)))

        # Magic items
        elif "rarity" in r:
            print("  Rarity: {}  Type: {}  Requires attunement: {}".format(
                r.get("rarity"), r.get("type", "?"), r.get("requires_attunement", "?")
            ))
            print("  {}".format(trunc(r.get("desc", ""), 300)))

        # Fallback
        else:
            desc = r.get("desc") or r.get("description") or ""
            print("  {}".format(trunc(desc, 300)))

        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
