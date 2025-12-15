# Hooks Directory Index

Quick reference guide to all files in the hooks directory.

## Overview

This directory contains the **Keboola Claude Code Error Reporter** - an automated system for reporting Keboola-related errors to GitHub Issues.

## Files

### 🚀 Quick Start

**[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- Installation (1 minute)
- First report (30 seconds)
- Common use cases
- Configuration basics

**Start here if you're new!**

---

### 📘 Core Documentation

**[README.md](README.md)** - Complete documentation (571 lines)
- Full feature overview
- Installation guide
- Usage instructions with all options
- How it works (technical details)
- Privacy and security considerations
- Comprehensive troubleshooting
- Development guide

**The definitive reference.**

---

### 🔌 Integration Guide

**[INTEGRATION.md](INTEGRATION.md)** - Integration patterns (408 lines)
- Claude Code prompt integration
- Custom slash commands
- Automated detection patterns
- CI/CD integration (GitHub Actions, pre-commit hooks)
- Multiple real-world examples
- Best practices
- Advanced patterns

**Read this to integrate with your workflow.**

---

### 📝 Version History

**[CHANGELOG.md](CHANGELOG.md)** - Version history and changes (188 lines)
- Release notes
- Feature list
- Technical statistics
- Known limitations
- Future enhancements
- Migration notes

**Track what's new and what's planned.**

---

### 🛠️ Executable Scripts

#### Main Script

**[error-reporter.sh](error-reporter.sh)** - The core error reporter (477 lines)

```bash
./hooks/error-reporter.sh \
  --error-message "Your error" \
  --context "What you were doing" \
  --severity high
```

Features:
- Full-featured CLI with all options
- Rate limiting and deduplication
- Dry-run mode
- Debug mode
- State management

#### Convenience Wrapper

**[report-keboola-error.sh](report-keboola-error.sh)** - Quick wrapper (39 lines)

```bash
./hooks/report-keboola-error.sh "Error message" "Context" "severity"
```

Features:
- Simplified interface
- Positional arguments
- Quick reporting

---

## Quick Reference

### Installation

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Make scripts executable
chmod +x hooks/*.sh
```

### Basic Usage

```bash
# Dry run (preview)
./hooks/error-reporter.sh --error-message "Test" --dry-run

# Create issue
./hooks/error-reporter.sh --error-message "API returned 404" --severity high

# Quick report
./hooks/report-keboola-error.sh "Error message"
```

### Configuration

```bash
# Change repository
export ERROR_REPORTER_REPO="my-org/my-repo"

# Disable reporting
export ERROR_REPORTER_DISABLED=1

# Enable debug
export ERROR_REPORTER_DEBUG=1
```

## File Statistics

| File | Type | Lines | Size | Purpose |
|------|------|-------|------|---------|
| `error-reporter.sh` | Bash | 477 | 13K | Main script |
| `report-keboola-error.sh` | Bash | 39 | 1.1K | Wrapper |
| `README.md` | Markdown | 571 | 13K | Main docs |
| `QUICKSTART.md` | Markdown | 260 | 5.1K | Quick guide |
| `INTEGRATION.md` | Markdown | 408 | 9.3K | Integration |
| `CHANGELOG.md` | Markdown | 188 | 5.9K | Version history |

**Total**: 1,943 lines (516 code, 1,427 documentation)

## Documentation Flow

```
┌─────────────────┐
│   New User?     │
│                 │
│  Start Here:    │
│ QUICKSTART.md   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Need Details?  │
│                 │
│   Read This:    │
│   README.md     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Integrating?  │
│                 │
│   Check This:   │
│ INTEGRATION.md  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Developer?    │
│                 │
│   See This:     │
│  CHANGELOG.md   │
└─────────────────┘
```

## Common Tasks

### First Time Setup

1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `./hooks/error-reporter.sh --help`
3. Test with `--dry-run`

### Report an Error

1. Identify the error
2. Run: `./hooks/error-reporter.sh --error-message "..." --context "..." --severity X`
3. Verify on GitHub

### Integrate with Claude Code

1. Read [INTEGRATION.md](INTEGRATION.md)
2. Choose integration pattern
3. Test with `--dry-run`
4. Deploy

### Troubleshooting

1. Check [README.md](README.md) troubleshooting section
2. Enable debug: `export ERROR_REPORTER_DEBUG=1`
3. Run with `--dry-run`
4. Check prerequisites

## Support

- **Questions**: See [README.md](README.md)
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Integration**: See [INTEGRATION.md](INTEGRATION.md)
- **Issues**: Report on GitHub

## Links

- **Repository**: [keboola/xmas-challenge](https://github.com/keboola/xmas-challenge)
- **Main README**: [../README.md](../README.md)
- **GitHub CLI**: [cli.github.com](https://cli.github.com/)

## Version

**Current Version**: 1.0.0 (2025-12-15)

See [CHANGELOG.md](CHANGELOG.md) for details.

---

## Quick Command Reference

```bash
# Help
./hooks/error-reporter.sh --help

# Dry run
./hooks/error-reporter.sh --error-message "test" --dry-run

# Simple report
./hooks/error-reporter.sh --error-message "API error"

# Full report
./hooks/error-reporter.sh \
  --error-message "Detailed error message" \
  --context "What was happening" \
  --solution "What was tried" \
  --keboola-version "1.2.3" \
  --component "component-name" \
  --severity high

# Force report (skip checks)
./hooks/error-reporter.sh --error-message "..." --force

# Debug mode
export ERROR_REPORTER_DEBUG=1
./hooks/error-reporter.sh --error-message "..."

# View reported issues
gh issue list --label "auto-report"

# Check state
cat ~/.config/keboola-error-reporter/reported_errors.db
```

---

**Navigation**: You are here → `hooks/INDEX.md`

**Next Steps**: Read [QUICKSTART.md](QUICKSTART.md) to get started!
