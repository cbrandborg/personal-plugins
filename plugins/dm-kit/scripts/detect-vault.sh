#!/usr/bin/env bash
# detect-vault.sh — Walk up from CWD to find the nearest D&D campaign vault root.
#
# A vault root is a directory containing BOTH:
#   - CLAUDE.md (with any content)
#   - a Chapters/ subdirectory
#
# Prints the absolute path of the vault root on success, exits 0.
# Prints nothing and exits 1 if no vault is found.
#
# Usage:
#   VAULT="$(./detect-vault.sh)" || { echo "not in a vault"; exit 1; }

set -euo pipefail

start="${1:-$PWD}"
dir="$(cd "$start" && pwd)"

while [[ "$dir" != "/" ]]; do
  if [[ -f "$dir/CLAUDE.md" && -d "$dir/Chapters" ]]; then
    echo "$dir"
    exit 0
  fi
  dir="$(dirname "$dir")"
done

exit 1
