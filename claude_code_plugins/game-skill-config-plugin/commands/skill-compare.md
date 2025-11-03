---
description: Compare two or more skill configurations side-by-side
argument-hint: <skill1> <skill2> [skill3...]
allowed-tools: Read
---

# Skill Comparison Command

Compare multiple skill configurations to identify differences, similarities, and balance disparities.

## Usage

```
/skill-compare skill1.json skill2.json [skill3.json ...]
```

Or use file references:
```
/skill-compare @Assets/Skills/TryndamereBloodlust.json @Assets/Skills/SionSoulFurnace.json
```

## Comparison Categories

### 1. Basic Information
- Skill name, description, ID
- Duration (frames and seconds), frame rate

### 2. Structure
- Number of tracks, number of Actions
- Action types used, track organization

### 3. Mechanics
- Damage/heal/shield output
- Resource consumption/generation
- Special mechanics (input detection, multi-phase, etc.)

### 4. Scaling
- Base values, spell power ratios
- Attack power ratios, health ratios, level scaling

### 5. Timing
- Action timing patterns, animation length
- Skill responsiveness, total duration

### 6. Balance
- Effective values at levels 1, 6, 11, 16
- Scaling efficiency

## Output Format

Provide comprehensive side-by-side comparison including:
- Overview table
- Mechanics comparison
- Value calculations at different levels
- Timeline comparison
- Balance analysis
- Design pattern comparison
- Code quality assessment
- Recommendations

Focus on insights that help maintain skill system balance and consistency.
