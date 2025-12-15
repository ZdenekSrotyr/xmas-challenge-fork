#!/usr/bin/env bash

################################################################################
# Keboola Claude Code Error Reporter
#
# Automatically reports Keboola-related errors encountered by Claude Code
# to GitHub Issues for tracking and resolution.
#
# Usage:
#   error-reporter.sh [OPTIONS]
#
# Options:
#   --error-message TEXT     The error message (required)
#   --context TEXT          Additional context about what was attempted
#   --solution TEXT         What Claude tried to fix it
#   --keboola-version TEXT  Keboola version if known
#   --component TEXT        Component name if applicable
#   --severity LEVEL        critical|high|medium|low (default: medium)
#   --dry-run              Don't create issue, just show what would be created
#   --force                Skip deduplication check
#   --help                 Show this help message
#
# Environment Variables:
#   ERROR_REPORTER_REPO     Target GitHub repo (default: keboola/xmas-challenge)
#   ERROR_REPORTER_DISABLED Set to "1" to disable reporting
#   ERROR_REPORTER_DEBUG    Set to "1" for verbose output
#
################################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="${HOME}/.config/keboola-error-reporter"
CACHE_FILE="${STATE_DIR}/reported_errors.db"
RATE_LIMIT_FILE="${STATE_DIR}/rate_limit.log"
MAX_REPORTS_PER_HOUR=10
MAX_REPORTS_PER_DAY=50
DEDUP_WINDOW_HOURS=24

# Default values
REPO="${ERROR_REPORTER_REPO:-keboola/xmas-challenge}"
SEVERITY="medium"
DRY_RUN=false
FORCE=false
DEBUG="${ERROR_REPORTER_DEBUG:-0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Helper Functions
################################################################################

log() {
    echo -e "${BLUE}[ERROR-REPORTER]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

debug() {
    if [[ "${DEBUG}" == "1" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $*" >&2
    fi
}

show_help() {
    sed -n '/^# Usage:/,/^$/p' "$0" | sed 's/^# //; s/^#//'
    exit 0
}

################################################################################
# Validation Functions
################################################################################

check_prerequisites() {
    debug "Checking prerequisites..."

    # Check if error reporting is disabled
    if [[ "${ERROR_REPORTER_DISABLED:-0}" == "1" ]]; then
        log_warning "Error reporting is disabled via ERROR_REPORTER_DISABLED"
        exit 0
    fi

    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        log_error "Install it from: https://cli.github.com/"
        exit 1
    fi

    # Check if gh is authenticated
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated"
        log_error "Run: gh auth login"
        exit 1
    fi

    # Check if repo exists and is accessible
    if ! gh repo view "${REPO}" &> /dev/null; then
        log_error "Cannot access repository: ${REPO}"
        log_error "Check your permissions or set ERROR_REPORTER_REPO"
        exit 1
    fi

    debug "Prerequisites check passed"
}

validate_inputs() {
    debug "Validating inputs..."

    if [[ -z "${ERROR_MESSAGE:-}" ]]; then
        log_error "Error message is required (--error-message)"
        exit 1
    fi

    if [[ ! "${SEVERITY}" =~ ^(critical|high|medium|low)$ ]]; then
        log_error "Invalid severity: ${SEVERITY}"
        log_error "Must be one of: critical, high, medium, low"
        exit 1
    fi

    debug "Input validation passed"
}

################################################################################
# Rate Limiting
################################################################################

init_state_dir() {
    mkdir -p "${STATE_DIR}"
    touch "${CACHE_FILE}"
    touch "${RATE_LIMIT_FILE}"
}

check_rate_limit() {
    debug "Checking rate limits..."

    local current_time=$(date +%s)
    local hour_ago=$((current_time - 3600))
    local day_ago=$((current_time - 86400))

    # Count reports in the last hour
    local reports_last_hour=$(awk -v threshold="${hour_ago}" '$1 > threshold' "${RATE_LIMIT_FILE}" 2>/dev/null | wc -l | tr -d ' ')

    # Count reports in the last day
    local reports_last_day=$(awk -v threshold="${day_ago}" '$1 > threshold' "${RATE_LIMIT_FILE}" 2>/dev/null | wc -l | tr -d ' ')

    debug "Reports in last hour: ${reports_last_hour}/${MAX_REPORTS_PER_HOUR}"
    debug "Reports in last day: ${reports_last_day}/${MAX_REPORTS_PER_DAY}"

    if [[ ${reports_last_hour} -ge ${MAX_REPORTS_PER_HOUR} ]]; then
        log_error "Rate limit exceeded: ${reports_last_hour} reports in the last hour"
        log_error "Maximum allowed: ${MAX_REPORTS_PER_HOUR} per hour"
        log_error "Please try again later or use --force to override"
        return 1
    fi

    if [[ ${reports_last_day} -ge ${MAX_REPORTS_PER_DAY} ]]; then
        log_error "Rate limit exceeded: ${reports_last_day} reports in the last day"
        log_error "Maximum allowed: ${MAX_REPORTS_PER_DAY} per day"
        log_error "Please contact maintainers if you need higher limits"
        return 1
    fi

    debug "Rate limit check passed"
    return 0
}

record_report() {
    local current_time=$(date +%s)
    echo "${current_time}" >> "${RATE_LIMIT_FILE}"

    # Clean up old entries (older than 24 hours)
    local day_ago=$((current_time - 86400))
    local temp_file="${RATE_LIMIT_FILE}.tmp"
    awk -v threshold="${day_ago}" '$1 > threshold' "${RATE_LIMIT_FILE}" > "${temp_file}" 2>/dev/null || true
    mv "${temp_file}" "${RATE_LIMIT_FILE}"
}

################################################################################
# Deduplication
################################################################################

compute_error_hash() {
    # Create a hash from error message and component (if any)
    local input="${ERROR_MESSAGE}|${COMPONENT:-}"
    echo -n "${input}" | shasum -a 256 | awk '{print $1}'
}

check_duplicate() {
    if [[ "${FORCE}" == "true" ]]; then
        debug "Skipping duplicate check (--force)"
        return 0
    fi

    debug "Checking for duplicates..."

    local error_hash=$(compute_error_hash)
    local current_time=$(date +%s)
    local window_start=$((current_time - (DEDUP_WINDOW_HOURS * 3600)))

    # Check if this error was reported recently
    if grep -q "^${error_hash}|" "${CACHE_FILE}" 2>/dev/null; then
        local last_report=$(grep "^${error_hash}|" "${CACHE_FILE}" | tail -1 | cut -d'|' -f2)

        if [[ ${last_report} -gt ${window_start} ]]; then
            local hours_ago=$(( (current_time - last_report) / 3600 ))
            log_warning "This error was already reported ${hours_ago} hours ago"
            log_warning "Skipping duplicate report (use --force to override)"
            return 1
        fi
    fi

    debug "No duplicate found"
    return 0
}

record_error() {
    local error_hash=$(compute_error_hash)
    local current_time=$(date +%s)
    local issue_url="$1"

    echo "${error_hash}|${current_time}|${issue_url}" >> "${CACHE_FILE}"

    # Clean up old entries
    local window_start=$((current_time - (DEDUP_WINDOW_HOURS * 3600 * 7))) # Keep 1 week
    local temp_file="${CACHE_FILE}.tmp"
    awk -F'|' -v threshold="${window_start}" '$2 > threshold' "${CACHE_FILE}" > "${temp_file}" 2>/dev/null || true
    mv "${temp_file}" "${CACHE_FILE}"
}

################################################################################
# GitHub Issue Creation
################################################################################

generate_issue_body() {
    cat <<EOF
## Error Report

**This issue was automatically generated by Claude Code Error Reporter**

### Error Details

**Error Message:**
\`\`\`
${ERROR_MESSAGE}
\`\`\`

EOF

    if [[ -n "${CONTEXT:-}" ]]; then
        cat <<EOF
**Context:**
${CONTEXT}

EOF
    fi

    if [[ -n "${SOLUTION:-}" ]]; then
        cat <<EOF
**Attempted Solution:**
${SOLUTION}

EOF
    fi

    cat <<EOF
### Environment

EOF

    if [[ -n "${KEBOOLA_VERSION:-}" ]]; then
        echo "- **Keboola Version:** ${KEBOOLA_VERSION}"
    fi

    if [[ -n "${COMPONENT:-}" ]]; then
        echo "- **Component:** ${COMPONENT}"
    fi

    cat <<EOF
- **Severity:** ${SEVERITY}
- **Reported:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- **Reporter:** Claude Code Error Reporter

### Next Steps

- [ ] Triage: Verify this is a valid issue
- [ ] Categorize: Assign to appropriate area
- [ ] Investigate: Reproduce and understand root cause
- [ ] Fix: Update documentation/code
- [ ] Verify: Ensure Claude Code can handle this scenario

---

*This report was automatically generated. If this is a duplicate or invalid, please close it and consider adjusting the error reporter configuration.*
EOF
}

generate_issue_title() {
    local title="[Auto-Report] "

    if [[ -n "${COMPONENT:-}" ]]; then
        title+="${COMPONENT}: "
    fi

    # Truncate error message to 80 chars for title
    local error_snippet=$(echo "${ERROR_MESSAGE}" | head -1 | cut -c1-80)
    if [[ ${#ERROR_MESSAGE} -gt 80 ]]; then
        error_snippet+="..."
    fi

    title+="${error_snippet}"

    echo "${title}"
}

get_labels() {
    local labels="auto-report,needs-triage"

    case "${SEVERITY}" in
        critical)
            labels+=",priority:critical"
            ;;
        high)
            labels+=",priority:high"
            ;;
        low)
            labels+=",priority:low"
            ;;
    esac

    if [[ -n "${COMPONENT:-}" ]]; then
        labels+=",component:${COMPONENT}"
    fi

    echo "${labels}"
}

create_github_issue() {
    local title=$(generate_issue_title)
    local body=$(generate_issue_body)
    local labels=$(get_labels)

    debug "Title: ${title}"
    debug "Labels: ${labels}"

    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN - Would create issue with:"
        echo ""
        echo "Repository: ${REPO}"
        echo "Title: ${title}"
        echo "Labels: ${labels}"
        echo ""
        echo "Body:"
        echo "----------------------------------------"
        echo "${body}"
        echo "----------------------------------------"
        return 0
    fi

    log "Creating GitHub issue..."

    # Create the issue and capture the URL
    local issue_url
    issue_url=$(echo "${body}" | gh issue create \
        --repo "${REPO}" \
        --title "${title}" \
        --body-file - \
        --label "${labels}" \
        2>&1)

    if [[ $? -eq 0 ]]; then
        log_success "Issue created: ${issue_url}"
        record_error "${issue_url}"
        record_report

        # Return the URL for scripts that might want to use it
        echo "${issue_url}"
        return 0
    else
        log_error "Failed to create issue"
        log_error "${issue_url}"
        return 1
    fi
}

################################################################################
# Main
################################################################################

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --error-message)
                ERROR_MESSAGE="$2"
                shift 2
                ;;
            --context)
                CONTEXT="$2"
                shift 2
                ;;
            --solution)
                SOLUTION="$2"
                shift 2
                ;;
            --keboola-version)
                KEBOOLA_VERSION="$2"
                shift 2
                ;;
            --component)
                COMPONENT="$2"
                shift 2
                ;;
            --severity)
                SEVERITY="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Initialize
    init_state_dir

    # Validate
    validate_inputs
    check_prerequisites

    # Check rate limits (unless dry run)
    if [[ "${DRY_RUN}" != "true" ]] && [[ "${FORCE}" != "true" ]]; then
        if ! check_rate_limit; then
            exit 1
        fi
    fi

    # Check for duplicates
    if ! check_duplicate; then
        exit 1
    fi

    # Create the issue
    create_github_issue
}

# Run main function
main "$@"
