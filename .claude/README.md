# PhotoBooth Claude Code Agent System

This document describes how to use the Claude Code agent system for developing, maintaining, and deploying the PhotoBooth application.

---

## Table of Contents

1. [Overview](#overview)
2. [Agent Inventory](#agent-inventory)
3. [Development Workflow](#development-workflow)
4. [Agent Dependencies](#agent-dependencies)
5. [Commands Reference](#commands-reference)
6. [Skills Reference](#skills-reference)
7. [State Management](#state-management)
8. [Usage Examples](#usage-examples)

---

## Overview

The PhotoBooth project uses a multi-agent Claude Code system organized by development phase:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Development Lifecycle                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  PLANNING   │───>│ DEVELOPMENT │───>│   PRE-PR    │───>│ MAINTENANCE │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│        │                  │                  │                  │           │
│        ▼                  ▼                  ▼                  ▼           │
│  ┌───────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐   │
│  │dev-planner│      │api-impl   │      │code-qual  │      │maintenance│   │
│  │usecase-res│      │frontend   │      │           │      │           │   │
│  └───────────┘      │test-runner│      └───────────┘      └───────────┘   │
│                     │code-review│                                          │
│                     │hw-debugger│                                          │
│                     └───────────┘                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Inventory

### Planning Phase

| Agent | File | Purpose | Tools |
|-------|------|---------|-------|
| **dev-planner** | `agents/dev-planner.md` | Break down features into implementation tasks | Read, Glob, Grep, Task |
| **usecase-resolver** | `agents/usecase-resolver.md` | Map use case docs to code implementation | Read, Glob, Grep, Task, Write, Edit |

### Development Phase

| Agent | File | Purpose | Tools |
|-------|------|---------|-------|
| **api-implementer** | `agents/api-implementer.md` | FastAPI backend following Clean Architecture | Read, Write, Edit, Glob, Grep, Bash |
| **frontend-implementer** | `agents/frontend-implementer.md` | React/TypeScript components | Read, Write, Edit, Glob, Grep, Bash |
| **code-reviewer** | `agents/code-reviewer.md` | Code quality and security review | Read, Grep, Glob |
| **test-runner** | `agents/test-runner.md` | Run and analyze test results | Bash, Read, Grep |
| **hardware-debugger** | `agents/hardware-debugger.md` | Pi 5 hardware diagnostics | Bash, Read, Grep, Glob |

### Quality & Maintenance Phase

| Agent | File | Purpose | Tools |
|-------|------|---------|-------|
| **code-quality-resolver** | `agents/code-quality-resolver.md` | Pre-PR lint, type check, tests, coverage | Read, Write, Edit, Glob, Grep, Bash, Task |
| **maintenance-agent** | `agents/maintenance-agent.md` | Post-implementation code health | Read, Write, Edit, Glob, Grep, Bash, Task |

---

## Development Workflow

### 1. Planning a Feature

```
User: "I want to implement photo capture functionality"

1. Start with dev-planner:
   → Reads use case docs (UC-002)
   → Creates task breakdown
   → Identifies backend/frontend split

2. Use usecase-resolver for details:
   → Maps UC-002 to Clean Architecture layers
   → Generates file list and code stubs
   → Updates development.json state
```

### 2. Implementing the Feature

```
After planning:

1. Backend work (api-implementer):
   → Creates domain entity
   → Creates application use case
   → Creates API endpoint
   → Adds repository

2. Frontend work (frontend-implementer) [parallel]:
   → Creates page component
   → Creates custom hooks
   → Adds API service
   → Updates routes

3. Testing (test-runner):
   → Runs unit tests
   → Runs integration tests
   → Reports coverage
```

### 3. Pre-PR Quality Check

```
Before creating PR:

1. Run code-quality-resolver:
   → Formatting (black, prettier)
   → Linting (flake8, eslint)
   → Type check (mypy, tsc)
   → Tests (pytest, vitest)
   → Coverage (≥80%)
   → Security scan (bandit, npm audit)

2. Use code-reviewer for manual review:
   → Security vulnerabilities
   → Performance issues
   → Best practices
```

### 4. Post-Implementation Maintenance

```
After feature is deployed:

1. Run maintenance-agent periodically:
   → Code health monitoring
   → Dependency updates
   → Performance analysis
   → Documentation sync
   → Technical debt tracking
```

---

## Agent Dependencies

```
                    ┌─────────────────┐
                    │   dev-planner   │
                    └────────┬────────┘
                             │ spawns
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │api-implmtr │  │frontend-imp│  │test-runner │
     └────────────┘  └────────────┘  └────────────┘
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    ┌─────────────────┐
                    │  code-reviewer  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │code-quality-res │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ maintenance-agt │◄──── periodic
                    └─────────────────┘
```

### Cross-Agent References

| Agent | References | Referenced By |
|-------|------------|---------------|
| dev-planner | test-runner, code-reviewer, hardware-debugger | - |
| usecase-resolver | development.json state | maintenance-agent |
| api-implementer | Clean Architecture patterns | dev-planner |
| frontend-implementer | Component patterns | dev-planner |
| code-reviewer | - | dev-planner, maintenance-agent |
| test-runner | - | dev-planner, maintenance-agent |
| hardware-debugger | hardware-integration skill | dev-planner, maintenance-agent |
| code-quality-resolver | - | - |
| maintenance-agent | code-reviewer, test-runner, hardware-debugger, usecase-resolver | - |

---

## Commands Reference

| Command | File | Description | Usage |
|---------|------|-------------|-------|
| `/test` | `commands/test.md` | Run test suites | `/test [backend\|frontend\|all]` |
| `/build` | `commands/build.md` | Build application | `/build [dev\|prod]` |
| `/lint` | `commands/lint.md` | Run linters | `/lint [--fix]` |
| `/status` | `commands/status.md` | Project status | `/status` |
| `/docs` | `commands/docs.md` | Browse documentation | `/docs [topic]` |
| `/usecase` | `commands/usecase.md` | View use case | `/usecase UC-001` |
| `/state` | `commands/state.md` | Manage dev state | `/state [show\|focus\|progress]` |
| `/pre-pr` | `commands/pre-pr.md` | Pre-PR checks | `/pre-pr [--quick\|--fix]` |

---

## Skills Reference

Skills provide domain knowledge that auto-activates based on keywords.

| Skill | Directory | Keywords | Purpose |
|-------|-----------|----------|---------|
| **hardware-integration** | `skills/hardware-integration/` | camera, gpio, raspberry, pi5, usb | Pi 5 hardware knowledge |
| **print-system** | `skills/print-system/` | print, cups, selphy, paper, ink | CUPS/printer configuration |
| **deployment** | `skills/deployment/` | deploy, docker, systemd, production | Deployment procedures |

### Skill Auto-Activation

When you mention keywords, skills automatically provide relevant context:

```
User: "The camera isn't working"
→ hardware-integration skill activates
→ Provides camera troubleshooting procedures
→ References getUserMedia API, Safari settings
```

---

## State Management

### State Files

| File | Purpose |
|------|---------|
| `state/development.json` | Use case status, component progress, tech debt |
| `state/context.json` | Session context, recent files |
| `state/SCHEMA.md` | State structure documentation |

### Use Case Status Flow

```
not_started ──► in_progress ──► implemented ──► tested ──► complete
     │               │               │             │
     │               │               │             └── All tests pass
     │               │               └── Code written, needs testing
     │               └── Currently being developed
     └── Not yet started
```

### Tracking Progress

Use the `/state` command:

```bash
# View overall progress
/state progress

# Focus on specific use case
/state focus UC-002

# Update status
/state update UC-002 implemented

# View technical debt
/state debt
```

---

## Usage Examples

### Example 1: Implementing a New Feature

```
User: Implement photo capture (UC-002)

Step 1 - Plan
> Use dev-planner to analyze UC-002 and create task breakdown

Step 2 - Resolve Use Case
> Use usecase-resolver to map UC-002 to code structure

Step 3 - Backend Implementation
> Use api-implementer to create:
  - backend/app/domain/entities/photo.py
  - backend/app/application/use_cases/capture_photo.py
  - backend/app/adapters/api/routes/photo.py

Step 4 - Frontend Implementation (parallel)
> Use frontend-implementer to create:
  - frontend/src/pages/CapturePage.tsx
  - frontend/src/components/camera/CameraView.tsx
  - frontend/src/hooks/useCamera.ts

Step 5 - Testing
> Use test-runner to run tests
> Fix any failures

Step 6 - Quality Check
> Run /pre-pr to validate all quality gates

Step 7 - Update State
> /state update UC-002 complete
```

### Example 2: Pre-PR Quality Check

```
User: Check code quality before PR

> /pre-pr

Running quality checks...

[1/6] Formatting............ ✅ PASS
[2/6] Linting............... ❌ FAIL
      - backend/app/api/routes/photo.py:45: line too long
[3/6] Type Check............ ✅ PASS
[4/6] Unit Tests............ ✅ 47/47 passed
[5/6] Coverage.............. ✅ 84.2%
[6/6] Security.............. ✅ No vulnerabilities

Result: ❌ NEEDS FIXES

To auto-fix formatting issues:
> /pre-pr --fix
```

### Example 3: Hardware Troubleshooting

```
User: Printer not responding

Step 1 - Use hardware-debugger:
> Check USB connection
> Check CUPS status
> Check printer queue

Step 2 - Reference print-system skill:
> CUPS configuration
> Canon Selphy CP1500 specifics
> Paper/ink status checks
```

### Example 4: Maintenance Check

```
User: Run weekly maintenance

> Use maintenance-agent

Results:
- Code Health: 92/100
- Dependencies: 3 outdated (minor versions)
- Security: 0 vulnerabilities
- Tech Debt: 5 items (2 high priority)

Recommendations:
1. Update fastapi 0.104.0 → 0.109.0
2. Fix complexity in composite_generator.py
3. Add missing docstrings in photo_service.py
```

---

## Configuration

### Settings (settings.json)

```json
{
  "permissions": {
    "allow": ["Read(.claude/**)", "Write(.claude/state/**)"],
    "deny": ["Read(.env)"],
    "ask": ["Bash(sudo *)"]
  },
  "hooks": {
    "SessionStart": ["Show project status"],
    "PostToolUse": ["Format code on write"],
    "Stop": ["Show uncommitted changes"]
  }
}
```

### Hooks

| Hook | Trigger | Action |
|------|---------|--------|
| SessionStart | Claude session begins | Show branch, status, disk space |
| PreToolUse | Before Bash commands | Block destructive commands |
| PostToolUse | After Write/Edit | Auto-format Python/TypeScript |
| Stop | Session ends | Show uncommitted changes |

---

## Best Practices

### 1. Start with Planning
Always use `dev-planner` or `usecase-resolver` before jumping into implementation.

### 2. Update State Frequently
Keep `development.json` updated to track progress across sessions.

### 3. Run Quality Checks Early
Use `/pre-pr --quick` during development, full `/pre-pr` before creating PR.

### 4. Use Parallel Agents
Backend and frontend implementation can run in parallel after planning.

### 5. Track Technical Debt
Use maintenance-agent to track and prioritize debt items.

---

## Troubleshooting

### Agent Not Found
Check that the agent file exists in `.claude/agents/` with correct YAML frontmatter.

### Skill Not Activating
Verify keywords in skill's `auto-activation-keywords` match your query.

### State File Corrupted
Reset state:
```bash
cp .claude/state/SCHEMA.md /tmp/
rm .claude/state/*.json
# Recreate from SCHEMA.md template
```

### Hook Failing
Check hook command syntax in `settings.json`. Test command manually in terminal.

---

## File Structure

```
.claude/
├── README.md                 # This file
├── settings.json             # Permissions, hooks, env vars
├── agents/
│   ├── dev-planner.md        # Feature planning
│   ├── usecase-resolver.md   # Use case → code mapping
│   ├── api-implementer.md    # Backend development
│   ├── frontend-implementer.md # Frontend development
│   ├── code-reviewer.md      # Code review
│   ├── code-quality-resolver.md # Pre-PR quality
│   ├── test-runner.md        # Test execution
│   ├── hardware-debugger.md  # Hardware issues
│   └── maintenance-agent.md  # Post-impl maintenance
├── commands/
│   ├── test.md               # /test command
│   ├── build.md              # /build command
│   ├── lint.md               # /lint command
│   ├── status.md             # /status command
│   ├── docs.md               # /docs command
│   ├── usecase.md            # /usecase command
│   ├── state.md              # /state command
│   └── pre-pr.md             # /pre-pr command
├── skills/
│   ├── hardware-integration/
│   │   └── SKILL.md          # Pi 5, camera, GPIO
│   ├── print-system/
│   │   └── SKILL.md          # CUPS, Canon Selphy
│   └── deployment/
│       └── SKILL.md          # Docker, systemd
├── state/
│   ├── SCHEMA.md             # State structure docs
│   ├── development.json      # Use case progress
│   └── context.json          # Session context
└── hooks/
    └── (hook scripts)
```
