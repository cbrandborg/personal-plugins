#!/usr/bin/env bash
# open5e-query.sh — Query the Open5e public API for D&D 5e content.
#
# Open5e is a free, SRD-covered API for monsters, spells, classes, magic items,
# races, backgrounds, feats, conditions, and core rules. No auth required.
# Docs: https://open5e.com/api-docs
#
# Usage:
#   open5e-query.sh <endpoint> <search>
#
# Endpoints (most useful):
#   monsters       — creatures with full stat blocks
#   spells         — spells with level, school, casting time, effects
#   magicitems     — magic items with rarity, attunement, properties
#   classes        — class features, progression
#   races          — racial traits
#   conditions     — condition descriptions (prone, poisoned, etc.)
#   backgrounds    — backgrounds with features and proficiencies
#   feats          — feat prerequisites and benefits
#   weapons        — weapon properties and damage
#   armor          — armor AC, stealth disadvantage, etc.
#
# Examples:
#   open5e-query.sh monsters goblin
#   open5e-query.sh spells fireball
#   open5e-query.sh magicitems "bag of holding"

set -euo pipefail

if [[ $# -lt 2 ]]; then
  cat >&2 <<EOF
usage: $0 <endpoint> <search>

Endpoints: monsters, spells, magicitems, classes, races, conditions,
           backgrounds, feats, weapons, armor

Example: $0 monsters "young red dragon"
EOF
  exit 1
fi

endpoint="$1"
search="$2"
encoded=$(printf '%s' "$search" | python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.stdin.read()))')
url="https://api.open5e.com/${endpoint}/?search=${encoded}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
curl -sSfL "$url" | python3 "${SCRIPT_DIR}/_open5e-format.py"
