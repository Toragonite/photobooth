# State Management Command

Manage development state for the PhotoBooth project.

## Usage

```
/state [subcommand] [args]
```

## Subcommands

### `show` - Display Current State
Show overall development progress and current focus.

### `focus <UC-XXX>` - Set Current Focus
Set the use case you're currently working on.

### `progress` - Show Progress Summary
Display implementation progress by component.

### `debt` - Show Technical Debt
List all technical debt items.

### `blockers` - Show Blockers
List all active blockers.

### `update <UC-XXX> <status>` - Update Use Case Status
Update a use case status. Valid statuses:
- `not_started`
- `in_progress`
- `implemented`
- `tested`
- `complete`
- `blocked`

### `add-debt <severity> <description>` - Add Technical Debt
Add a new technical debt item. Severity: low, medium, high.

### `resolve-debt <TD-XXX>` - Resolve Technical Debt
Mark a technical debt item as resolved.

## State Files

- `.claude/state/development.json` - Main development state
- `.claude/state/context.json` - Session context
- `.claude/state/SCHEMA.md` - State schema documentation

## Examples

```bash
# Show current state
/state show

# Set focus to UC-001
/state focus UC-001

# Mark UC-001 as implemented
/state update UC-001 implemented

# Show all incomplete use cases
/state progress

# Add technical debt
/state add-debt medium "API endpoint needs rate limiting"
```

## State Structure

The development state tracks:
- **Use Cases**: 24 use cases with implementation status
- **Components**: Backend, frontend, infrastructure progress
- **Technical Debt**: Known issues to address
- **Blockers**: Issues preventing progress
- **Test Coverage**: Unit and integration test percentages

## Integration

This command integrates with:
- `usecase-resolver` agent - Reads state to prioritize work
- `maintenance-agent` - Monitors state for issues
- `dev-planner` - Uses state for planning
