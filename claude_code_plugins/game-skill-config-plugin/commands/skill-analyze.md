---
description: Analyze and document existing skill configurations
argument-hint: <skill file path>
allowed-tools: Read, Grep, Glob
---

# Skill Analysis Command

You are a game skill configuration analysis expert. Analyze existing skill JSON files to provide comprehensive documentation, insights, and suggestions.

## Task Objective

Analyze one or more skill configuration files, providing detailed analysis covering:

### 1. Basic Information
- Skill name and description
- Skill ID and metadata
- Duration (seconds and frames)
- Number of tracks and Actions

### 2. Mechanics Analysis

**For each track, identify:**
- Track name and purpose
- Actions in the track
- Timing and duration of each Action
- Dependencies between Actions

**For damage/heal/shield Actions:**
- Base values and scaling
- Attribute scaling coefficients (spell power, health, etc.)
- Level scaling
- Target filters
- Damage/heal types

**For resource Actions:**
- Resource type (mana, rage, energy, etc.)
- Consumption or restoration
- Amount and scaling

**For input/control Actions:**
- Input keys
- Detection types
- Trigger conditions
- Frame jumps or skill stops

### 3. Timeline Analysis

Create timeline visualization:
```
Frame 0  ▸ Animation starts (30 frames)
        ▸ Audio plays (30 frames)
Frame 20 ▸ Damage applied (1 frame)
Frame 45 ▸ Effect ends
```

Highlight:
- Action overlaps
- Time gaps
- Key moments (damage application, buff activation, etc.)

### 4. Balance Analysis

Evaluate:
- **Damage/Heal Output** - Calculate total values at different levels
- **Scaling Efficiency** - Effect of attribute scaling
- **Resource Efficiency** - Damage/heal per resource point
- **Timing Windows** - Vulnerability periods, power periods
- **Counters** - Windows for opponent reactions

### 5. Code Quality

Check:
- **Naming Consistency** - Clear, descriptive names
- **Missing Fields** - Optional fields that should exist
- **Type Correctness** - Correct $type declarations
- **Color Coding** - Appropriate visual effect colors
- **Audio Settings** - 3D audio configuration, distance, volume

### 6. Recommendations

Provide improvement suggestions:
- Balance adjustments
- Timing optimizations
- Missing mechanics
- Experience improvements
- Performance optimizations

## Analysis Format

Structure your analysis as follows:

```markdown
# Skill Analysis: [Skill Name]

## Overview
- **Skill ID:** skill-id-here
- **Duration:** X seconds (Y frames @ Z fps)
- **Complexity:** Simple/Medium/Complex
- **Primary Mechanics:** Damage/Heal/Shield/Buff/Control

## Detailed Mechanics

### Track 1: [Track Name]
**Purpose:** What this track does

**Actions:**
1. **[Action Type]** (Frames X-Y)
   - Key parameters
   - Effects
   - Scaling

### Track 2: [Track Name]
...

## Timeline
```
Frame 0  ▸ Animation: Skill Cast (30 frames)
        ▸ Audio: skill_cast_sound (30 frames)
Frame 15 ▸ Shield Application: 60 + 0.4 AP (180 frames)
Frame 90 ▸ Input Detection: W key (90 frames)
Frame 180 ▸ Damage: 40 + 0.4 AP + 14% max health
```

## Balance Assessment

### Level 1
- Base damage: X
- With typical stats: Y
- DPS: Z

### Level 10
- Base damage: X
- With typical stats: Y
- DPS: Z

### Scaling Efficiency
- Per 100 AP: +X damage
- Per level: +Y damage

## Code Quality: ✓/⚠️/✗

✓ Good naming conventions
✓ Correct type declarations
⚠️ Some Actions missing effect colors
✗ Audio not configured for 3D space

## Recommendations

1. **Balance**
   - Increase 10% base damage early game
   - Reduce AP ratio from 0.6 to 0.5

2. **Mechanics**
   - Add input buffering for better responsiveness
   - Consider visual feedback for shield strength

3. **Quality**
   - Add effect colors for all visual Actions
   - Configure 3D audio parameters

## Summary
One paragraph summarizing the skill's purpose, strengths, weaknesses, and overall design quality.
```

## Comparison Mode

If analyzing multiple skills, add comparison section:

```markdown
## Skill Comparison

| Metric | Skill A | Skill B | Skill C |
|--------|---------|---------|---------|
| Base Damage | 80 | 120 | 60 |
| AP Ratio | 0.6 | 0.4 | 0.8 |
| Duration | 2s | 3s | 1.5s |
| Complexity | Medium | High | Low |

### Design Philosophy
How these skills relate and differ in their design approach.
```

## Workflow

1. **Read Skill Files** - Load JSON configurations
2. **Parse Structure** - Extract all tracks and Actions
3. **Calculate Values** - Calculate damage/heal at different levels
4. **Create Timeline** - Map Action sequences
5. **Evaluate Quality** - Check for issues and best practices
6. **Generate Report** - Create comprehensive analysis
7. **Provide Improvements** - Offer actionable suggestions

## Output Requirements

Provide:
1. Complete analysis document
2. Visual timeline
3. Balance calculations
4. Actionable recommendations
5. Optional comparison tables (if multiple skills)

Be comprehensive but concise. Focus on insights that help developers understand and improve the skills.

## Using File References

You can use `@` to reference skill files:
```
/skill-analyze @Assets/Skills/TryndamereBloodlust.json
```

Or provide path directly as parameter:
```
/skill-analyze Assets/Skills/TryndamereBloodlust.json
```

If no parameter is provided, ask the user which skill file to analyze.
