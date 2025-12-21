# Self-Learning AI Knowledge System

[![Dashboard](https://img.shields.io/badge/dashboard-live-brightgreen)](https://zdeneksrotyr.github.io/xmas-challenge-fork/)
[![Actions](https://img.shields.io/badge/workflows-automated-blue)](https://github.com/ZdenekSrotyr/xmas-challenge-fork/actions)

A self-healing documentation system where AI agents learn from user interactions and automatically fix knowledge gaps.

## Quick Links

| Resource | Link |
|----------|------|
| **Documentation Index** | [docs/INDEX.md](docs/INDEX.md) |
| **Live Dashboard** | https://zdeneksrotyr.github.io/xmas-challenge-fork/ |
| **Workflow Diagrams** | [docs/workflows.md](docs/workflows.md) |

## What This Does

```
User asks AI → AI doesn't know → System captures gap → AI fixes docs → Better answers next time
```

- **90% autonomous**: Most issues fixed without human intervention
- **Multi-LLM**: Same docs generate Claude & Gemini skills
- **Self-healing CI/CD**: Validation failures auto-fixed by Claude

## Repository Structure

```
docs/                   ← EDIT HERE (source of truth)
├── INDEX.md            ← Start here for navigation
├── keboola/            ← Platform knowledge
└── workflows.md        ← Visual workflow diagrams

claude/                 ← AUTO-GENERATED (Claude plugins)
├── component-developer/
├── dataapp-developer/
└── keboola-core/

automation/             ← Backend systems
├── learning/           ← Interaction capture
├── graph/              ← Knowledge tracking
└── web/                ← Dashboard UI

.github/workflows/      ← CI/CD automation
```

## Getting Started

### For Users

**Use the plugins:**
```bash
claude /plugin marketplace add ZdenekSrotyr/xmas-challenge-fork
```

**Browse documentation:**
https://zdeneksrotyr.github.io/xmas-challenge-fork/

### For Contributors

1. Edit files in `docs/` only
2. Push to main
3. Skills auto-regenerate

See [docs/INDEX.md](docs/INDEX.md) for detailed guides.

### For Developers

**Run dashboard locally:**
```bash
cd automation/web && python3 -m http.server 8000
```

**Understand workflows:**
See [docs/workflows.md](docs/workflows.md) for visual diagrams.

## How Self-Healing Works

| Confidence | Action |
|------------|--------|
| ≥90% | Push fix to main |
| 70-89% | Create PR |
| <70% | Create issue |

AI reviews PRs and can iterate up to 2 times before merging or escalating.

## Documentation

| Guide | Description |
|-------|-------------|
| [docs/INDEX.md](docs/INDEX.md) | Main navigation & reading order |
| [docs/workflows.md](docs/workflows.md) | Visual workflow diagrams |
| [docs/keboola/](docs/keboola/) | Keboola platform knowledge |
| [automation/learning/README.md](automation/learning/README.md) | Learning system details |

## License

MIT - see [LICENSE](LICENSE)
