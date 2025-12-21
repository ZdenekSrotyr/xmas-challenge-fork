# Contributing to Documentation

> **This is the source of truth** - Edit only files in `docs/` folder.

## Quick Rules

| Do | Don't |
|----|-------|
| Edit files in `docs/` | Edit files in `claude/` or `gemini/` |
| Use numbered prefixes (`01-`, `02-`) | Use random file names |
| Include valid code examples | Copy-paste untested code |
| Push to main | Create feature branches for docs |

## Setup (for maintainers)

### 1. Add Anthropic API Key

Required for AI-powered workflows:

1. Get API key from https://console.anthropic.com/settings/keys
2. Go to repo Settings > Secrets and variables > Actions
3. Add secret: `ANTHROPIC_API_KEY` = `sk-ant-...`

### 2. Enable GitHub Pages

1. Go to Settings > Pages
2. Source: Deploy from branch
3. Branch: `main`, folder: `/automation/web`

## Writing Documentation

### File Structure

```
docs/
├── INDEX.md              ← Navigation (start here)
├── README.md             ← This file (how to contribute)
├── workflows.md          ← Visual workflow diagrams
└── keboola/
    ├── 01-core-concepts.md
    ├── 02-storage-api.md
    ├── 03-common-pitfalls.md
    ├── 04-component-development.md
    └── 05-dataapp-development.md
```

### Naming Convention

- Use numbers for ordering: `01-`, `02-`, `03-`
- Use kebab-case: `core-concepts.md`, not `CoreConcepts.md`
- Be descriptive: `storage-api.md`, not `api.md`

### Code Examples

Always specify language and test your code:

```markdown
```python
import os
token = os.environ["KBC_TOKEN"]  # Never hardcode!
```
```

Show both wrong and correct approaches:

```markdown
**Wrong:**
```python
url = "hardcoded.com"
```

**Correct:**
```python
url = os.environ["URL"]
```
```

## How Auto-Sync Works

```
docs/ changed → sync-claude-skills.yml → claude/keboola-core/SKILL.md
            → sync-gemini-skills.yml → gemini/keboola-core/skill.yaml
```

Skills regenerate automatically on every push to `docs/`.

## Validation

The system validates:
- Python syntax in code blocks
- Links (no 404s)
- Required fields in JSON schemas

If validation fails:
1. Issue is created automatically
2. AI proposes a fix
3. Fix is merged (if confidence ≥90%) or reviewed

## Adding New Documentation

```bash
# 1. Create file with number prefix
cat > docs/keboola/06-new-topic.md << 'EOF'
# New Topic

Content here...
EOF

# 2. Commit and push
git add docs/keboola/06-new-topic.md
git commit -m "docs: Add new topic"
git push origin main

# 3. Skills auto-regenerate (no action needed)
```

## Reporting Issues

Found a knowledge gap? Create an issue:

```bash
gh issue create \
  --title "Missing: Rate limits documentation" \
  --body "Agent didn't know about rate limits" \
  --label "auto-report"
```

The system will auto-triage and propose a fix.

## Related

- [INDEX.md](INDEX.md) - Documentation navigation
- [workflows.md](workflows.md) - Visual workflow diagrams
- [Learning System](../automation/learning/README.md) - How learning capture works
