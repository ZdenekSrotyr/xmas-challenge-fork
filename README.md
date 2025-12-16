# 🧠 Self-Learning AI Knowledge System

> **A self-improving knowledge base for AI agents that learns from real user interactions**

[![GitHub Pages](https://img.shields.io/badge/docs-live-brightgreen)](https://zdeneksrotyr.github.io/xmas-challenge-fork/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

This repository implements a complete **self-healing documentation system** where AI agents (Claude, Gemini, etc.) continuously improve their knowledge by learning from user interactions. When agents encounter gaps in their knowledge, the system automatically captures those moments, analyzes them, and proposes documentation updates.

## 🎯 What Makes This Special

Unlike traditional static documentation:

- **Learns from Real Usage**: Captures actual user-agent interactions
- **AI-Powered Gap Detection**: Automatically identifies what's missing or wrong
- **Self-Healing Loop**: Proposes fixes → Creates PRs → Merges safely → Better agent
- **Multi-LLM Support**: Single source documentation generates skills for Claude, Gemini, and more
- **Zero Manual Maintenance**: Documentation evolves automatically based on real needs

## 🌐 Live Dashboard

View the knowledge base and learning dashboard:
**https://zdeneksrotyr.github.io/xmas-challenge-fork/**

Features:
- 📚 **Documentation Browser**: Browse all docs with git history
- 🧠 **Learning Dashboard**: See what the AI is learning in real-time
- 📊 **Analytics**: Track interactions, gaps identified, and improvements
- 🕐 **Timeline**: Complete change history from git

## 🏗️ Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ Uses AI agent
       ▼
┌─────────────────┐
│  Claude/Gemini  │  ← Has knowledge from docs/
└──────┬──────────┘
       │ Conversation
       ▼
┌──────────────────┐
│ Learning Capture │  ← Hook records interaction
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   AI Analyzer    │  ← Identifies knowledge gaps
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Create Issue     │  ← Proposes documentation fix
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Auto-Triage     │  ← AI categorizes & prioritizes
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Generate PR     │  ← AI writes the fix
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Auto-Merge     │  ← Safe automatic merge
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Regenerate Skills│  ← docs/ → claude/ & gemini/
└──────┬───────────┘
       │
       └──→ Better agent next time!
```

## 📁 Repository Structure

```
xmas-challenge-fork/
│
├── docs/                          # 📚 SOURCE OF TRUTH - Edit here only
│   ├── README.md
│   └── keboola/
│       ├── 01-core-concepts.md
│       ├── 02-storage-api.md
│       └── 03-common-pitfalls.md
│
├── automation/
│   ├── learning/                  # 🧠 Learning System
│   │   ├── capture.py             # Capture interactions
│   │   ├── analyzer.py            # AI gap analysis
│   │   ├── proposer.py            # Propose doc fixes
│   │   ├── feedback.py            # User satisfaction
│   │   └── data/
│   │       └── memory.db          # SQLite: interactions + learnings
│   │
│   ├── graph/                     # 📊 Knowledge Graph
│   │   ├── knowledge_graph.py     # Graph database
│   │   ├── event_handler.py       # GitHub event processor
│   │   ├── export_docs.py         # docs/ + history → JSON
│   │   ├── export_learnings.py    # memory.db → JSON
│   │   └── data/
│   │       └── graph.db           # Concepts & relationships
│   │
│   ├── web/                       # 🌐 Web UI
│   │   ├── index.html
│   │   ├── css/styles.css
│   │   ├── js/
│   │   │   ├── app.js             # Doc browser
│   │   │   └── learning.js        # Learning dashboard
│   │   └── data/
│   │       ├── docs.json          # Generated from docs/
│   │       └── learnings.json     # Generated from memory.db
│   │
│   └── scripts/                   # 🔧 Generators
│       ├── claude_generator.py    # Markdown → SKILL.md
│       └── gemini_generator.py    # Markdown → skill.yaml
│
├── .github/workflows/
│   ├── validate-docs.yml          # Validate documentation
│   ├── auto-triage.yml            # AI-powered triage
│   ├── propose-fix.yml            # Generate fix PRs
│   ├── auto-merge.yml             # 🆕 Safe auto-merge
│   ├── learn-from-interaction.yml # 🆕 Process learnings
│   ├── sync-claude.yml            # docs/ → claude/
│   ├── sync-gemini.yml            # docs/ → gemini/
│   ├── track-issues.yml           # Track in graph
│   ├── track-prs.yml              # Track in graph
│   └── deploy-ui.yml              # Deploy to GitHub Pages
│
├── .claude/hooks/
│   └── learning-capture.sh        # 🆕 Hook for capturing learnings
│
├── claude/                        # 🤖 GENERATED - DO NOT EDIT
│   ├── keboola-core/
│   ├── component-developer/
│   ├── dataapp-developer/
│   └── developer/
│
└── gemini/                        # 🤖 GENERATED - DO NOT EDIT
    └── keboola-core/
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ZdenekSrotyr/xmas-challenge-fork.git
cd xmas-challenge-fork
```

### 2. View Documentation Locally

```bash
cd automation/web
python3 -m http.server 8000
open http://localhost:8000
```

### 3. Capture Your First Learning

When using Claude Code, if you discover a knowledge gap:

```bash
./.claude/hooks/learning-capture.sh \
  "Trying to understand Storage API rate limits" \
  "Agent didn't know about rate limits" \
  "Helpful"
```

Or use the manual reporting workflow (coming soon).

### 4. View Learnings

```bash
# Export learnings to JSON
python3 automation/graph/export_learnings.py

# View in browser
open automation/web/index.html  # Click "Learning Dashboard" tab
```

## 🧠 How Learning Works

### 1. Capture Phase

**Automatic (via hook)**:
- Hook is called when agent encounters unknown territory
- Interaction is stored in `memory.db`

**Manual (coming soon)**:
- Slash command: `/report-gap "what was missing"`
- Web form on dashboard

### 2. Analysis Phase

AI analyzer (`analyzer.py`) examines the interaction:
- What concept was involved? (e.g., "Storage API")
- What type of gap? (missing_info, incorrect, outdated)
- What should be fixed?

### 3. Proposal Phase

System creates a GitHub Issue with:
- Context from real user interaction
- Proposed documentation fix
- Link to interaction in memory.db

### 4. Self-Healing Phase

Auto-triage workflow:
- AI categorizes the issue
- Assigns priority based on impact
- Triggers fix generation if confidence > 80%

Auto-fix workflow:
- AI generates documentation update
- Creates PR with changes
- Runs validation

Auto-merge workflow:
- Checks changed files are in safe paths
- Merges if all checks pass
- Triggers skill regeneration

### 5. Improvement Phase

- `sync-claude.yml` regenerates Claude skills
- `sync-gemini.yml` regenerates Gemini skills
- UI is updated with new content
- Next user gets better answer!

## 📊 Auto-Merge Safety

Auto-merge **only** works for changes in these safe paths:

✅ **Allowed**:
- `docs/` - Documentation updates
- `claude/` - Generated Claude skills
- `gemini/` - Generated Gemini skills
- `automation/web/data/` - UI data
- `automation/graph/data/` - Graph/memory databases

❌ **Not Allowed** (requires human review):
- `.github/workflows/` - Workflow changes
- `automation/learning/` - Learning system code
- `automation/scripts/` - Generator scripts
- Anything else

PRs touching forbidden paths will be labeled but not auto-merged.

## 🎯 Use Cases

### For Platform Documentation

Keep Keboola platform documentation always up-to-date based on real developer questions.

**Example:**
1. Developer asks agent: "How do I handle rate limiting in Storage API?"
2. Agent doesn't know (not in docs)
3. System captures gap
4. AI proposes: "Add rate limiting section to Storage API docs"
5. PR is auto-generated and merged
6. Next developer gets the answer immediately

### For Product Teams

Understand what users struggle with:
- Dashboard shows most common gaps
- Identifies confusing documentation
- Tracks improvement over time (user satisfaction trends)

### For AI Researchers

Study how AI agents learn:
- What types of knowledge gaps occur?
- How quickly does self-healing improve performance?
- What's the quality of AI-generated documentation fixes?

## 🛠️ Development

### Run Tests

```bash
# Test learning capture
cd automation/learning
python3 capture.py --context "test" --response "test" --feedback "5/5"

# Test gap analysis
python3 analyzer.py --interaction-id 1

# Test proposer
python3 proposer.py
```

### Generate Skills Locally

```bash
# Generate Claude skills
python3 automation/scripts/claude_generator.py \
  --input docs/keboola/ \
  --output claude/keboola-core/SKILL.md

# Generate Gemini skills
python3 automation/scripts/gemini_generator.py \
  --input docs/keboola/ \
  --output gemini/keboola-core/skill.yaml
```

### Export Data for UI

```bash
# Export documentation + git history
python3 automation/graph/export_docs.py

# Export learnings
python3 automation/graph/export_learnings.py
```

## 📝 Contributing

### Editing Documentation

**✅ DO**: Edit files in `docs/`
```bash
vim docs/keboola/02-storage-api.md
git commit -m "docs: Add rate limiting section"
```

**❌ DON'T**: Edit generated skills directly
```bash
vim claude/keboola-core/SKILL.md  # Will be overwritten!
```

### Reporting Issues

Found a knowledge gap? Create an issue:

```bash
gh issue create \
  --title "Missing: Storage API rate limits" \
  --body "When asking about rate limits, agent couldn't help" \
  --label "auto-report"
```

The system will auto-triage and propose a fix!

## 🔐 Security

- **No secrets in code**: API keys go in GitHub Secrets
- **Safe auto-merge**: Only documented safe paths
- **Human review**: Critical changes require approval
- **Audit trail**: All learnings stored with context
- **Privacy**: No PII captured in interactions

## 📈 Metrics

View real-time metrics on the dashboard:
- **Total Interactions**: How many times agents were used
- **Gaps Identified**: Knowledge gaps found
- **Auto-Fixed**: Issues resolved automatically
- **Avg Satisfaction**: User ratings (1-5 stars)
- **Time to Fix**: Gap identified → PR merged

## 🗺️ Roadmap

- [x] Learning capture system
- [x] AI gap analysis
- [x] Auto-triage workflow
- [x] Auto-merge for safe paths
- [x] Learning dashboard UI
- [ ] Slash command for manual reporting
- [ ] Embeddings for semantic gap detection
- [ ] A/B testing: old docs vs new docs
- [ ] Integration with Zep for better memory
- [ ] Support for more LLMs (OpenAI, Mistral, etc.)

## 📚 Documentation

- **[Workflows Guide](.github/WORKFLOWS.md)**: Complete workflow documentation
- **[Learning System](automation/learning/README.md)**: Technical details
- **[Live Dashboard](https://zdeneksrotyr.github.io/xmas-challenge-fork/)**: Browse docs and learnings

## 💬 FAQ

**Q: Will it auto-merge bad changes?**
A: No. Auto-merge only works for documentation in safe paths, and all changes go through validation. Critical code requires human review.

**Q: What if the AI proposes incorrect fixes?**
A: You can reject PRs, and the system learns from rejections (coming soon). Also, human review is always available.

**Q: Does it capture private data?**
A: No. Only the context necessary for improvement is captured. No PII, no secrets.

**Q: Can I use this for my own product?**
A: Yes! Fork the repo and adapt `docs/` to your domain. The learning system is generic.

## 🙏 Acknowledgments

Built with:
- [Claude Code](https://claude.com/claude-code) - AI coding assistant
- [Claude API](https://www.anthropic.com/api) - AI-powered analysis
- [GitHub Actions](https://github.com/features/actions) - Automation
- [SQLite](https://www.sqlite.org/) - Lightweight database

Inspired by:
- [Zep](https://www.getzep.com/) - Long-term memory for AI agents
- Self-healing systems in SRE
- Documentation-as-code practices

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by developers who hate outdated docs**

*Last updated: 2025-12-16*
