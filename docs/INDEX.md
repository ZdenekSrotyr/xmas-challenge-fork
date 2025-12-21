# Documentation Index

> **Start here** - This is your guide to all documentation in this repository.

## Quick Navigation

| I want to... | Go to |
|-------------|-------|
| Understand what this repo does | [Project Overview](#project-overview) |
| Learn about Keboola platform | [Keboola Knowledge Base](#1-keboola-knowledge-base) |
| Build a Keboola component | [Component Development](#2-component-development) |
| Build a data app | [Data App Development](#3-data-app-development) |
| Understand the CI/CD automation | [System Architecture](#4-system-architecture) |
| See how workflows work | [Workflow Diagrams](workflows.md) |

---

## Project Overview

This repository is a **self-healing AI knowledge system** that:
1. Stores documentation about Keboola platform
2. Automatically generates AI skills from docs
3. Learns from user interactions to improve itself
4. Uses Claude AI to auto-fix issues

**Key principle**: Edit only in `docs/` folder. Everything else is auto-generated.

---

## Documentation Structure

```
docs/                           ← YOU ARE HERE (source of truth)
├── INDEX.md                    ← This file
├── README.md                   ← How to contribute
├── workflows.md                ← Visual workflow diagrams
└── keboola/                    ← Keboola platform knowledge
    ├── 01-core-concepts.md
    ├── 02-storage-api.md
    ├── 03-common-pitfalls.md
    ├── 04-component-development.md
    └── 05-dataapp-development.md

claude/                         ← AUTO-GENERATED (do not edit)
├── keboola-core/               ← Generated knowledge skill
├── component-developer/        ← Component building plugin
├── dataapp-developer/          ← Data app building plugin
└── developer/                  ← General dev tools

.github/                        ← GitHub workflows & config
└── workflows/                  ← CI/CD automation

automation/                     ← Backend systems
├── learning/                   ← Learning capture system
├── graph/                      ← Knowledge graph
└── web/                        ← Dashboard UI
```

---

## Reading Order by Goal

### 1. Keboola Knowledge Base

Learn about the Keboola platform:

| Order | Document | What You'll Learn |
|-------|----------|-------------------|
| 1 | [Core Concepts](keboola/01-core-concepts.md) | Stack URL, API tokens, tables, buckets, jobs |
| 2 | [Storage API](keboola/02-storage-api.md) | API reference, authentication, rate limits |
| 3 | [Common Pitfalls](keboola/03-common-pitfalls.md) | Mistakes to avoid, debugging tips |
| 4 | [Component Development](keboola/04-component-development.md) | Building components |
| 5 | [Data App Development](keboola/05-dataapp-development.md) | Building Streamlit apps |

### 2. Component Development

Build production-ready Keboola Python components:

| Order | Document | What You'll Learn |
|-------|----------|-------------------|
| 1 | [Plugin Overview](../claude/component-developer/README.md) | Available agents and use cases |
| 2 | [Getting Started](../claude/component-developer/guides/getting-started/initialization.md) | Initial setup |
| 3 | [Architecture](../claude/component-developer/guides/component-builder/architecture.md) | Component structure |
| 4 | [Workflow Patterns](../claude/component-developer/guides/component-builder/workflow-patterns.md) | Development patterns |
| 5 | [Testing](../claude/component-developer/guides/component-builder/running-and-testing.md) | Testing procedures |
| 6 | [UI Schema](../claude/component-developer/guides/ui-developer/overview.md) | Configuration forms |

**Agents available:**
- `component-builder` - Build components
- `ui-developer` - Create config schemas
- `tester` - Testing & QA
- `debugger` - Troubleshooting
- `reviewer` - Code review

### 3. Data App Development

Build Streamlit apps on Keboola:

| Order | Document | What You'll Learn |
|-------|----------|-------------------|
| 1 | [Plugin Overview](../claude/dataapp-developer/README.md) | Features and setup |
| 2 | [Quick Start](../claude/dataapp-developer/skills/dataapp-dev/QUICKSTART.md) | Get started fast |
| 3 | [Workflow Guide](../claude/dataapp-developer/skills/dataapp-dev/workflow-guide.md) | Development workflow |
| 4 | [Best Practices](../claude/dataapp-developer/skills/dataapp-dev/best-practices.md) | Recommended patterns |
| 5 | [Templates](../claude/dataapp-developer/skills/dataapp-dev/templates.md) | Ready-to-use code |

### 4. System Architecture

Understand how the self-healing CI/CD works:

| Order | Document | What You'll Learn |
|-------|----------|-------------------|
| 1 | [Workflow Diagrams](workflows.md) | Visual overview of all workflows |
| 2 | [Learning System](../automation/learning/README.md) | How learning capture works |
| 3 | [Knowledge Graph](../automation/graph/README.md) | Relationship tracking |
| 4 | [Dashboard](../automation/web/README.md) | Web UI for browsing |

---

## Confidence-Based Automation

The system uses AI confidence levels to decide actions:

| Confidence | Action | Example |
|------------|--------|---------|
| **≥90%** | Push directly to main | Typo fixes, simple updates |
| **70-89%** | Create PR for review | New sections, refactoring |
| **<70%** | Create issue for human | Complex changes, unclear requirements |

---

## Contributing

1. **Edit docs**: Only modify files in `docs/` folder
2. **Push changes**: Commit and push to main
3. **Auto-sync**: Skills regenerate automatically
4. **Report gaps**: Create issue with `auto-report` label

See [docs/README.md](README.md) for detailed guidelines.

---

## Live Resources

- **Dashboard**: https://zdeneksrotyr.github.io/xmas-challenge-fork/
- **GitHub Actions**: https://github.com/ZdenekSrotyr/xmas-challenge-fork/actions
- **Issues**: https://github.com/ZdenekSrotyr/xmas-challenge-fork/issues
