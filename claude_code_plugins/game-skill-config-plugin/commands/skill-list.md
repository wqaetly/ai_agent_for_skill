---
description: List all skill configurations in the project
allowed-tools: Glob, Read
---

# Skill List Command

List and summarize all skill configuration files in the project.

## Task Objective

Find and display all skill JSON files in the `Assets/Skills/` directory and provide a summary of each skill.

## Workflow

1. **Find skill files** - Use Glob to find all .json files in Assets/Skills/
2. **Read each file** - Load skill configuration
3. **Extract key information** - Get skillName, skillDescription, skillId, duration
4. **Calculate statistics** - Count tracks, Actions, total duration (seconds)
5. **Format output** - Create formatted table or list

## Output Format

```markdown
# Skill Configuration List

Found X skills in Assets/Skills/

## Skill Summary

| Skill Name | ID | Duration | Tracks | Description |
|------------|-----|----------|---------|-------------|
| Bloodlust | tryndamere-bloodlust-001 | 2.0s | 3 | Consumes rage to heal |
| Soul Furnace | sion-soul-furnace-001 | 6.0s | 5 | Shield with explosion |
| ... | ... | ... | ... | ... |

## Detailed Information

### 1. Bloodlust (tryndamere-bloodlust-001)
**Description:** Tryndamere consumes rage to restore health
**Duration:** 60 frames (2.0s @ 30fps)
**Track Count:** 3
- Resource Heal Track (1 Action)
- Animation Track (1 Action)
- Audio Track (1 Action)

**Core Mechanics:**
- Resource Cost: 50 rage
- Base Heal: 30 + 0.5 per rage
- Level Scaling: +10 base, +0.45 per rage per level
- Spell Power Scaling: 0.3 base + 0.012 per rage

---

### 2. Soul Furnace (sion-soul-furnace-001)
...

## Statistics

- **Total Skills:** X
- **Average Duration:** Y seconds
- **Most Complex:** [Skill with most tracks/Actions]
- **Action Type Distribution:**
  - Damage: X skills
  - Heal: Y skills
  - Shield: Z skills
  - Control: W skills
```

Can be filtered and sorted by skill type, hero, complexity, etc.
