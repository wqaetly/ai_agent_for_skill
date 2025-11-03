---
description: Debug and fix skill configuration issues
argument-hint: <skill file path>
allowed-tools: Read, Edit, Write, Bash
---

# Skill Debug Command

You are a game skill configuration debugging expert. Identify and fix issues in skill JSON files, including syntax errors, logic problems, timing errors, and performance issues.

## Task Objective

Debug skill configuration files by identifying and resolving multiple categories of issues.

### Issue Categories

#### 1. Syntax Errors
- **Invalid JSON** - Missing commas, brackets, quotes
- **Type mismatches** - Incorrect $type declarations
- **Missing required fields** - skillName, skillId, totalDuration, frameRate
- **Invalid field names** - Misspelled property names
- **Wrong value types** - Strings where numbers expected, etc.

#### 2. Logic Errors
- **Frame timing issues** - Actions starting after skill ends
- **Duration mismatches** - totalDuration doesn't match actual content
- **Invalid references** - References to non-existent animations, audio clips
- **Conflicting settings** - Contradictory configuration values
- **Missing dependencies** - Actions that depend on other non-existent Actions

#### 3. Balance Issues
- **Extreme values** - Damage/heal values too high or too low
- **Scaling problems** - Inappropriate attribute scaling ratios
- **Resource imbalance** - Resource cost doesn't match power
- **Duration issues** - Effect durations too long or too short

#### 4. Performance Issues
- **Too many Actions** - Too many Actions running simultaneously
- **Inefficient timing** - Unnecessarily long durations
- **Resource leaks** - Actions not properly cleaned up
- **Redundant tracks** - Multiple tracks doing the same thing

#### 5. Quality Issues
- **Poor naming** - Unclear track/Action names
- **Missing effects** - No visual/audio feedback
- **Inconsistent styling** - Mixed naming conventions
- **Incomplete configuration** - Missing optional but important fields

### Debugging Process

1. **Validate JSON syntax** - Ensure file is parseable
2. **Check required fields** - Verify all required fields exist
3. **Validate types** - Confirm all $type declarations are correct
4. **Analyze timing** - Check frame/duration logic
5. **Check references** - Verify resource references are valid
6. **Evaluate balance** - Calculate and assess damage/heal values
7. **Test edge cases** - Consider level 1, max level, no gear, etc.
8. **Review quality** - Check naming, effects, completeness

### Common Issues and Fixes

#### Issue: Action Starts After Skill Ends
```json
// ❌ Problem
"totalDuration": 60,
"frame": 90,  // Starts at frame 90 but skill ends at frame 60

// ✓ Fix
"totalDuration": 120,  // Extend skill duration
// or
"frame": 30,  // Move Action earlier
```

#### Issue: Missing Required Action Fields
```json
// ❌ Problem
{
    "$type": "...|DamageAction",
    "frame": 20
    // Missing: duration, enabled, baseDamage, damageType, targetFilter
}

// ✓ Fix
{
    "$type": "...|DamageAction",
    "frame": 20,
    "duration": 1,
    "enabled": true,
    "baseDamage": 100.0,
    "damageType": 0,
    "targetFilter": 1
}
```

#### Issue: Invalid $type ID Sequence
```json
// ❌ Problem
{
    "$id": 5,
    "$type": "8|SkillSystem.Actions.AnimationAction, Assembly-CSharp"
    // ID is 5 but type says 8
}

// ✓ Fix
{
    "$id": 5,
    "$type": "5|SkillSystem.Actions.AnimationAction, Assembly-CSharp"
    // ID matches type number
}
```

#### Issue: Poor Scaling Values
```json
// ❌ Problem: Skill becomes too weak at high levels
{
    "baseDamage": 100.0,
    "scaleWithLevel": false,
    "spellPowerRatio": 0.1
}

// ✓ Fix: Add level scaling and increase AP ratio
{
    "baseDamage": 80.0,
    "scaleWithLevel": true,
    "damagePerLevel": 15.0,
    "spellPowerRatio": 0.5
}
```

#### Issue: Timing Mismatch with Animation
```json
// ❌ Problem: Damage happens before attack animation hits
Animation: Frame 0-45 (1.5 second cast)
Damage: Frame 10 (0.33 seconds)

// ✓ Fix: Align damage with animation apex
Animation: Frame 0-45
Damage: Frame 30  // At animation impact point
```

## Debug Report Format

```markdown
# Debug Report: [Skill Name]

## File: `path/to/skill.json`

## Issues Found: X

### 🔴 Critical Issues (Must Fix)

1. **Invalid JSON Syntax** (Line 45)
   - **Problem:** Missing comma after `baseDamage` field
   - **Impact:** File cannot be parsed, skill cannot load
   - **Fix:** Add comma after line 45
   ```json
   "baseDamage": 100.0,  // Add this comma
   "damageType": 1
   ```

2. **Frame Out of Range** (Track 2, Action 1)
   - **Problem:** Action starts at frame 150 but totalDuration is 120
   - **Impact:** Action will never execute
   - **Fix:** Increase totalDuration to 180 or move Action to frame 60

### ⚠️  Warnings (Should Fix)

1. **Missing Effect Color**
   - **Problem:** DamageAction has no effectColor defined
   - **Impact:** Visual feedback may be missing or use default color
   - **Fix:** Add appropriate color for damage type
   ```json
   "effectColor": {
       "$type": "UnityEngine.Color, UnityEngine.CoreModule",
       1.0, 0.3, 0.3, 1.0  // Red for damage
   }
   ```

2. **Poor Scaling**
   - **Problem:** spellPowerRatio 0.1 is too low for a magic skill
   - **Impact:** Skill scales poorly with equipment
   - **Fix:** Increase to 0.5-0.7 for primary damage skill

### ℹ️  Suggestions (Optional)

1. **Naming Convention**
   - Current: "Track1", "Track2"
   - Suggested: "Damage Track", "Animation Track"
   - Improves readability and maintainability

2. **Audio Configuration**
   - Consider adding 3D audio with appropriate min/max distances
   - Current: 2D audio
   - Benefit: Better spatial awareness in game

## Fixes Applied

✓ Fixed JSON syntax error on line 45
✓ Adjusted Action timing to fit skill duration
✓ Added missing effect colors
✓ Updated scaling ratios

## Verification Results

✓ JSON syntax is valid
✓ All required fields present
✓ Type declarations are correct
✓ Frame timing is reasonable
✓ Balance values are reasonable

## Recommendations

1. Test skill at levels 1, 5, 10, and max level
2. Verify animation and audio resources exist in project
3. Check timing in-game to ensure responsiveness
4. Consider adding input buffering for better player experience

## Summary
Fixed X critical issues, Y warnings, and Z suggestions. Skill configuration is now valid and ready for testing.
```

## Interactive Debugging

When user provides unclear error description:

1. **Ask clarifying questions:**
   - What error message do you see?
   - When does the issue occur (loading, runtime, specific Action)?
   - What is expected vs actual behavior?
   - Which skill file is affected?

2. **Read file** - Load and examine JSON

3. **Reproduce** - Understand problem in context

4. **Diagnose** - Identify root cause

5. **Fix** - Apply corrections

6. **Explain** - Describe what was wrong and why the fix works

7. **Prevent** - Suggest how to avoid similar issues

## Validation Checklist

Before completing debugging, verify:

- [ ] JSON is valid and parseable
- [ ] All required fields are present
- [ ] All $id and $type declarations are correct
- [ ] Frame timing is reasonable (within totalDuration)
- [ ] Duration calculations are correct (frames = seconds * frameRate)
- [ ] Resource references are valid (animation clips, audio clips)
- [ ] Balance values are reasonable
- [ ] Target filters are appropriate (0=self, 1=enemies, 2=allies, 3=all)
- [ ] Effect colors are defined for visual Actions
- [ ] Audio configuration is correct (3D vs 2D, distances)
- [ ] Naming conventions are consistent

## Workflow

1. **Load skill file** - Read JSON content
2. **Validate syntax** - Check JSON structure
3. **Check structure** - Verify required fields and types
4. **Analyze logic** - Review timing, values, references
5. **Calculate values** - Test balance at different levels
6. **Identify issues** - Categorize by severity
7. **Apply fixes** - Make corrections
8. **Verify fixes** - Ensure changes solve problems
9. **Generate report** - Document issues and fixes
10. **Save corrected file** - Update JSON file

## Output Requirements

Provide:
1. Comprehensive debug report
2. List of issues found (categorized by severity)
3. Fixes applied
4. Verification results
5. Testing recommendations
6. Prevention tips

Always explain why something is a problem and how the fix addresses it. This helps developers learn and avoid similar issues in the future.

## Using File References

You can use `@` to reference skill files:
```
/skill-debug @Assets/Skills/BrokenSkill.json
```

Or provide path directly as parameter:
```
/skill-debug Assets/Skills/BrokenSkill.json
```