#!/usr/bin/env bash
# canvas-sync-hook.sh — PostToolUse hook: warn if a scene file isn't in the canvas.
#
# Runs after every Write or Edit. If the target file looks like a scene file
# (path contains /Chapters/.../Scenes/...md), verify the scene's filename
# appears in the chapter's .canvas JSON. If not, print a warning to stdout.
#
# Always exits 0. Never blocks the tool call. Warning only.
#
# Expects the Claude Code hook payload on stdin as JSON with at least:
#   { "tool_input": { "file_path": "..." } }

set -e

payload=$(cat)

# Extract file_path from the JSON payload using python (more portable than jq)
file_path=$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    ti = data.get("tool_input", {}) or {}
    # Write uses "file_path"; Edit uses "file_path" too. Some tools may use "path".
    print(ti.get("file_path") or ti.get("path") or "")
except Exception:
    print("")
' 2>/dev/null)

# If we could not parse the payload, say nothing and exit cleanly.
[[ -z "$file_path" ]] && exit 0

# Only care about scene files: path must contain /Chapters/.../Scenes/...md
case "$file_path" in
  */Chapters/*/Scenes/*.md) : ;;
  *) exit 0 ;;
esac

# Derive the chapter directory (parent of Scenes)
scene_dir="$(dirname "$file_path")"
chapter_dir="$(dirname "$scene_dir")"
scene_basename="$(basename "$file_path")"

# Chapter directory may not exist yet if the write just created the scene.
# Still check: the parent Chapters/<NN - Name>/ should exist if we got here.
[[ -d "$chapter_dir" ]] || exit 0

# Find the .canvas file in the chapter directory
canvas_file=""
while IFS= read -r -d '' cf; do
  canvas_file="$cf"
  break
done < <(find "$chapter_dir" -maxdepth 1 -type f -name "*.canvas" -print0 2>/dev/null)

if [[ -z "$canvas_file" ]]; then
  echo "⚠️  dm-kit canvas-sync: chapter '$chapter_dir' has no .canvas file. Consider running scaffold-chapter to create one."
  exit 0
fi

# Check if the scene filename appears anywhere in the canvas JSON
if ! grep -qF -- "$scene_basename" "$canvas_file" 2>/dev/null; then
  cat <<EOF
⚠️  dm-kit canvas-sync warning: scene '$scene_basename' is not referenced in
   $canvas_file

Obsidian will not show this scene in the chapter canvas until a node is added.
Fix with one of:
  - Re-run /dm-kit:scaffold-scene (it handles the canvas update)
  - Run: python3 \${CLAUDE_PLUGIN_ROOT}/scripts/add-scene-to-canvas.py "$canvas_file" "<vault-relative-scene-path>"
EOF
fi

exit 0
