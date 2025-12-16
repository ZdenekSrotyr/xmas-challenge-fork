# Knowledge Graph System

> **Automatic tracking of Issues, PRs, Documents, and Skills**

## Overview

This knowledge graph system automatically tracks relationships between:
- 📄 **Documents** - Source docs and generated skills
- 💡 **Concepts** - Keboola concepts (Storage API, Stack URL, etc.)
- 🐛 **Issues** - GitHub issues reporting gaps
- 🔀 **Pull Requests** - Fixes and improvements
- 🎯 **Skills** - Generated Claude/Gemini skills

## How It Works

### Completely Automatic! 🤖

When you create an issue or PR, GitHub workflows automatically:
1. Extract mentioned concepts and files
2. Add nodes to the graph
3. Link relationships
4. Track status changes
5. Identify affected skills

### Example Flow

```
Issue #1 created: "Missing Stack URL docs"
  ↓ [track-issues.yml triggers]
  ↓ [event_handler.py extracts concepts]
  ↓
Graph:
  Issue:1 --ABOUT--> Concept:StackURL
  Issue:1 --ABOUT--> Document:docs/keboola/01-core-concepts.md
  ↓
PR #3 created: "Add Stack URL documentation"
  ↓ [track-prs.yml triggers]
  ↓ [event_handler.py links PR to issue]
  ↓
Graph:
  Issue:1 --FIXED_BY--> PullRequest:3
  PullRequest:3 --MODIFIES--> Document:docs/keboola/01-core-concepts.md
  ↓
PR #3 merged
  ↓ [event_handler.py finds dependents]
  ↓
Graph:
  Document:docs/keboola/01-core-concepts.md --GENERATES--> Skill:claude-keboola-core
  ↓
Result: Automatically triggers Claude skill regeneration! ✨
```

## Graph Structure

### Node Types

```python
Document: {
    path: "docs/keboola/01-core-concepts.md",
    title: "Core Concepts"
}

Concept: {
    name: "StackURL"
}

Issue: {
    number: 1,
    title: "Missing Stack URL docs",
    status: "open|closed"
}

PullRequest: {
    number: 3,
    title: "Add Stack URL documentation",
    status: "open|merged|closed",
    additions: 340,
    deletions: 7
}

Skill: {
    platform: "claude",
    path: "skills/claude/keboola-core/SKILL.md"
}
```

### Relationships

```
Issue --ABOUT--> Concept
Issue --ABOUT--> Document
Issue --FIXED_BY--> PullRequest
PullRequest --MODIFIES--> Document
Document --GENERATES--> Skill
Document --EXPLAINS--> Concept
Concept --REQUIRED_BY--> Skill
```

## Usage

### View Graph Stats

```bash
cd automation/graph
python knowledge_graph.py --stats
```

Output:
```
📊 Knowledge Graph Statistics
Total nodes: 23
Total edges: 45

Nodes by type:
  Document: 8
  Concept: 7
  Issue: 3
  PullRequest: 3
  Skill: 2
```

### List Nodes

```bash
# List all issues
python knowledge_graph.py --list issues

# List all PRs
python knowledge_graph.py --list prs

# List all documents
python knowledge_graph.py --list documents
```

### Manual Tracking (Testing)

You can manually track events for testing:

```bash
# Track issue creation
echo '{"title": "Test issue", "body": "About Stack URL", "html_url": "...", "created_at": "2025-01-15T10:00:00Z", "labels": []}' > issue.json
python event_handler.py issue created 999 --data issue.json

# Track issue closure
python event_handler.py issue closed 999

# Track PR creation
echo '{"title": "Fix docs", "body": "Fixes #999", "html_url": "...", "created_at": "...", "changed_files": [{"filename": "docs/test.md"}]}' > pr.json
python event_handler.py pr created 888 --data pr.json

# Track PR merge
python event_handler.py pr merged 888
```

## GitHub Workflows

### track-issues.yml

Triggers on: `issues.opened`, `issues.closed`, `issues.reopened`

**What it does:**
1. Fetches issue data from GitHub API
2. Calls `event_handler.py issue created/closed [number]`
3. Commits updated graph.db
4. Shows stats in workflow summary

### track-prs.yml

Triggers on: `pull_request.opened`, `pull_request.closed`

**What it does:**
1. Fetches PR data + changed files
2. Calls `event_handler.py pr created/merged [number]`
3. Finds affected skills (if merged)
4. Triggers skill regeneration workflows
5. Commits updated graph.db
6. Shows affected skills in summary

## Intelligent Features

### Impact Analysis

When a document changes, the graph automatically knows:
- Which concepts it explains
- Which skills include it
- Which issues mention it
- Which PRs modified it

Example:
```python
from knowledge_graph import KnowledgeGraph

with KnowledgeGraph() as graph:
    # Find all skills affected by changing a doc
    doc_id = "Document:docs/keboola/02-storage-api.md"
    dependents = graph.find_dependents(doc_id)

    for dep_id in dependents:
        if dep_id.startswith("Skill:"):
            print(f"Need to regenerate: {dep_id}")
```

### Self-Healing Loop

The graph enables the complete self-healing loop:

```
1. Validation finds gap
   → Creates Issue in graph
   → Links to affected Concepts/Documents

2. Auto-triage categorizes
   → Updates Issue with priority
   → Identifies related issues

3. Auto-fix generates PR
   → Links PR to Issue (FIXED_BY)
   → Links PR to modified Documents (MODIFIES)

4. PR merged
   → Closes Issue
   → Finds dependent Skills
   → Triggers regeneration

5. Skills regenerated
   → Updates Skill metadata
   → Links Skill to new Documents
   → Cycle complete! ✓
```

## Database

**Location:** `automation/graph/data/graph.db`

**Type:** SQLite (lightweight, in-repo, version controlled)

**Schema:**
```sql
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,           -- "Issue:1", "Document:docs/..."
    type TEXT NOT NULL,            -- "Issue", "Document", etc.
    properties JSON NOT NULL,      -- Node-specific data
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE edges (
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    relationship TEXT NOT NULL,    -- "ABOUT", "FIXED_BY", etc.
    properties JSON,
    UNIQUE(from_id, to_id, relationship)
);
```

## Future Enhancements

### Phase 1 (Current POC)
- ✅ Automatic Issue/PR tracking
- ✅ Concept extraction
- ✅ Impact analysis
- ✅ Skill regeneration triggers

### Phase 2 (Production)
- [ ] NLP-based concept extraction
- [ ] Semantic search over graph
- [ ] Quality metrics dashboard
- [ ] Graph visualization UI

### Phase 3 (Advanced)
- [ ] LLM-powered query ("What docs explain Storage API?")
- [ ] Automatic documentation gaps detection
- [ ] Predictive skill regeneration
- [ ] Migration to Neo4j for scale

## Benefits

### For Self-Healing System

1. **Automatic**: No manual tracking needed
2. **Complete**: Full audit trail from issue → PR → regeneration
3. **Intelligent**: Knows what needs updating when docs change
4. **Efficient**: Only regenerates affected skills

### For Development

1. **Impact Analysis**: "If I change this doc, what breaks?"
2. **Gap Detection**: "Which concepts lack documentation?"
3. **Quality Metrics**: "How many issues per concept?"
4. **Traceability**: "What PRs fixed issues about Stack URL?"

### For Multi-LLM

1. **Platform Tracking**: Knows which LLMs need which skills
2. **Parallel Regeneration**: Triggers Claude + Gemini workflows
3. **Consistency**: All platforms updated from same source

---

**Status**: POC implementation
**Performance**: Suitable for 100s of nodes/edges (SQLite)
**Production**: Migrate to Neo4j for 1000s+ of nodes
