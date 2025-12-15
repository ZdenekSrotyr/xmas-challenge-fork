#!/usr/bin/env bash

################################################################################
# Convenience wrapper for error-reporter.sh
#
# Usage:
#   report-keboola-error.sh "error message" ["context"] ["severity"]
#
# Examples:
#   report-keboola-error.sh "API returned 404"
#   report-keboola-error.sh "API returned 404" "Listing workspaces" "high"
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ERROR_REPORTER="${SCRIPT_DIR}/error-reporter.sh"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 \"error message\" [\"context\"] [\"severity\"]"
    echo ""
    echo "Examples:"
    echo "  $0 \"API returned 404\""
    echo "  $0 \"API returned 404\" \"Listing workspaces\""
    echo "  $0 \"API returned 404\" \"Listing workspaces\" \"high\""
    exit 1
fi

ERROR_MESSAGE="$1"
CONTEXT="${2:-}"
SEVERITY="${3:-medium}"

ARGS=("--error-message" "${ERROR_MESSAGE}" "--severity" "${SEVERITY}")

if [[ -n "${CONTEXT}" ]]; then
    ARGS+=("--context" "${CONTEXT}")
fi

exec "${ERROR_REPORTER}" "${ARGS[@]}"
