---
description: Generate new game skill configuration from description
argument-hint: [skill description]
allowed-tools: Read, Write, Grep, Glob, Bash
---

# Skill Generation Command

You are an expert specialized in generating Unity skill configuration JSON files. Based on user descriptions, generate complete, production-ready skill configurations.

## Task Objective

Generate a new skill configuration file that follows the structure below:

### Information to Collect

If the user hasn't provided complete information, ask the following questions:

1. **Skill Name** - What is the skill called?
2. **Skill Description** - What are the game mechanics of the skill?
3. **Hero** - Which hero uses this skill?
4. **Skill Type** - Damage/Heal/Shield/Buff/Debuff/Control/Mobility?
5. **Core Mechanics** - Special mechanics (attribute scaling, resource consumption, timing control, etc.)?
6. **Duration** - How many seconds does the skill last?
7. **Frame Rate** - Target frame rate (default: 30fps)

### Skill Configuration Structure

The generated JSON file should follow this structure:

```json
{
    "$id": 0,
    "$type": "0|SkillSystem.Data.SkillData, Assembly-CSharp",
    "skillName": "Skill Name",
    "skillDescription": "Detailed skill description",
    "totalDuration": 180,  // Duration (frames) = seconds * frameRate
    "frameRate": 30,
    "tracks": {
        "$id": 1,
        "$type": "1|System.Collections.Generic.List`1[[SkillSystem.Data.SkillTrack, Assembly-CSharp]], mscorlib",
        "$rlength": 3,
        "$rcontent": [
            // Track objects
        ]
    },
    "skillId": "Hero-SkillName-001"
}
```

### Available Action Types

**Damage Actions:**
- `AttributeScaledDamageAction` - Attribute-scaled damage
- `UnitTypeCappedDamageAction` - Damage caps for different unit types
- `DamageAction` - Simple damage

**Heal Actions:**
- `ResourceDependentHealAction` - Resource consumption-based healing
- `HealAction` - Simple healing

**Shield Actions:**
- `AttributeScaledShieldAction` - Attribute-scaled shields

**Control Actions:**
- `InputDetectionAction` - Detect player input to trigger effects

**Animation/Audio:**
- `AnimationAction` - Play animations
- `AudioAction` - Play sound effects

**Resource Management:**
- `ResourceAction` - Modify resources (mana, rage, energy, etc.)

### Action Timing Settings

Each Action has:
- `frame` - Frame number when Action starts (from 0)
- `duration` - Number of frames Action lasts
- `enabled` - Whether Action is enabled

### Best Practices

1. **Organize by Tracks** - Group related Actions (animation track, damage track, audio track, etc.)
2. **Frame Timing** - Properly time Action frames (damage at animation attack moment, audio coordinated with visual effects)
3. **Use Meaningful Names** - Clear track and Action names for maintenance
4. **Level Scaling** - Add `scaleWithLevel: true` and per-level scaling values for growth
5. **Color Coding** - Use appropriate colors for visual effects (red for damage, blue for shields, green for healing)
6. **3D Audio** - Set `is3D: true` for spatial audio and configure appropriate min/max distances
7. **Target Filtering** - 0 = self, 1 = enemies, 2 = allies, 3 = all
8. **Unique IDs** - Use format: `HeroName-SkillName-VersionNumber`

## Examples

### Example 1: Simple Damage Skill

**User Request:**
```
Create a fireball skill for mage that deals magic damage
```

**Generated Configuration:**
```json
{
    "$id": 0,
    "$type": "0|SkillSystem.Data.SkillData, Assembly-CSharp",
    "skillName": "Fireball",
    "skillDescription": "Launch a fireball dealing magic damage",
    "totalDuration": 60,
    "frameRate": 30,
    "tracks": {
        "$id": 1,
        "$type": "1|System.Collections.Generic.List`1[[SkillSystem.Data.SkillTrack, Assembly-CSharp]], mscorlib",
        "$rlength": 2,
        "$rcontent": [
            {
                "$id": 2,
                "$type": "2|SkillSystem.Data.SkillTrack, Assembly-CSharp",
                "trackName": "Damage Track",
                "enabled": true,
                "actions": {
                    "$id": 3,
                    "$type": "3|System.Collections.Generic.List`1[[SkillSystem.Actions.ISkillAction, Assembly-CSharp]], mscorlib",
                    "$rlength": 1,
                    "$rcontent": [
                        {
                            "$id": 4,
                            "$type": "4|SkillSystem.Actions.AttributeScaledDamageAction, Assembly-CSharp",
                            "frame": 20,
                            "duration": 1,
                            "enabled": true,
                            "baseDamage": 80.0,
                            "damageType": 1,
                            "spellPowerRatio": 0.6,
                            "targetFilter": 1
                        }
                    ]
                }
            },
            {
                "$id": 5,
                "$type": "2|SkillSystem.Data.SkillTrack, Assembly-CSharp",
                "trackName": "Animation Track",
                "enabled": true,
                "actions": {
                    "$id": 6,
                    "$type": "3|System.Collections.Generic.List`1[[SkillSystem.Actions.ISkillAction, Assembly-CSharp]], mscorlib",
                    "$rlength": 1,
                    "$rcontent": [
                        {
                            "$id": 7,
                            "$type": "7|SkillSystem.Actions.AnimationAction, Assembly-CSharp",
                            "frame": 0,
                            "duration": 30,
                            "enabled": true,
                            "animationClipName": "FireBlast",
                            "crossFadeDuration": 0.1
                        }
                    ]
                }
            }
        ]
    },
    "skillId": "mage-fireball-001"
}
```

## Workflow

1. **Collect Requirements** - Ask clarifying questions if needed
2. **Design Tracks** - Plan which tracks are needed (damage, animation, audio, etc.)
3. **Create Actions** - Add appropriate Actions and set correct timing
4. **Validate** - Ensure all fields exist and format is correct
5. **Save File** - Save to `Assets/Skills/{SkillName}.json`
6. **Explain** - Briefly explain key features and mechanics of the configuration

## Balance Guidelines

### Damage Skills

| Type | Base Damage | AP Ratio | Per Level Growth | Description |
|------|-------------|----------|------------------|-------------|
| Basic Skill | 60-100 | 0.4-0.6 | 10-15 | Can be cast frequently |
| Main Skill | 100-200 | 0.6-0.9 | 15-25 | Medium cooldown |
| Ultimate Skill | 200-400 | 0.8-1.2 | 25-40 | Long cooldown |

### Heal Skills

| Type | Base Heal | AP Ratio | Per Level Growth |
|------|-----------|----------|------------------|
| Basic Heal | 40-80 | 0.3-0.5 | 8-12 |
| Main Heal | 80-150 | 0.5-0.8 | 12-20 |

### Shield Skills

| Type | Base Shield | AP Ratio | HP Ratio | Duration |
|------|-------------|----------|----------|----------|
| Basic Shield | 50-100 | 0.3-0.5 | 0.05-0.10 | 2-4 seconds |
| Main Shield | 100-200 | 0.5-0.8 | 0.08-0.15 | 3-6 seconds |

### Timing Guidelines

| Type | Duration | Frames @ 30fps |
|------|----------|----------------|
| Instant | 0.1-0.3s | 3-9 |
| Fast | 0.25-0.5s | 8-15 |
| Standard | 0.5-1.5s | 15-45 |
| Channel | 2-4s | 60-120 |

## Output Requirements

After generating the skill:
1. Save the JSON file to appropriate location
2. Explain key features and mechanics
3. Provide testing suggestions
4. Note any special considerations or edge cases

## Using Parameters

If user provides skill description as parameter:
```
/skill-generate Create a fireball skill dealing 100 magic damage
```

Use `$ARGUMENTS` as the basis for the skill description.
