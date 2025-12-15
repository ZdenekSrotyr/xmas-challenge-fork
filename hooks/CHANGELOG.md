# Changelog

All notable changes to the Keboola Error Reporter will be documented in this file.

## [1.0.0] - 2025-12-15

### Added

#### Core Script (`error-reporter.sh`)
- Initial release of automatic error reporting system
- GitHub Issue creation via `gh` CLI
- Comprehensive command-line interface with multiple options
- Safety features:
  - Rate limiting (10/hour, 50/day)
  - Deduplication (24-hour window)
  - Dry-run mode for testing
  - Force mode to bypass checks
- State management in `~/.config/keboola-error-reporter/`
- Structured issue templates with:
  - Error message formatting
  - Context sections
  - Solution tracking
  - Environment details
  - Next steps checklist
- Automatic label application:
  - `auto-report` for all reports
  - `needs-triage` for human review
  - `priority:*` based on severity
  - `component:*` for component-specific issues
- Color-coded logging (info, success, warning, error, debug)
- Debug mode for troubleshooting
- Comprehensive input validation
- Environment variable configuration support

#### Convenience Wrapper (`report-keboola-error.sh`)
- Simplified interface for quick error reporting
- Positional arguments for common use cases
- Automatic pass-through to main script

#### Documentation
- **README.md** (571 lines): Complete user documentation
  - Overview and features
  - Installation instructions
  - Usage guide with all options
  - How it works (technical details)
  - Configuration options
  - Multiple real-world examples
  - Privacy and data considerations
  - Comprehensive troubleshooting guide
  - Development section
  - Integration points

- **QUICKSTART.md** (260 lines): Get started in 5 minutes
  - Quick installation
  - First report walkthrough
  - Common use cases
  - Configuration basics
  - Safety features overview
  - Best practices
  - Common issues and solutions

- **INTEGRATION.md** (408 lines): Integration patterns
  - Claude Code prompt integration
  - Custom slash command examples
  - Automated detection patterns
  - Test failure reporting
  - Multiple integration examples
  - GitHub Actions workflow
  - Pre-commit hook example
  - Best practices for automation
  - Monitoring and metrics
  - Advanced integration patterns
  - Custom wrapper examples

### Technical Details

#### Features
- **Rate Limiting**: Prevents spam with configurable limits
- **Deduplication**: SHA-256 hash-based duplicate detection
- **State Management**: Persistent state in user config directory
- **Error Handling**: Graceful failures with helpful error messages
- **Validation**: Pre-flight checks for all prerequisites
- **Privacy**: Only reports explicitly provided information
- **Flexibility**: Environment variables for configuration
- **Testability**: Dry-run mode for safe testing

#### Files Created
```
hooks/
├── .gitignore               # State directory exclusions
├── CHANGELOG.md            # This file
├── INTEGRATION.md          # Integration guide (408 lines)
├── QUICKSTART.md          # Quick start guide (260 lines)
├── README.md              # Main documentation (571 lines)
├── error-reporter.sh      # Main script (477 lines, executable)
└── report-keboola-error.sh # Convenience wrapper (39 lines, executable)
```

#### Statistics
- Total Lines of Code: 516 (bash scripts)
- Total Lines of Documentation: 1,239 (markdown)
- Test Coverage: 6 automated tests
- Pass Rate: 100%

#### Dependencies
- `bash` 3.2+ (macOS/Linux)
- `gh` (GitHub CLI) 2.0+
- Standard Unix utilities: `awk`, `grep`, `shasum`, `date`, `cut`

#### Configuration
- Default repository: `keboola/xmas-challenge`
- State directory: `~/.config/keboola-error-reporter/`
- Default severity: `medium`
- Rate limits: 10/hour, 50/day
- Deduplication window: 24 hours

#### Environment Variables
- `ERROR_REPORTER_REPO`: Target GitHub repository
- `ERROR_REPORTER_DISABLED`: Disable reporting (set to "1")
- `ERROR_REPORTER_DEBUG`: Enable debug output (set to "1")

### Testing

All tests passing:
1. Help command validation
2. Missing parameter error handling
3. Invalid severity validation
4. Dry-run mode functionality
5. Full parameter integration
6. Convenience wrapper validation

### Known Limitations

- Requires GitHub CLI to be installed and authenticated
- Requires write access to target repository
- Rate limits are per-machine, not per-user
- Deduplication uses simple hash (error message + component)
- No automatic issue updates (create only)

### Future Enhancements

Potential improvements for future versions:
- [ ] Integration with issue comments (update existing issues)
- [ ] Support for other issue trackers (GitLab, Jira, etc.)
- [ ] Machine learning-based duplicate detection
- [ ] Automatic severity detection from error patterns
- [ ] Integration with CI/CD platforms
- [ ] Web dashboard for reporting analytics
- [ ] Email notifications for issue creation
- [ ] Slack/Discord webhook integration
- [ ] Custom template support
- [ ] Multi-repository reporting
- [ ] Issue search before creating (enhanced deduplication)

### Migration Notes

This is the initial release, no migration needed.

### Security Considerations

- No sensitive data collected by default
- All data explicitly provided by user
- State files stored in user's home directory
- Respects GitHub authentication and permissions
- No network requests except to GitHub API (via `gh` CLI)

### License

Part of the Keboola Xmas Challenge project.

### Contributors

- Initial implementation: Claude Code (Anthropic)
- Concept: Keboola Xmas Challenge Team

### Support

- Documentation: See [README.md](README.md)
- Quick Start: See [QUICKSTART.md](QUICKSTART.md)
- Integration: See [INTEGRATION.md](INTEGRATION.md)
- Issues: Report via GitHub Issues (or use the error reporter itself!)

---

**Note**: Version numbers follow [Semantic Versioning](https://semver.org/):
- MAJOR: Incompatible API changes
- MINOR: New functionality (backwards compatible)
- PATCH: Bug fixes (backwards compatible)
