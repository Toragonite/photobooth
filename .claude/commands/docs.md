---
description: Browse or search project documentation
argument-hint: [topic: api|schema|errors|deploy|usecase|all]
---

Browse PhotoBooth documentation.

**Topic**: $ARGUMENTS (default: list available docs)

## Available Documentation

| Topic | File | Description |
|-------|------|-------------|
| `api` | `docs/API_SPECIFICATION.md` | REST API endpoints |
| `schema` | `docs/DATABASE_SCHEMA.md` | SQLite tables |
| `errors` | `docs/ERROR_CODES.md` | Error code reference |
| `deploy` | `docs/DEPLOYMENT.md` | Pi 5 deployment guide |
| `style` | `docs/UI_STYLE_GUIDE.md` | UI/UX guidelines |
| `testing` | `docs/TESTING_STRATEGY.md` | Test approach |
| `design` | `DESIGN.md` | Main design spec |
| `arch` | `docs/architecture/CLEAN_ARCHITECTURE.md` | Architecture |
| `entities` | `docs/entities/ENTITIES.md` | Domain entities |
| `interfaces` | `docs/interfaces/INTERFACES.md` | Ports & adapters |
| `usecase` | `docs/use-cases/INDEX.md` | Use case catalog |

## Instructions

### If no topic specified
List all available documentation files with brief descriptions.

### If specific topic
1. Read the relevant documentation file
2. Provide a summary of key points
3. Highlight sections relevant to current work
4. Offer to dive deeper into specific sections

### If "usecase"
1. Read `docs/use-cases/INDEX.md`
2. List all 24 use cases with priorities
3. Ask which use case to explore in detail

### If searching for something specific
Use grep to search across all documentation:
```bash
grep -r "search_term" docs/ DESIGN.md CLAUDE.md
```
