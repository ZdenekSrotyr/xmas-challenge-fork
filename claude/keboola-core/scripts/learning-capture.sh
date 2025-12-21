#!/bin/bash
# Learning capture hook - captures knowledge gaps discovered during sessions
# Called by Claude Code when session ends or when explicitly invoked

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Find repo root (where automation/learning exists)
REPO_ROOT="${CLAUDE_PLUGIN_ROOT:-$PLUGIN_ROOT}"
if [ -d "$REPO_ROOT/../../automation/learning" ]; then
    REPO_ROOT="$(cd "$REPO_ROOT/../.." && pwd)"
elif [ -d "$REPO_ROOT/../automation/learning" ]; then
    REPO_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
fi

LEARNING_DIR="$REPO_ROOT/automation/learning"

# Check if learning system exists
if [ ! -f "$LEARNING_DIR/capture.py" ]; then
    echo "Learning system not found at $LEARNING_DIR"
    exit 0
fi

# Capture parameters
CONTEXT="${1:-Session ended}"
RESPONSE="${2:-No specific response}"
FEEDBACK="${3:-}"

# Run capture
python3 "$LEARNING_DIR/capture.py" \
    --context "$CONTEXT" \
    --response "$RESPONSE" \
    --feedback "$FEEDBACK" 2>/dev/null || true

echo "Learning captured successfully"
