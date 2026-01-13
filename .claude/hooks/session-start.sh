#!/bin/bash
# PhotoBooth - Session start hook
# Displays project status when starting a new Claude Code session

echo ""
echo "📷 PhotoBooth Project"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Git information
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    CHANGES=$(git status --short 2>/dev/null | wc -l)
    LAST_COMMIT=$(git log -1 --format="%s" 2>/dev/null | head -c 50)

    echo "📂 Branch: $BRANCH"
    echo "📝 Last commit: $LAST_COMMIT"

    if [ "$CHANGES" -gt 0 ]; then
        echo "⚠️  Uncommitted changes: $CHANGES files"
    else
        echo "✅ Working directory clean"
    fi
else
    echo "⚠️  Not a git repository"
fi

echo ""

# System information
echo "💻 System Info"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Disk space
DISK_FREE=$(df -h . 2>/dev/null | tail -1 | awk '{print $4}')
echo "💾 Disk free: $DISK_FREE"

# Docker status (if available)
if command -v docker &> /dev/null; then
    CONTAINERS=$(docker ps -q 2>/dev/null | wc -l)
    echo "🐳 Docker containers running: $CONTAINERS"
fi

# Node.js version (if available)
if command -v node &> /dev/null; then
    NODE_VER=$(node --version 2>/dev/null)
    echo "📦 Node.js: $NODE_VER"
fi

# Python version (if available)
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version 2>/dev/null | cut -d' ' -f2)
    echo "🐍 Python: $PY_VER"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Available commands: /test, /build, /lint, /status, /docs, /usecase"
echo ""

exit 0
