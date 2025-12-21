#!/bin/bash
# Learning capture hook - runs on session Stop
# Creates issue if learning was discovered during session

set -e

# Check if gh is available
if ! command -v gh &> /dev/null; then
    exit 0
fi

# Check if we're in a git repo with GitHub remote
if ! gh repo view &> /dev/null 2>&1; then
    exit 0
fi

# The hook receives session context - for now just log
# Future: Could analyze session for learnings
echo "Session ended - learning capture hook triggered"
