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

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

endpoint="$1"
query="$2"
# Normalize query to lowercase kebab for slug attempt
slug=$(printf '%s' "$query" | tr '[:upper:] ' '[:lower:]-')

base="https://www.dnd5eapi.co/api/${endpoint}"
direct="${base}/${slug}"
response_file=$(mktemp)
trap 'rm -f "$response_file"' EXIT

if curl -sSfL "$direct" >"$response_file" 2>/dev/null; then
  python3 -m json.tool "$response_file"
  exit 0
fi

# Fallback: list endpoint and filter by name containing query. Pass all shell
# input as argv data to a static Python helper; never interpolate it into code.
curl -sSfL "$base" >"$response_file"
python3 "$SCRIPT_DIR/_dnd5eapi-filter.py" "$query" "$endpoint" "$0" <"$response_file"
