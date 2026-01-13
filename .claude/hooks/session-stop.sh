#!/bin/bash
# PhotoBooth - Session stop hook
# Displays summary and reminders when ending a Claude Code session

echo ""
echo "📋 Session Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for uncommitted changes
if git rev-parse --git-dir > /dev/null 2>&1; then
    CHANGES=$(git status --short 2>/dev/null | wc -l)
    STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l)
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

    if [ "$CHANGES" -gt 0 ]; then
        echo "⚠️  Uncommitted changes: $CHANGES files"
        echo ""
        echo "Modified files:"
        git status --short 2>/dev/null | head -10

        if [ "$CHANGES" -gt 10 ]; then
            echo "... and $((CHANGES - 10)) more"
        fi

        echo ""
        echo "💡 Remember to commit your changes:"
        echo "   git add . && git commit -m 'your message'"
    else
        echo "✅ Working directory clean"
    fi

    # Check if ahead of remote
    AHEAD=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
    if [ "$AHEAD" -gt 0 ]; then
        echo ""
        echo "📤 $AHEAD commit(s) not pushed to remote"
        echo "💡 Run: git push origin $BRANCH"
    fi
else
    echo "⚠️  Not a git repository"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👋 Session ended. See you next time!"
echo ""

exit 0
