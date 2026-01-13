# Development State Schema

This document defines the state management structure for Claude Code agents working on the PhotoBooth project.

## Purpose

The state manager tracks:
- Implementation progress of use cases
- Current development context
- Technical debt and TODOs
- Test coverage status
- Known issues and blockers

## State Files

### `development.json` - Main Development State

```json
{
  "version": "1.0.0",
  "lastUpdated": "ISO-8601 timestamp",
  "currentFocus": {
    "useCase": "UC-XXX",
    "component": "backend|frontend|infrastructure",
    "description": "What is currently being worked on"
  },
  "useCases": {
    "UC-001": { "status": "not_started|in_progress|implemented|tested|complete", "files": [], "notes": "" },
    ...
  },
  "components": {
    "backend": { "progress": 0-100, "lastTouched": "timestamp" },
    "frontend": { "progress": 0-100, "lastTouched": "timestamp" },
    "infrastructure": { "progress": 0-100, "lastTouched": "timestamp" }
  },
  "technicalDebt": [
    { "id": "TD-001", "severity": "low|medium|high", "description": "", "file": "", "line": 0 }
  ],
  "blockers": [
    { "id": "BLK-001", "type": "hardware|software|design", "description": "", "resolved": false }
  ]
}
```

### `context.json` - Session Context

```json
{
  "sessionId": "uuid",
  "startedAt": "ISO-8601 timestamp",
  "recentFiles": ["list of recently touched files"],
  "recentUseCases": ["list of recently worked on use cases"],
  "pendingTasks": ["tasks to complete this session"],
  "notes": "session-specific notes"
}
```

## Use Case Status Flow

```
not_started → in_progress → implemented → tested → complete
                   ↓              ↓
              blocked ←──────────┘
```

### Status Definitions

| Status | Description |
|--------|-------------|
| `not_started` | Use case not yet begun |
| `in_progress` | Currently being implemented |
| `implemented` | Code written, not yet tested |
| `tested` | Tests written and passing |
| `complete` | Fully implemented, tested, documented |
| `blocked` | Cannot proceed due to blocker |

## Agent Commands

### Reading State

```bash
# Get current focus
cat .claude/state/development.json | jq '.currentFocus'

# Get use case status
cat .claude/state/development.json | jq '.useCases["UC-001"]'

# List incomplete use cases
cat .claude/state/development.json | jq '[.useCases | to_entries[] | select(.value.status != "complete")]'
```

### Updating State

Agents should update state after:
1. Starting work on a use case
2. Completing implementation
3. Adding/resolving technical debt
4. Encountering/resolving blockers

## Integration with Agents

| Agent | State Interaction |
|-------|-------------------|
| `dev-planner` | Reads state to prioritize work |
| `usecase-resolver` | Updates use case status |
| `api-implementer` | Updates backend progress |
| `frontend-implementer` | Updates frontend progress |
| `maintenance-agent` | Monitors technical debt |
| `test-runner` | Updates test status |
