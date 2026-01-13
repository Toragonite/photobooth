#!/bin/bash
# PhotoBooth - Post-tool hook for auto-formatting edited files
# Runs after Edit/Write operations

FILE="$CLAUDE_FILE_PATH"

# Skip if no file path
if [[ -z "$FILE" ]]; then
    exit 0
fi

# Format Python files
if [[ "$FILE" == *.py ]]; then
    if command -v black &> /dev/null; then
        black "$FILE" 2>/dev/null
    fi
    if command -v isort &> /dev/null; then
        isort "$FILE" 2>/dev/null
    fi
    echo "Formatted Python file: $FILE"
fi

# Format TypeScript/JavaScript files
if [[ "$FILE" == *.ts || "$FILE" == *.tsx || "$FILE" == *.js || "$FILE" == *.jsx ]]; then
    if command -v npx &> /dev/null; then
        npx prettier --write "$FILE" 2>/dev/null
    fi
    echo "Formatted TypeScript/JavaScript file: $FILE"
fi

# Format JSON files
if [[ "$FILE" == *.json ]]; then
    if command -v npx &> /dev/null; then
        npx prettier --write "$FILE" 2>/dev/null
    fi
fi

# Format YAML files
if [[ "$FILE" == *.yml || "$FILE" == *.yaml ]]; then
    if command -v npx &> /dev/null; then
        npx prettier --write "$FILE" 2>/dev/null
    fi
fi

exit 0
