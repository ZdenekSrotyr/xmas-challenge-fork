# Documentation Source

> **⚠️ POC**: This is the single source of truth for all LLM skills

## Overview

This directory contains the **canonical documentation** for Keboola platform knowledge.
All skills for different LLMs (Claude, Gemini, etc.) are **automatically generated** from these files.

## Structure

```
docs/
└── keboola/
    ├── 01-core-concepts.md      # Fundamental concepts
    ├── 02-storage-api.md         # Storage API usage
    └── 03-common-pitfalls.md     # Common mistakes
```

## How It Works

1. **Edit docs here** - This is the only place to edit documentation
2. **Commit and push** - Push changes to main branch
3. **Auto-generate** - Workflows automatically generate skills:
   - `sync-claude-skills.yml` → `skills/claude/`
   - `sync-gemini-skills.yml` → `skills/gemini/`

## DO NOT Edit Skills Directly

```
❌ DO NOT EDIT: skills/claude/keboola-core/SKILL.md
❌ DO NOT EDIT: skills/gemini/keboola-core/skill.yaml

✅ EDIT HERE: docs/keboola/*.md
```

Skills are regenerated on every docs/ commit, so manual edits will be overwritten.

## Writing Guidelines

### File Naming
- Use numbers for ordering: `01-`, `02-`, `03-`
- Use kebab-case: `core-concepts.md`, not `CoreConcepts.md`
- Be descriptive: `storage-api.md`, not `api.md`

### Content Structure

#### Headings
```markdown
# Main Topic         (H1 - one per file)
## Section          (H2 - major sections)
### Subsection      (H3 - details)
```

#### Code Blocks
Always specify language:
```markdown
```python
import requests
# Code here
```
```

#### Examples
Show both ❌ wrong and ✅ correct:
```markdown
## Common Mistake

❌ **Wrong:**
```python
url = "hardcoded.com"
```

✅ **Correct:**
```python
url = os.environ["URL"]
```
```

### Code Quality

All Python examples must:
- Be syntactically valid
- Use environment variables for secrets
- Include error handling
- Have comments explaining key points

**Why:** The `validate-docs.yml` workflow checks all code blocks for syntax errors.

## Validation

Before committing, you can run validation locally:

```bash
# Validate all docs
python scripts/validators/markdown_validator.py docs/

# Check Python syntax
python scripts/validators/code_validator.py docs/

# Test generators
python scripts/generators/claude_generator.py \
  --input docs/keboola/ \
  --output /tmp/test-skill.md
```

## Self-Healing

If validation fails:
1. GitHub Actions creates an issue
2. Claude analyzes and categorizes it
3. Claude proposes a fix PR
4. Human reviews and merges
5. Skills automatically regenerate

## Adding New Documentation

To add a new topic:

```bash
# 1. Create new file
cat > docs/keboola/04-new-topic.md << 'EOF'
# New Topic

Content here...
EOF

# 2. Commit
git add docs/keboola/04-new-topic.md
git commit -m "docs: Add new topic"
git push

# 3. Skills auto-generate (no action needed)
```

The workflows will detect the new file and include it in the next skill generation.

## Multi-LLM Support

Each LLM gets documentation in its native format:

| LLM    | Format | Location |
|--------|--------|----------|
| Claude | Markdown | `skills/claude/keboola-core/SKILL.md` |
| Gemini | YAML | `skills/gemini/keboola-core/skill.yaml` |

The content is the same, just formatted differently.

## FAQ

### Q: Can I edit skills directly?
**A:** No. Always edit `docs/`. Skills regenerate automatically.

### Q: How long does generation take?
**A:** Usually < 30 seconds after pushing to main.

### Q: What if I break something?
**A:** The validation workflow will catch it and create an issue. The self-healing system will propose a fix.

### Q: Can I add images or diagrams?
**A:** Yes, but store them in `docs/images/` and reference with relative paths.

### Q: How do I test changes locally?
**A:** Run the generators manually (see Validation section above).

## Related Workflows

- `.github/workflows/validate-docs.yml` - Validates on every push
- `.github/workflows/sync-claude-skills.yml` - Claude skill generation
- `.github/workflows/sync-gemini-skills.yml` - Gemini skill generation
- `.github/workflows/auto-triage.yml` - Self-healing triage
- `.github/workflows/propose-fix.yml` - Self-healing PR generation

---

**Remember**: This is a POC demonstrating multi-LLM knowledge management.
In production, this would connect to upstream repositories and have more robust validation.
