#!/bin/bash
# Learning capture hook - called when agent wants to record a learning

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Capture interaction
python3 "$REPO_ROOT/automation/learning/capture.py" \
    --context "$1" \
    --response "$2" \
    --feedback "${3:-}"
