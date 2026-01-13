---
description: Show project status including git, dependencies, and health
argument-hint: [detail: summary|full|git|deps|docker]
---

Show PhotoBooth project status.

**Detail level**: $ARGUMENTS (default: summary)

## Instructions

### Summary (default)
Show quick overview:
1. Git branch and uncommitted changes
2. Last commit message
3. Docker container status (if running)
4. Disk space available

### Git Status
```bash
echo "=== Git Status ==="
git branch -v
git status --short
git log --oneline -5
```

### Dependencies Status
```bash
echo "=== Backend Dependencies ==="
pip list --outdated 2>/dev/null | head -10

echo "=== Frontend Dependencies ==="
cd frontend && npm outdated 2>/dev/null | head -10
```

### Docker Status
```bash
echo "=== Docker Containers ==="
docker compose ps 2>/dev/null || echo "Docker not running"

echo "=== Docker Images ==="
docker images | grep photobooth
```

### Full Status
Run all of the above checks and provide a comprehensive report.

## Output Format

Present status in a clear, organized manner:
- Use checkmarks (✅) for healthy items
- Use warnings (⚠️) for issues needing attention
- Use errors (❌) for critical problems
