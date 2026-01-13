#!/bin/bash
# PhotoBooth - Pre-tool hook for validating bash commands
# This script blocks dangerous commands before execution

# Get the command being executed
COMMAND="$CLAUDE_TOOL_INPUT"

# Define dangerous patterns
DANGEROUS_PATTERNS=(
    'rm -rf /'
    'rm -rf /*'
    '> /dev/sd'
    'mkfs\.'
    'dd if=.*of=/dev'
    ':(){ :|:& };:'
    'chmod -R 777 /'
    'mv /* /dev/null'
    'wget.*\|.*sh'
    'curl.*\|.*sh'
)

# Check for dangerous patterns
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$pattern"; then
        echo "BLOCKED: Potentially destructive command detected" >&2
        echo "Pattern matched: $pattern" >&2
        exit 2  # Exit code 2 blocks the command
    fi
done

# Block commands on main branch that could affect production
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
    if echo "$COMMAND" | grep -qE "(docker push|npm publish|pip upload)"; then
        echo "BLOCKED: Cannot publish/deploy directly from $BRANCH branch" >&2
        echo "Please create a release branch first" >&2
        exit 2
    fi
fi

# All checks passed
exit 0
