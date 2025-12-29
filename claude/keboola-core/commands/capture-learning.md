# Capture Learning

Use this command when you discover a knowledge gap or learning during the session.

## When to Use

Call `/capture-learning` immediately when you:
- Discover something missing from documentation
- Find incorrect information in SKILL.md
- Learn something new that should be documented
- User teaches you something valuable

## How to Capture

When this command is invoked, create a GitHub issue to capture the learning:

```bash
gh issue create \
  --title "[Learning] [Brief description of what was learned]" \
  --body "## Knowledge Gap Discovered

**What was missing/incorrect:**
[Describe what information was missing or wrong]

**What we learned:**
[Describe the correct information or new knowledge]

**Context:**
[How did this come up? What was the user trying to do?]

**Suggested fix:**
[How should the documentation be updated?]

**Source/Evidence:**
[Link to official docs, API response, or user confirmation]

---
*Captured during session via /capture-learning*"
```

> **Note:** Labels are added automatically by the `auto-label-issues` workflow based on the `[Learning]` prefix in the title. This works for all users, including non-collaborators.

## Examples

### Example 1: Missing API Feature

**Trigger:** User asks about a Keboola feature you don't know

```
User: "How do I use the new AI data quality feature?"
You: "I don't have this in my knowledge base. Let me capture this learning."
```

**Action:** Create issue with title "Learning: AI data quality feature documentation needed"

### Example 2: Incorrect Information

**Trigger:** Your information contradicts official docs

```
User: "The docs say /v2/storage not /v1/storage"
You: "You're right! My knowledge is outdated. Capturing this."
```

**Action:** Create issue with title "Learning: Storage API endpoint updated to v2"

### Example 3: Better Pattern Discovered

**Trigger:** You find a better way to do something

```
You: "I just realized there's a more efficient way to do bulk uploads using the async API."
```

**Action:** Create issue with title "Learning: Async bulk upload pattern for better performance"

## Important

- Capture learnings IMMEDIATELY when discovered
- Don't wait until end of session
- Include specific details and evidence
- Tag with `auto-report` and `learning` labels
- The self-healing system will process and update docs automatically
