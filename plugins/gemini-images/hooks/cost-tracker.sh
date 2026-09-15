#!/bin/bash
set -euo pipefail

exec python3 "${CLAUDE_PLUGIN_ROOT}/hooks/cost_tracker.py"
