---
name: game-skill-system-expert
description: Expert knowledge of Unity-based game skill configuration system. Use when working with skill JSON files, generating/modifying/analyzing game skills, debugging skill configs, or discussing skill mechanics like damage/healing/shields/buffs. Automatically activates for skill-related tasks in game development.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# Game Skill System Expert

## Overview

This Skill provides comprehensive expertise in Unity-based game skill configuration systems. It understands the complete architecture, including SkillData structures, tracks, Actions, timing systems, attribute scaling, and balance principles.

## When to Use This Skill

I automatically activate when you:
- Work with skill JSON configuration files
- Generate, create, or modify game skills
- Analyze skill balance or mechanics
- Debug skill configuration issues
- Discuss game mechanics (damage, healing, shields, resources, buffs, debuffs)
- Optimize skill timing or performance
- Batch process multiple skill configurations
- Reference files in the `Assets/Skills/` directory

## Core Capabilities

### 1. Skill Generation
Create complete, production-ready skill configurations from natural language descriptions.

**Process:**
1. Gather requirements through targeted questions
2. Design appropriate track architecture
3. Calculate balanced values using game design formulas
4. Generate complete JSON with correct structure
5. Validate configuration
6. Explain mechanics and provide testing guidance

**Key Considerations:**
- Appropriate base values for skill type
- Scaling ratios that feel fair
- Timing that feels responsive
- Correct target filtering
- Complete audio/visual configuration
- Unique skill IDs

### 2. Skill Analysis
Parse and analyze existing configurations to provide insights and recommendations.

**Analysis Includes:**
- Mechanics breakdown (what the skill does)
- Timing analysis (when Actions occur)
- Balance assessment (damage/heal output at different levels)
- Scaling efficiency (effect of attribute scaling)
- Code quality assessment
- Comparison with similar skills

**Outputs:**
- Comprehensive documentation
- Timeline visualizations
- Balance calculations
- Improvement recommendations

### 3. Skill Debugging
Identify and fix issues in skill configurations.

**Issue Detection:**
- Syntax errors (invalid JSON)
- Structural errors (missing fields, wrong types)
- Logic errors (timing issues, invalid references)
- Balance problems (extreme values)
- Quality issues (poor naming, missing effects)

**Debugging Process:**
1. Validate JSON syntax
2. Check required fields and types
3. Analyze timing logic
4. Verify resource references
5. Assess balance
6. Categorize issues by severity
7. Apply fixes
8. Generate debug report

### 4. Skill Optimization
Improve existing skills for better performance, feel, or maintainability.

**Optimization Areas:**
- Timing refinement for better responsiveness
- Scaling curve adjustments for smoother progression
- Performance improvements (reduce redundancy)
- Code quality (naming, structure, organization)
- Balance adjustments

## Technical Reference

### SkillData Structure

```json
{
    "$id": 0,
    "$type": "0|SkillSystem.Data.SkillData, Assembly-CSharp",
    "skillName": "Skill Name",
    "skillDescription": "What the skill does",
    "totalDuration": 180,  // frames
    "frameRate": 30,       // fps
    "tracks": {
        "$id": 1,
        "$type": "1|System.Collections.Generic.List`1[[SkillSystem.Data.SkillTrack, Assembly-CSharp]], mscorlib",
        "$rlength": 3,
        "$rcontent": [/* tracks */]
    },
    "skillId": "Hero-SkillName-001"
}
```

### Track Structure

```json
{
    "$id": 2,
    "$type": "2|SkillSystem.Data.SkillTrack, Assembly-CSharp",
    "trackName": "Track Name",
    "enabled": true,
    "actions": {
        "$id": 3,
        "$type": "3|System.Collections.Generic.List`1[[SkillSystem.Actions.ISkillAction, Assembly-CSharp]], mscorlib",
        "$rlength": 1,
        "$rcontent": [/* actions */]
    }
}
```

### Common Action Types

**Damage:**
- `AttributeScaledDamageAction` - Scales with spell power, attack damage, health
- `UnitTypeCappedDamageAction` - Different damage caps for minions/jungle/champs
- `DamageAction` - Simple fixed damage

**Healing:**
- `ResourceDependentHealAction` - Healing based on resource consumption
- `HealAction` - Simple healing

**Shields:**
- `AttributeScaledShieldAction` - Attribute-scaled shield with duration

**Control:**
- `InputDetectionAction` - Detect player input to trigger conditional effects

**Animation/Audio:**
- `AnimationAction` - Play animation clips
- `AudioAction` - Play sound effects (2D or 3D spatial audio)

**Resources:**
- `ResourceAction` - Modify resources (mana, rage, energy, etc.)

### Action Properties

Each Action has:
- `$id` - Unique numeric ID within the file
- `$type` - Full type path with ID prefix
- `frame` - Action start time (from 0)
- `duration` - Number of frames Action lasts
- `enabled` - Whether Action is active

### Scaling Formulas

**Damage Formula:**
```
Total = (Base + Level * PerLevel) + SpellPower * SpellPowerRatio + AttackDamage * ADRatio + MaxHealth * HealthRatio
```

**Heal Formula:**
```
Total = (Base + Level * PerLevel) + SpellPower * SpellPowerRatio + Resource * PerResource
```

**Shield Formula:**
```
Total = (Base + Level * PerLevel) + SpellPower * SpellPowerRatio + Health * HealthRatio
```

### Balance Guidelines

**Damage Skills:**

| Type | Base | Spell Power Ratio | Per Level | Description |
|------|------|-------------------|-----------|-------------|
| Basic | 60-100 | 0.4-0.6 | 10-15 | Can be cast frequently |
| Main | 100-200 | 0.6-0.9 | 15-25 | Medium cooldown |
| Ultimate | 200-400 | 0.8-1.2 | 25-40 | Long cooldown |

**Heal Skills:**

| Type | Base | Spell Power Ratio | Per Level |
|------|------|-------------------|-----------|
| Basic | 40-80 | 0.3-0.5 | 8-12 |
| Main | 80-150 | 0.5-0.8 | 12-20 |

**Shield Skills:**

| Type | Base | Spell Power Ratio | Health Ratio | Duration |
|------|------|-------------------|--------------|----------|
| Basic | 50-100 | 0.3-0.5 | 0.05-0.10 | 2-4 seconds |
| Main | 100-200 | 0.5-0.8 | 0.08-0.15 | 3-6 seconds |

**Timing Guidelines:**

| Type | Duration | Frames @ 30fps |
|------|----------|----------------|
| Instant | 0.1-0.3s | 3-9 |
| Quick | 0.25-0.5s | 8-15 |
| Standard | 0.5-1.5s | 15-45 |
| Channel | 2-4s | 60-120 |

### Target Filters

- `0` = Self only
- `1` = Enemies only
- `2` = Allies only
- `3` = All units

### Damage Types

- `0` = Physical damage
- `1` = Magic damage
- `2` = True damage (ignores resistances)

### Resource Types

- `0` = Mana
- `1` = Energy
- `2` = Rage
- `3` = Shield (temporary health)
- `4` = Health

## Workflow Examples

### Example 1: Generate New Skill

**User Request:** "Create a fireball skill for a mage"

**My Approach:**
1. Ask clarifying questions:
   - Damage amount preference? (I'll suggest 80 base, 0.6 spell power ratio)
   - Duration? (I'll suggest 1 second cast time)
   - Any special mechanics? (AOE, single target, etc.)

2. Design tracks:
   - Damage track (fire damage at frame 20)
   - Animation track (cast animation 0-30)
   - Audio track (cast sound + hit sound)

3. Generate JSON with correct structure

4. Explain mechanics and testing steps

### Example 2: Analyze Existing Skill

**User Request:** "Analyze TryndamereBloodlust.json"

**My Approach:**
1. Use Read tool to load file
2. Parse structure and extract all data
3. Calculate heal values for levels 1, 6, 11, 16
4. Create timeline showing Action sequence
5. Assess balance (heal per rage point)
6. Check code quality
7. Provide recommendations

### Example 3: Debug Skill Issue

**User Request:** "My skill isn't working, damage seems wrong"

**My Approach:**
1. Read skill configuration
2. Validate JSON structure
3. Check Action timing and frames
4. Calculate actual damage values
5. Compare with expected values
6. Identify issue (e.g., wrong damage type, missing scaling)
7. Fix and explain

## Best Practices

### Structure
- Group related Actions in named tracks
- Use clear, descriptive track names
- Order tracks logically (animation, damage, audio, effects)

### Timing
- Align damage/healing with animation apex
- Add sound effects at appropriate moments
- Consider input buffering for better responsiveness
- Frame 0 is skill start, plan timing accordingly

### Balance
- Start with guideline values, adjust based on testing
- Ensure scaling feels fair (not too weak early, not too strong late)
- Consider resource cost vs power level
- Test at multiple levels and attribute levels

### Quality
- Always include effect colors for visual Actions
- Configure 3D audio properly (minDistance, maxDistance)
- Use unique, descriptive skill IDs
- Add helpful comments in skill descriptions
- Validate before saving

### Maintainability
- Follow consistent naming conventions
- Keep related Actions together in tracks
- Use meaningful IDs and names
- Document complex mechanics in descriptions

## Quality Checklist

Verify before completing any skill work:

- [ ] JSON syntax is valid
- [ ] All required fields present (skillName, skillDescription, totalDuration, frameRate, skillId)
- [ ] $id and $type declarations match and are sequential
- [ ] All frames are within totalDuration
- [ ] Duration calculations are correct (frames = seconds * frameRate)
- [ ] Balance values are in appropriate ranges
- [ ] Effect colors are defined for visual Actions
- [ ] Audio configuration is correct (3D when needed)
- [ ] Target filters are appropriate
- [ ] Naming is consistent and descriptive
- [ ] Resource references are valid (animation/audio clip names)

## Common Patterns

**Instant Damage Skill:**
```
- Animation track: Cast animation (10-20 frames)
- Damage track: Damage at animation apex
- Audio track: Cast sound + hit sound
```

**Channel Skill:**
```
- Animation track: Channel animation (entire duration)
- Damage track: Multiple damage ticks
- Audio track: Channel loop sound
```

**Shield with Explosion:**
```
- Shield track: Apply shield (6 second duration)
- Input detection track: Wait for W key after 3 seconds
- Damage track: Explosion damage when input detected
- Animation track: Shield cast + explosion
- Audio track: Shield application + explosion sounds
```

**Resource-Based Healing:**
```
- Resource track: Consume rage/energy
- Heal track: Healing based on consumed resource
- Animation track: Cast animation
- Audio track: Cast sound + resource consumption sound
```

## Tools I Use

- **Read**: Load skill JSON files
- **Write**: Create new skill configurations
- **Edit**: Modify existing skills
- **Grep**: Search patterns across multiple skills
- **Glob**: Find all skill files
- **Bash**: Validate JSON, run scripts, batch operations

## Output Format

I provide:
- Clear, well-formatted JSON configurations
- Detailed explanations with reasoning
- Calculated breakdowns
- Timeline visualizations
- Actionable recommendations
- Testing guidance

## Need Help?

Just describe what you need in natural language:
- "Create a healing skill that consumes mana"
- "Analyze all damage skills in Assets/Skills"
- "Debug SionSoulFurnace.json"
- "Why does my skill timing feel off?"
- "Generate 3 variants of a lightning skill"

I'll handle the technical details and guide you through the process!