#!/bin/bash

# Validate Skill JSON Configuration
# This script validates skill JSON files after they are written or edited

FILE_PATH="$1"

# Only validate files in Assets/Skills directory
if [[ ! "$FILE_PATH" =~ Assets/Skills/.*\.json$ ]]; then
    exit 0
fi

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

echo "🔍 Validating skill configuration: $(basename "$FILE_PATH")"

# Validate JSON syntax
if ! python3 -m json.tool "$FILE_PATH" > /dev/null 2>&1; then
    echo "❌ Invalid JSON syntax in $FILE_PATH"
    echo "Please fix JSON errors before continuing."
    exit 1
fi

# Basic structure validation
required_fields=("skillName" "skillDescription" "totalDuration" "frameRate" "skillId" "tracks")
missing_fields=()

for field in "${required_fields[@]}"; do
    if ! grep -q "\"$field\"" "$FILE_PATH"; then
        missing_fields+=("$field")
    fi
done

if [ ${#missing_fields[@]} -gt 0 ]; then
    echo "⚠️  Missing required fields: ${missing_fields[*]}"
    echo "Skill configuration may not load correctly."
    exit 0
fi

# Check for common issues
warnings=()

# Check if totalDuration is reasonable (between 1 and 600 seconds at 30fps)
total_duration=$(grep -oP '"totalDuration":\s*\K\d+' "$FILE_PATH" | head -1)
if [ -n "$total_duration" ]; then
    if [ "$total_duration" -lt 30 ] || [ "$total_duration" -gt 18000 ]; then
        warnings+=("totalDuration ($total_duration frames) seems unusual")
    fi
fi

# Check if skillId follows naming convention
skill_id=$(grep -oP '"skillId":\s*"\K[^"]+' "$FILE_PATH" | head -1)
if [ -n "$skill_id" ]; then
    if [[ ! "$skill_id" =~ ^[a-z]+-[a-z]+-[a-z0-9-]+$ ]]; then
        warnings+=("skillId format should be: champion-skill-name-version (kebab-case)")
    fi
fi

# Report warnings
if [ ${#warnings[@]} -gt 0 ]; then
    echo "⚠️  Warnings:"
    for warning in "${warnings[@]}"; do
        echo "   - $warning"
    done
fi

# Success
if [ ${#warnings[@]} -eq 0 ]; then
    echo "✅ Skill configuration validated successfully"
fi

exit 0
