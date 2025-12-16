# ⚠️ POC NOTICE - Plugins Directory

## Important

The plugins in this directory are **NOT connected to the official ai-kit repository**.

This is a **Proof of Concept** for the Keboola Xmas Challenge demonstrating:
- Self-healing knowledge systems
- Multi-LLM skill generation
- Automated documentation validation

## New Architecture

The **new architecture** (POC) uses:
- `docs/` - Single source of truth (Markdown)
- `skills/` - Auto-generated skills for different LLMs
- Workflows - Auto-sync docs → skills

## Old vs New

| Aspect | Old (plugins/) | New (docs/ + skills/) |
|--------|---------------|----------------------|
| Edit location | `plugins/*/SKILL.md` | `docs/**/*.md` |
| Multi-LLM | Manual copy | Auto-generated |
| Validation | Per-plugin | Centralized |
| Self-healing | Per-plugin | Docs-level |
| Upstream sync | Git subtree | (Future work) |

## What to Use

For **POC testing**:
- ✅ Use: `skills/claude/keboola-core/` (generated from docs/)
- ❌ Don't use: `plugins/keboola-core/` (old structure)

For **production**:
- We would connect this to official ai-kit via git subtree
- See [POC-README.md](../POC-README.md) for details

## Migration Path

If POC is successful:

1. Keep `docs/` as source of truth
2. Add git subtree for ai-kit plugins
3. Merge workflow: docs/ → ai-kit plugins → upstream PR
4. Extend to other LLMs (Gemini, OpenAI, etc.)

---

**Status**: POC only - Not for production use
