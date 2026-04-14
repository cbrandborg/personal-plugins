#!/usr/bin/env bash
# detect-vault.sh — Walk up from CWD to find the nearest D&D campaign vault root.
#
# A vault root is a directory containing BOTH:
#   - CLAUDE.md (with any content)
#   - a Chapters/ subdirectory
#
# Preserves the CWD path style literally — does NOT resolve symlinks or swap
# to physical paths. This matters when the user has the same vault registered
# at multiple roots (e.g. Google Drive mount + Documents mirror). The returned
# path is always anchored in the CWD tree the caller is actually using.
#
# Prints the absolute path of the vault root on success, exits 0.
# Prints nothing and exits 1 if no vault is found.
#
# Usage:
#   VAULT="$(./detect-vault.sh)" || { echo "not in a vault"; exit 1; }

set -euo pipefail

start="${1:-$PWD}"

# Normalize to absolute without using `cd` (which resolves symlinks on macOS).
case "$start" in
  /*) dir="$start" ;;
  *)  dir="$PWD/$start" ;;
esac

dir="${dir%/}"
[[ -z "$dir" ]] && dir="/"

while [[ "$dir" != "/" && -n "$dir" ]]; do
  if [[ -f "$dir/CLAUDE.md" && -d "$dir/Chapters" ]]; then
    echo "$dir"
    exit 0
  fi
  dir="$(dirname "$dir")"
done

exit 1
