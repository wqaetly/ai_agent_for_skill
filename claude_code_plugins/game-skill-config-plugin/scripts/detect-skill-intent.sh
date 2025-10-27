#!/bin/bash

# Detect Skill Configuration Intent
# This script detects if the user is asking about skill configuration
# and suggests appropriate commands

USER_PROMPT="$1"

# Convert to lowercase for matching
prompt_lower=$(echo "$USER_PROMPT" | tr '[:upper:]' '[:lower:]')

# Keywords that indicate skill configuration intent
skill_keywords=(
    "skill config"
    "skill configuration"
    "game skill"
    "create skill"
    "generate skill"
    "new skill"
    "skill json"
    "analyze skill"
    "debug skill"
    "fix skill"
    "skill balance"
    "skill timing"
    "damage skill"
    "healing skill"
    "shield skill"
)

# Check if any keyword matches
matched=false
for keyword in "${skill_keywords[@]}"; do
    if [[ "$prompt_lower" =~ $keyword ]]; then
        matched=true
        break
    fi
done

# If matched, provide helpful suggestions
if [ "$matched" = true ]; then
    echo ""
    echo "💡 Tip: I can help with skill configuration!"
    echo "   Available commands:"
    echo "   • /skill-generate - Create new skill configurations"
    echo "   • /skill-analyze - Analyze existing skills"
    echo "   • /skill-debug - Debug skill issues"
    echo ""
fi

exit 0
