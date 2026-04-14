#!/usr/bin/env bash
# dnd5eapi-query.sh — Query the dnd5eapi.co public API for D&D 5e SRD content.
#
# An alternative/overlap source to Open5e. Sometimes has different coverage
# (rules, skills, ability score details). No auth required.
# Docs: https://www.dnd5eapi.co/docs/
#
# Usage:
#   dnd5eapi-query.sh <endpoint> <slug-or-search>
#
# Common endpoints:
#   monsters       — e.g. "goblin", "adult-red-dragon"
#   spells         — e.g. "fireball"
#   skills         — e.g. "athletics", "perception"
#   conditions     — e.g. "poisoned", "frightened"
#   rules          — top-level rules sections
#   magic-items    — e.g. "bag-of-holding"
#   classes        — e.g. "paladin"
#
# The dnd5eapi uses kebab-case slugs rather than search. This script tries a
# direct slug lookup first; if that 404s it falls back to listing endpoint
# matches containing the query.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  cat >&2 <<EOF
usage: $0 <endpoint> <slug-or-search>

Common endpoints: monsters, spells, skills, conditions, rules, magic-items, classes

Example: $0 monsters goblin
         $0 skills athletics
EOF
  exit 1
fi

endpoint="$1"
query="$2"
# Normalize query to lowercase kebab for slug attempt
slug=$(printf '%s' "$query" | tr '[:upper:] ' '[:lower:]-')

base="https://www.dnd5eapi.co/api/${endpoint}"
direct="${base}/${slug}"

if result=$(curl -sSfL "$direct" 2>/dev/null); then
  printf '%s' "$result" | python3 -m json.tool
  exit 0
fi

# Fallback: list endpoint and filter by name containing query
curl -sSfL "$base" | python3 -c "
import json, sys
q = '$query'.lower()
data = json.load(sys.stdin)
results = data.get('results', [])
matches = [r for r in results if q in r.get('name', '').lower() or q in r.get('index', '').lower()]
if not matches:
    print(f'No matches for \"{q}\" in {len(results)} entries at endpoint \"$endpoint\".')
    sys.exit(1)
print(f'Matches for \"{q}\":')
for m in matches[:20]:
    print(f\"  - {m.get('name', '?')}  (slug: {m.get('index', '?')})\")
print()
print(f\"Re-run with an exact slug to get details, e.g.:  $0 $endpoint {matches[0].get('index', '')}\")
"
