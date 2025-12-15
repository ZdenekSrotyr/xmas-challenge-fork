# Report Issue - Smart Error Detection

When a user reports that your solution doesn't work, follow this protocol:

## Step 1: Gather Context (ALWAYS DO THIS FIRST)

Ask the user for specific details:
- "What's the exact error message you're seeing?"
- "Can you share the code you're running?"
- "What environment are you using? (local, Keboola Custom Python, etc.)"
- "What did you expect vs what actually happened?"

## Step 2: Analyze the Problem

Determine the root cause:

### User Error Indicators:
- "Permission denied" or "401/403 errors" → Check token/permissions
- "Module not found" → Missing dependency
- "Network error" or "timeout" → Environment issue
- Variables not defined → Code adaptation needed
- Wrong table name → User's specific config

**Action:** Help fix the user error. DO NOT create GitHub issue.

### Knowledge Gap Indicators:
- You don't know how to solve something
- The SKILL.md doesn't cover this scenario
- Multiple users ask the same question
- Keboola has a feature you're not aware of

**Action:** Suggest creating issue to improve knowledge base.

### Documentation Bug Indicators:
- User shows official docs contradict your information
- API endpoint has changed (v1 → v2)
- Feature works differently than you described
- Code example doesn't run even with correct setup

**Action:** Strongly recommend creating issue with evidence.

## Step 3: Attempt to Fix (2-3 tries)

Try different approaches:
1. First attempt: Fix obvious issues
2. Second attempt: Check alternative approaches
3. Third attempt: Research in Keboola docs

## Step 4: Escalation Decision

After 2-3 attempts, evaluate:

### IF User Error:
"I've helped you fix the [specific issue]. This was related to [explanation]. Let me know if you have other questions!"

### IF Knowledge Gap:
"I notice I don't have information about [topic] in my knowledge base. This would be valuable to add.

Should I create an issue so this gets documented for others? It would include:
- Your question
- The solution we found
- Context for future users"

**Wait for user confirmation before creating issue.**

### IF Documentation Bug:
"It looks like the documentation I have might be outdated. According to [official source], the correct approach is [X], but I was suggesting [Y].

I should create an issue to fix this so other users don't encounter the same problem. Should I proceed?"

**Strongly recommend, but still wait for confirmation.**

## Step 5: Create Issue (Only If Confirmed)

Use the error reporter hook:

```bash
./hooks/error-reporter.sh \
  --error-message "Clear description of the problem" \
  --context "What we were trying to do" \
  --attempted "What solutions were tried" \
  --severity [low|medium|high|critical] \
  --component "keboola-core" # or relevant component
```

## Step 6: Inform User

"I've created issue #[number] to track this. The team will review and update the knowledge base. Thanks for helping improve the documentation!"

---

## Examples

### Example 1: User Error (DO NOT REPORT)

**User:** "Your code doesn't work! I get 'Permission denied'"

**You:**
```
I see a permission error. Let's check a few things:

1. Does your token have the correct permissions?
   Check in Keboola: Settings → API Tokens

2. Is the table in a bucket you have access to?
   Try listing tables to see what you can access.

Let me help you fix this...
```

**Do NOT create issue** - this is user's environment.

---

### Example 2: Knowledge Gap (OFFER TO REPORT)

**User:** "How do I use Keboola's new AI data quality feature?"

**You:**
```
I don't have information about the AI data quality feature in my current knowledge base.

Let me check if this is a new feature... [attempts to search/research]

It looks like this is a newer feature that isn't covered yet.
Would you like me to create an issue to add documentation about this?
It would help you and other users who need this information.
```

**Wait for user confirmation, then create issue.**

---

### Example 3: Documentation Bug (STRONGLY RECOMMEND REPORTING)

**User:** "Your code uses /v1/storage/tables but I get 404. The official docs show /v2/storage/tables"

**You:**
```
You're absolutely right! The documentation I have shows the old v1 endpoint,
but Keboola has migrated to v2. This is definitely an error in my knowledge base.

I should create an issue to update this so other users don't hit the same problem.
The issue would:
- Flag the outdated endpoint in the SKILL.md
- Update all Storage API examples to use v2
- Add a note about the v1 → v2 migration

Should I create this issue?
```

**Strongly recommend, create issue when user confirms.**

---

## Key Principles

1. **ALWAYS gather details first** - Don't assume
2. **Try to fix first** - At least 2-3 attempts
3. **Distinguish user errors from knowledge gaps** - Critical!
4. **Always ask permission** - Never auto-report
5. **Be transparent** - Explain why you're suggesting to report
6. **Thank users** - They're helping improve the system

---

## DO NOT Report These:

❌ User's environment issues (permissions, network, missing packages)
❌ User's code adaptation mistakes (wrong variable names, etc.)
❌ First-time questions that you can answer
❌ Requests for features that don't exist in Keboola
❌ General Python/programming questions not specific to Keboola

## DO Report These:

✅ Information missing from SKILL.md that should be there
✅ Outdated or incorrect information in SKILL.md (with evidence)
✅ Broken links to Keboola documentation
✅ Code examples that don't work even with correct setup
✅ Patterns that multiple users struggle with
✅ New Keboola features not yet documented

---

## Usage

This command is automatically considered when users report problems. You don't need to explicitly call it - just follow the protocol above in your responses.

If you need to manually check the protocol, you can reference this command with `/report-issue`.
