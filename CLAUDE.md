# Project Instructions for Claude

## Before Completing a Task

Before finishing any session or task, check if any of the following occurred:

1. **User corrected a mistake** - You provided incorrect information that the user had to fix
2. **Knowledge gap discovered** - You didn't know about a feature, API, or pattern
3. **Documentation was unclear** - Something in the knowledge base was confusing or outdated
4. **Better pattern learned** - You discovered a more efficient way to do something

If ANY of these occurred, run `/keboola-core:capture-learning` to document the learning before completing the task.

### Example Triggers

- User says: "that's wrong", "actually it's...", "the docs say..."
- You say: "I don't have that in my knowledge", "I wasn't aware of..."
- API response differs from expected behavior
- User teaches you something new about Keboola

## Self-Healing System

This project uses a self-healing documentation system:

1. **Capture** - Use `/capture-learning` when mistakes or gaps are found
2. **Auto-Label** - Issues with `[Learning]` prefix get `auto-report` label automatically
3. **Triage** - `auto-triage` workflow analyzes and categorizes the issue
4. **Fix** - `propose-fix` workflow creates a PR with documentation updates
5. **Merge** - Changes are reviewed and merged automatically if tests pass

## Available Commands

- `/keboola-core:capture-learning` - Capture a knowledge gap or learning as a GitHub issue
