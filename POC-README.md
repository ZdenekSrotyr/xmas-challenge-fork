# 🎄 Keboola Xmas Challenge - Proof of Concept

> **⚠️ IMPORTANT: This is a PROOF OF CONCEPT**
> 
> This repository demonstrates a self-healing knowledge system for Claude Code + Keboola.
> It is **NOT connected to the official ai-kit repository** and is for **testing purposes only**.

## What This POC Demonstrates

1. **Self-Healing Documentation**: Automatically detects gaps, creates issues, and proposes fixes
2. **Multi-LLM Skills Generation**: Single source documentation → Multiple LLM skill formats
3. **Automated Validation**: Daily checks for syntax errors and broken links
4. **AI-Powered Triage**: Claude analyzes issues and categorizes them automatically

## Architecture

```
📁 Repository Structure
├── docs/                          # 📚 Source of Truth (Markdown)
│   └── keboola/
│       ├── 01-core-concepts.md
│       ├── 02-storage-api.md
│       └── 03-common-pitfalls.md
│
├── skills/                        # 🤖 Generated Skills (DO NOT EDIT MANUALLY)
│   ├── claude/                    # For Claude Code
│   │   └── keboola-core/
│   │       └── SKILL.md           # ← Generated from docs/
│   └── gemini/                    # For Gemini (future)
│       └── keboola-core/
│           └── skill.yaml         # ← Generated from docs/
│
├── .github/workflows/
│   ├── validate-docs.yml          # Validates docs/
│   ├── auto-triage.yml            # Self-healing triage
│   ├── propose-fix.yml            # AI-generated PRs
│   ├── sync-claude-skills.yml     # docs/ → skills/claude/
│   └── sync-gemini-skills.yml     # docs/ → skills/gemini/
│
└── scripts/generators/
    ├── claude_generator.py        # Markdown → Claude SKILL.md
    └── gemini_generator.py        # Markdown → Gemini skill.yaml
```

## How It Works

```
Developer edits docs/                    Self-healing detects issue
       │                                         │
       ▼                                         ▼
   Validate                                  Create Issue
       │                                         │
   ┌───┴────┐                                   ▼
   │        │                              Auto-Triage
   ▼        ▼                                   │
Claude   Gemini                                 ▼
Skills   Skills                            Propose Fix PR
       │        │                               │
       └────┬───┘                               ▼
            │                              Merge PR
            ▼                                   │
      Deployed                                  │
                                               └──→ Back to step 1
```

## What's NOT in This POC

❌ Connection to official `anthropic/ai-kit` repository  
❌ Production-ready plugin distribution  
❌ Full multi-LLM support (only Claude fully implemented)  
❌ Advanced conflict resolution for concurrent edits  
❌ Comprehensive test coverage  

## What IS in This POC

✅ Working self-healing loop (Issue → Triage → PR)  
✅ Documentation validation (syntax, links, code examples)  
✅ Skills generation from Markdown docs  
✅ Claude Code integration (keboola-core skill)  
✅ GitHub Actions automation  
✅ Multi-LLM architecture (foundation)  

## Xmas Challenge Success Criteria

This POC demonstrates all required functionality:

1. ✅ **Knowledge Gap Detection**: Validation finds issues automatically
2. ✅ **Automated Issue Creation**: Creates GitHub issues with context
3. ✅ **AI-Powered Triage**: Claude categorizes and prioritizes (85-95% confidence)
4. ✅ **Automated PR Generation**: Claude proposes comprehensive fixes
5. ✅ **Full Self-Healing Loop**: Issue → Triage → PR → Merge → Regenerate
6. ✅ **Continuous Improvement**: Daily validation ensures quality

## Testing the POC

### 1. Trigger Validation Manually
```bash
gh workflow run validate-docs.yml --repo ZdenekSrotyr/xmas-challenge-fork
```

### 2. Edit Documentation
```bash
# Edit a doc file
vim docs/keboola/02-storage-api.md

# Commit and push
git add docs/
git commit -m "docs: Add pagination example"
git push

# Skills automatically regenerate
```

### 3. View Generated Skills
```bash
# Claude skill
cat skills/claude/keboola-core/SKILL.md

# Gemini skill (when implemented)
cat skills/gemini/keboola-core/skill.yaml
```

## Active PRs and Issues

- [PR #3](https://github.com/ZdenekSrotyr/xmas-challenge-fork/pull/3): Stack URL documentation
- [PR #4](https://github.com/ZdenekSrotyr/xmas-challenge-fork/pull/4): Python syntax fixes
- [Issue #1](https://github.com/ZdenekSrotyr/xmas-challenge-fork/issues/1): Missing Stack URL concept
- [Issue #2](https://github.com/ZdenekSrotyr/xmas-challenge-fork/issues/2): Validation failures

## Future Work (Post-POC)

If this POC is successful, next steps would be:

1. **Upstream Integration**: Connect to official ai-kit via git subtree
2. **Production Hardening**: Add comprehensive tests, error handling
3. **Multi-LLM Expansion**: Full Gemini support, OpenAI, etc.
4. **Advanced Validation**: Semantic checks, example execution
5. **Conflict Resolution**: Handle concurrent doc edits gracefully
6. **Metrics & Monitoring**: Track self-healing effectiveness

## POC Status

- **Created**: 2025-12-16
- **Status**: ✅ Functional - Self-healing loop working end-to-end
- **Test Coverage**: Basic validation, 2 complete self-healing cycles demonstrated
- **Known Issues**: See [Issues](https://github.com/ZdenekSrotyr/xmas-challenge-fork/issues)

---

**Note**: This is experimental software created for the Keboola Xmas Challenge.  
Not intended for production use without further development.
