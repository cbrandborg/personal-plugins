#!/bin/bash
set -euo pipefail

# Read the hook input from stdin (consumed but not used — counter is global per session lifetime)
cat > /dev/null

# Single counter file per machine (resets when Claude Code session restarts the MCP server)
COUNTER_FILE="/tmp/gemini-images.count"

# Try to read max_generations from project settings
MAX_GENERATIONS=5
for dir in "." "$HOME"; do
  SETTINGS_FILE="${dir}/.claude/gemini-images.local.md"
  if [[ -f "$SETTINGS_FILE" ]]; then
    CUSTOM_MAX=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$SETTINGS_FILE" | grep '^max_generations:' | sed 's/max_generations: *//')
    if [[ -n "$CUSTOM_MAX" && "$CUSTOM_MAX" =~ ^[0-9]+$ ]]; then
      MAX_GENERATIONS=$CUSTOM_MAX
    fi
    break
  fi
done

# Read current count
CURRENT=0
if [[ -f "$COUNTER_FILE" ]]; then
  CURRENT=$(cat "$COUNTER_FILE")
fi

# Check limit
if [[ $CURRENT -ge $MAX_GENERATIONS ]]; then
  cat <<EOF
{"decision":"block","reason":"Generation limit reached (${CURRENT}/${MAX_GENERATIONS}). Run /image-settings to increase max_generations, or start a new session to reset the counter."}
EOF
  exit 0
fi

# Increment and allow
echo $((CURRENT + 1)) > "$COUNTER_FILE"

cat <<EOF
{"decision":"allow","reason":"Generation $((CURRENT + 1)) of ${MAX_GENERATIONS}"}
EOF
