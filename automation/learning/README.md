# Learning System for Self-Improving AI Agents

**A complete system for capturing interactions, analyzing knowledge gaps, and continuously improving AI agent capabilities.**

## Overview

This learning system enables AI agents (like Claude Code) to learn from their interactions with users and automatically improve their knowledge base. When the agent encounters gaps in its knowledge or makes mistakes, the system captures these interactions, analyzes them, proposes fixes, and creates GitHub issues for documentation updates.

## Architecture

The learning system consists of four main components:

### 1. Capture (`capture.py`)
Records all interactions between users and the AI agent in a SQLite database.

**Captures:**
- User context (what the user asked)
- Agent response (what the agent said)
- User feedback (ratings, comments)
- Timestamp and metadata

**Database schema:**
```sql
interactions (
    id, timestamp, user_context, agent_response,
    user_feedback, identified_gap, created_issue_id
)

learnings (
    id, interaction_id, concept, gap_type,
    proposed_fix, status
)
```

### 2. Analyzer (`analyzer.py`)
Uses AI (Claude API) to analyze interactions and identify knowledge gaps.

**Identifies:**
- Missing information in documentation
- Incorrect or outdated information
- Common confusion patterns
- Frequently asked questions not covered

**Gap types:**
- `missing_info` - Documentation doesn't cover this topic
- `incorrect_info` - Documentation is wrong or outdated
- `unclear_info` - Documentation exists but is confusing
- `missing_example` - Needs a code example

### 3. Proposer (`proposer.py`)
Generates documentation update proposals from identified learnings.

**Creates:**
- GitHub issues for documentation gaps
- Specific proposed fixes
- Priority based on frequency and impact
- Links back to original interactions

### 4. Feedback (`feedback.py`)
Tracks user satisfaction to measure improvement over time.

**Collects:**
- 1-5 star ratings
- Optional comments
- Patterns in low-rated interactions
- Improvement trends

## Installation

### Prerequisites

- Python 3.11+
- SQLite (included with Python)
- Git repository with GitHub Actions enabled

### Setup

1. **Create the learning directory structure:**
```bash
mkdir -p automation/learning/data
cd automation/learning
```

2. **Make scripts executable:**
```bash
chmod +x capture.py analyzer.py proposer.py feedback.py
```

3. **Initialize the database:**
```bash
./capture.py --context "test" --response "test"
```

This will create `data/memory.db` with the proper schema.

4. **Install the Claude Code hook:**
```bash
mkdir -p .claude/hooks
cp learning-capture.sh .claude/hooks/
chmod +x .claude/hooks/learning-capture.sh
```

5. **Set up GitHub Actions:**
```bash
# Add your Anthropic API key to GitHub secrets
gh secret set ANTHROPIC_API_KEY

# The workflows are already in .github/workflows/
```

## Usage

### Manual Capture

Record an interaction manually:

```bash
./capture.py \
    --context "How do I read a table from Keboola Storage?" \
    --response "Use the Storage API with GET /v2/storage/tables/{tableId}/data" \
    --feedback "User was confused about authentication"
```

### Via Hook

The hook automatically captures interactions when Claude Code is used:

```bash
# This happens automatically when configured
.claude/hooks/learning-capture.sh \
    "User question here" \
    "Agent response here" \
    "Optional feedback"
```

### Analyze Interactions

Process an interaction to identify gaps:

```bash
./analyzer.py --interaction-id 42
# Output: ✅ Identified gap: Storage API authentication
```

### Get Pending Learnings

See what documentation updates are needed:

```bash
./proposer.py
# Output:
# Learning #1: Storage API - Add authentication examples
# Learning #2: Job polling - Clarify timeout behavior
# Learning #3: Input mapping - Add visual diagram
```

### Add Feedback

Record user satisfaction:

```bash
./feedback.py \
    --interaction-id 42 \
    --rating 4 \
    --comment "Helpful but needed more details"
```

### Trigger GitHub Workflow

Process a specific interaction via GitHub Actions:

```bash
gh workflow run learn-from-interaction.yml \
    -f interaction_id=42
```

## Workflows

### Auto-merge Workflow

Automatically merges documentation PRs that meet safety criteria:

**Triggers:**
- PR opened by github-actions bot
- PR with "auto-merge" label
- PR title starts with `docs:`, `chore:`, or `style:`

**Safety checks:**
- Only merges changes to docs/ and .github/
- Verifies no code changes
- Requires all checks to pass
- Squash merges and deletes branch

**Configuration:** `.github/workflows/auto-merge.yml`

### Learn from Interaction Workflow

Processes captured interactions to identify and propose fixes:

**Triggers:**
- Manual workflow dispatch with interaction ID

**Steps:**
1. Analyze interaction using Claude API
2. Identify knowledge gaps
3. Generate proposed fixes
4. Create GitHub issues (when implemented)

**Configuration:** `.github/workflows/learn-from-interaction.yml`

## Database Schema

### Interactions Table

Stores all captured interactions:

```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- ISO 8601 timestamp
    user_context TEXT,                    -- User's question/request
    agent_response TEXT,                  -- Agent's answer
    user_feedback TEXT,                   -- User's rating/comment
    identified_gap INTEGER DEFAULT 0,     -- 1 if gap found
    created_issue_id INTEGER,             -- GitHub issue number
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Learnings Table

Stores identified knowledge gaps:

```sql
CREATE TABLE learnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_id INTEGER,               -- FK to interactions
    concept TEXT NOT NULL,                -- What concept has the gap
    gap_type TEXT,                        -- missing_info, incorrect_info, etc.
    proposed_fix TEXT,                    -- Suggested documentation update
    status TEXT DEFAULT 'pending',        -- pending, issued, fixed
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interaction_id) REFERENCES interactions(id)
);
```

## Integration with Claude Code

### Hook Configuration

Create `.claude/hooks/config.json`:

```json
{
  "hooks": {
    "after_response": {
      "command": ".claude/hooks/learning-capture.sh",
      "args": ["{{user_message}}", "{{agent_response}}"]
    }
  }
}
```

### Automatic Capture

When Claude Code responds to a user:
1. Hook captures the interaction
2. Stores in SQLite database
3. Returns interaction ID
4. Optionally triggers analysis

### Privacy Considerations

- All data stored locally in `data/memory.db`
- No automatic upload to external services
- GitHub issues only created with explicit consent
- User feedback is optional
- Can be disabled by removing the hook

## Metrics & Analytics

### Query Examples

**Most common gaps:**
```sql
SELECT concept, COUNT(*) as frequency
FROM learnings
WHERE status = 'pending'
GROUP BY concept
ORDER BY frequency DESC
LIMIT 10;
```

**Average satisfaction over time:**
```sql
SELECT
    DATE(created_at) as date,
    AVG(CAST(SUBSTR(user_feedback, 9, 1) AS INTEGER)) as avg_rating
FROM interactions
WHERE user_feedback LIKE 'Rating:%'
GROUP BY date
ORDER BY date DESC;
```

**Gap resolution rate:**
```sql
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM learnings
GROUP BY status;
```

## AI-Powered Analysis

### Current Implementation

The analyzer currently uses a mock implementation for testing:

```python
def analyze_interaction(interaction_id):
    """Use AI to analyze if interaction revealed a gap."""
    # TODO: Call Claude API to analyze
    return {
        "has_gap": True,
        "concept": "Storage API",
        "gap_type": "missing_info",
        "proposed_fix": "Add section about rate limiting"
    }
```

### Production Implementation

To enable real AI analysis:

1. **Install Anthropic SDK:**
```bash
pip install anthropic
```

2. **Set API key:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

3. **Update analyzer.py:**
```python
import anthropic
import os

def analyze_interaction(interaction_id):
    """Use Claude to analyze if interaction revealed a gap."""

    # Fetch interaction from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT user_context, agent_response, user_feedback FROM interactions WHERE id = ?",
        (interaction_id,)
    )
    interaction = cursor.fetchone()
    conn.close()

    if not interaction:
        return {"has_gap": False}

    # Call Claude API
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-5-20251101",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Analyze this interaction to identify knowledge gaps:

User asked: {interaction[0]}
Agent responded: {interaction[1]}
User feedback: {interaction[2] or "None"}

Does this reveal a gap in the documentation? If yes, provide:
1. The concept that needs improvement
2. The type of gap (missing_info, incorrect_info, unclear_info, missing_example)
3. A specific proposed fix

Respond in JSON format:
{{
    "has_gap": true/false,
    "concept": "...",
    "gap_type": "...",
    "proposed_fix": "..."
}}
"""
        }]
    )

    # Parse response
    import json
    return json.loads(message.content[0].text)
```

### Analysis Prompts

The system uses specialized prompts for different gap types:

**Missing Information:**
```
The documentation doesn't cover X. Users are asking about X.
Proposed fix: Add section explaining X with examples.
```

**Incorrect Information:**
```
The documentation says X, but it should say Y.
This is causing user confusion and errors.
Proposed fix: Update section to correct the information.
```

**Unclear Information:**
```
The documentation covers X, but users don't understand it.
Multiple users are asking follow-up questions.
Proposed fix: Rewrite section with clearer explanation and examples.
```

**Missing Examples:**
```
The documentation explains X conceptually but lacks code examples.
Users are asking "how do I actually do this?"
Proposed fix: Add working code example demonstrating X.
```

## Self-Healing Loop

The complete self-improvement cycle:

```
1. User interacts with Claude Code
   └─> Hook captures interaction
       └─> Stored in database

2. Analyzer processes interaction
   └─> AI identifies knowledge gap
       └─> Learning record created

3. Proposer generates fix
   └─> GitHub issue created
       └─> Includes proposed documentation update

4. Human reviews and merges
   └─> Documentation updated
       └─> Future interactions improve

5. Metrics track improvement
   └─> Satisfaction scores increase
       └─> Fewer duplicate questions
           └─> System continuously improves
```

### Success Metrics

Track these KPIs to measure system effectiveness:

- **Gap identification rate:** % of interactions with gaps identified
- **Fix implementation rate:** % of identified gaps that get fixed
- **Time to fix:** Average days from gap identification to fix merge
- **Satisfaction improvement:** User rating trend over time
- **Question reduction:** Decrease in repeated questions

## Troubleshooting

### Database locked error

```bash
# Check for other processes using the database
lsof data/memory.db

# Close connections and retry
```

### Hook not triggering

```bash
# Verify hook is executable
ls -l .claude/hooks/learning-capture.sh

# Check hook configuration
cat .claude/hooks/config.json

# Test manually
.claude/hooks/learning-capture.sh "test" "test"
```

### Analysis failing

```bash
# Check API key is set
echo $ANTHROPIC_API_KEY

# Test analyzer manually
./analyzer.py --interaction-id 1

# Check database has interactions
sqlite3 data/memory.db "SELECT COUNT(*) FROM interactions;"
```

### No learnings generated

```bash
# Check interactions were captured
./proposer.py

# Verify analyzer ran
sqlite3 data/memory.db "SELECT * FROM learnings;"

# Run analysis manually
./analyzer.py --interaction-id 1
```

## Best Practices

### 1. Regular Analysis

Run the analyzer periodically to stay on top of gaps:

```bash
# Analyze all new interactions
sqlite3 data/memory.db "SELECT id FROM interactions WHERE identified_gap = 0;" | \
    while read id; do
        ./analyzer.py --interaction-id $id
    done
```

### 2. Prioritize High-Frequency Gaps

Focus on gaps that affect many users:

```bash
# Get top 10 most common gaps
./proposer.py | head -10
```

### 3. Close the Loop

After fixing a gap:

```bash
# Mark as fixed in database
sqlite3 data/memory.db \
    "UPDATE learnings SET status = 'fixed' WHERE id = 42;"
```

### 4. Collect Feedback

Encourage users to rate interactions:

```bash
# Add rating prompt to Claude responses
echo "Was this helpful? Rate 1-5: "
read rating
./feedback.py --interaction-id $LAST_ID --rating $rating
```

### 5. Monitor Trends

Watch for patterns in gaps over time:

```bash
# Generate weekly report
sqlite3 data/memory.db "
    SELECT
        strftime('%Y-W%W', created_at) as week,
        COUNT(*) as gaps_identified
    FROM learnings
    GROUP BY week
    ORDER BY week DESC
    LIMIT 12;
"
```

## Advanced Usage

### Custom Gap Types

Add your own gap types:

```python
# In analyzer.py
GAP_TYPES = [
    "missing_info",
    "incorrect_info",
    "unclear_info",
    "missing_example",
    "outdated_info",      # NEW
    "missing_diagram",    # NEW
    "wrong_terminology"   # NEW
]
```

### Bulk Processing

Process many interactions at once:

```bash
# Analyze last 100 interactions
sqlite3 data/memory.db \
    "SELECT id FROM interactions WHERE identified_gap = 0 LIMIT 100;" | \
    xargs -I {} ./analyzer.py --interaction-id {}
```

### Export for Analysis

Export data for external analysis:

```bash
# Export to CSV
sqlite3 -header -csv data/memory.db \
    "SELECT * FROM learnings;" > learnings.csv

# Export to JSON
sqlite3 data/memory.db \
    "SELECT json_group_array(json_object(
        'id', id,
        'concept', concept,
        'gap_type', gap_type
    )) FROM learnings;" > learnings.json
```

### Integration with External Tools

Send learnings to external systems:

```python
# In proposer.py
import requests

def send_to_slack(learning):
    """Post learning to Slack channel."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    requests.post(webhook_url, json={
        "text": f"New learning identified: {learning['concept']}"
    })

def send_to_jira(learning):
    """Create JIRA ticket for learning."""
    # Implementation here
    pass
```

## Security Considerations

### Data Privacy

- Interactions may contain sensitive information
- Store database in a secure location
- Encrypt sensitive fields if needed
- Implement access controls

### API Key Security

```bash
# Never commit API keys
echo "ANTHROPIC_API_KEY=*" >> .gitignore

# Use environment variables
export ANTHROPIC_API_KEY="sk-..."

# Or use a secrets manager
gh secret set ANTHROPIC_API_KEY
```

### Rate Limiting

Implement rate limiting for API calls:

```python
import time
from functools import wraps

def rate_limit(max_calls_per_minute):
    def decorator(func):
        calls = []

        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if now - c < 60]

            if len(calls) >= max_calls_per_minute:
                sleep_time = 60 - (now - calls[0])
                time.sleep(sleep_time)

            calls.append(time.time())
            return func(*args, **kwargs)

        return wrapper
    return decorator

@rate_limit(max_calls_per_minute=50)
def analyze_interaction(interaction_id):
    # Analysis logic here
    pass
```

## Performance Optimization

### Database Indexing

```sql
-- Add indexes for common queries
CREATE INDEX idx_interactions_gap ON interactions(identified_gap);
CREATE INDEX idx_learnings_status ON learnings(status);
CREATE INDEX idx_learnings_concept ON learnings(concept);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp);
```

### Batch Processing

Process interactions in batches:

```python
def analyze_batch(interaction_ids, batch_size=10):
    """Analyze interactions in batches."""
    for i in range(0, len(interaction_ids), batch_size):
        batch = interaction_ids[i:i+batch_size]
        for interaction_id in batch:
            analyze_interaction(interaction_id)
        time.sleep(1)  # Rate limiting
```

### Caching

Cache common analysis results:

```python
import json
from functools import lru_cache

@lru_cache(maxsize=1000)
def analyze_interaction_cached(interaction_id):
    """Cached version of analyze_interaction."""
    return analyze_interaction(interaction_id)
```

## Cost Analysis

### Expected Costs

**Anthropic API (Claude Sonnet 4.5):**
- Input: $3 per million tokens
- Output: $15 per million tokens
- Average analysis: ~500 input + 100 output tokens
- Cost per analysis: ~$0.003

**GitHub Actions:**
- 2,000 free minutes per month
- Workflows use <5 minutes each
- Effectively free for most usage

**Storage:**
- SQLite database: ~1MB per 10,000 interactions
- Effectively free

**Total monthly cost (100 interactions/month):**
- API: $0.30
- Storage: $0.00
- GitHub Actions: $0.00
- **Total: ~$0.30/month**

### ROI Calculation

**Time saved:**
- Average 15 minutes per gap fixed manually
- 10 gaps identified per month
- **Time saved: 2.5 hours/month**

**Value at $50/hour:**
- **$125/month saved**

**ROI: 400:1**

## Contributing

### Adding New Features

1. Create feature branch
2. Add tests
3. Update documentation
4. Submit PR

### Reporting Issues

Use the GitHub issue template:
```yaml
name: Learning System Issue
about: Report a problem with the learning system
labels: learning-system
```

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [Full docs](./docs/)
- Slack: #ai-learning-system

## Changelog

### v1.0.0 (2025-12-16)
- Initial release
- Basic capture, analyze, propose, feedback workflow
- SQLite database backend
- GitHub Actions integration
- Auto-merge capability

### Planned Features
- Real-time analysis
- Web dashboard
- Slack/Discord integration
- Multi-language support
- A/B testing for prompts

---

Built with Claude Code to continuously improve Claude Code.
