# Game Skill Configuration Plugin

Comprehensive Claude Code plugin for Unity skill systems. Generate, analyze, debug, and optimize game skill JSON configurations from natural language descriptions.

> **Language:** English | [简体中文](README.zh-CN.md)

## ✨ Features

### 🎯 Specialized Commands

**`/skill-generate [description]`** - Generate New Skill Configuration
- Create complete skill JSON from natural language descriptions
- Intelligent questioning to gather requirements
- Balanced values based on game design principles
- Production-ready output with all required fields

**`/skill-analyze <file_path>`** - Analyze Existing Skills
- Comprehensive mechanics breakdown
- Timeline visualization
- Balance assessment across different levels
- Quality evaluation and suggestions
- Multi-skill comparative analysis

**`/skill-debug <file_path>`** - Debug Skill Issues
- Validate JSON syntax and structure
- Identify timing and logic errors
- Fix balance and performance issues
- Categorized problem reports (Critical/Warning/Suggestion)
- Auto-corrections with explanations

**`/skill-list`** - List All Skills
- Show summary of all skills in project
- Statistics and quick overview
- Filter by type, hero, or complexity

**`/skill-compare <skill1> <skill2>`** - Compare Skills
- Side-by-side mechanics comparison
- Balance analysis
- Identify design patterns and inconsistencies

### 🤖 Intelligent Agents

**Skill Configuration Specialist**
- Automatically called when handling skill configuration tasks
- Understands complete skill system architecture
- Provides expert guidance for generation, analysis, and debugging
- Batch processing capabilities

### 🧠 Agent Skill

**Game Skill System Expert**
- Professional knowledge with automatic model invocation
- Deep understanding of SkillData, tracks, Actions, and timing
- Balance formulas and scaling guidelines
- Best practices and quality standards
- Read-only tool access for safety

### 🔌 Automation Hooks

**Auto Validation**
- Validate skill JSON after Write/Edit operations
- Check syntax, required fields, and common issues
- Provide warnings for potential problems

**Intent Detection**
- Suggest relevant commands based on your requests
- Provide helpful tips when working with skills

**Session Context**
- Load skill system context on startup
- Ready to assist at any time

## 🚀 Installation

### From Local Directory

1. Add Marketplace:
   ```
   /plugin marketplace add E:\Study\wqaetly\ai_agent_for_skill\claude_code_plugins
   ```

2. Install Plugin:
   ```
   /plugin install game-skill-config@game-dev-plugins
   ```

3. Restart Claude Code

4. Verify Installation:
   ```
   /help
   ```
   You should see all the new commands.

For detailed installation guide, see [INSTALLATION.md](../INSTALLATION.md)

## 📖 Usage

### Quick Start

**Generate New Skill:**
```
/skill-generate Create a fireball skill for mage that deals magic damage
```

**Analyze Existing Skill:**
```
/skill-analyze Assets/Skills/TryndamereBloodlust.json
```

**Debug Skill:**
```
/skill-debug Assets/Skills/SionSoulFurnace.json
```

**List All Skills:**
```
/skill-list
```

**Compare Skill Balance:**
```
/skill-compare TryndamereBloodlust.json SionSoulFurnaceV2.json
```

### Natural Language

The plugin will automatically activate when you use natural language:

```
"I need a healing skill that consumes rage to restore health"
"Analyze all damage skills and compare their balance"
"Why isn't my shield skill working?"
"Create 5 variants of a lightning strike skill"
```

The Skill Configuration Specialist agent or Game Skill System Expert will automatically intervene.

## 🎮 Skill System Architecture

### Supported Action Types

**Damage Types:**
- `AttributeScaledDamageAction` - Attribute-scaled damage
- `UnitTypeCappedDamageAction` - Damage caps for different unit types

**Healing Types:**
- `ResourceDependentHealAction` - Resource consumption-based healing

**Shield Types:**
- `AttributeScaledShieldAction` - Attribute-scaled shields

**Control Types:**
- `InputDetectionAction` - Player input detection to trigger conditional effects

**Animation/Audio:**
- `AnimationAction` - Play animations
- `AudioAction` - Play sound effects (2D/3D spatial audio)

**Resources:**
- `ResourceAction` - Modify resources (mana, rage, energy, etc.)

### Balance Guidelines

Built-in balance value knowledge:

| Skill Type | Base Damage | AP Ratio | Per Level Growth |
|------------|-------------|----------|------------------|
| Basic Skill | 60-100 | 0.4-0.6 | 10-15 |
| Main Skill | 100-200 | 0.6-0.9 | 15-25 |
| Ultimate Skill | 200-400 | 0.8-1.2 | 25-40 |

### Timing Guidelines

| Type | Duration | Frames @ 30fps |
|------|----------|----------------|
| Instant | 0.1-0.3s | 3-9 |
| Fast | 0.25-0.5s | 8-15 |
| Standard | 0.5-1.5s | 15-45 |
| Channel | 2-4s | 60-120 |

## 📁 Plugin Structure

```
game-skill-config-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/                    # 5 specialized commands
│   ├── skill-generate.md
│   ├── skill-analyze.md
│   ├── skill-debug.md
│   ├── skill-list.md
│   └── skill-compare.md
├── agents/                      # Specialized agents
│   └── skill-config-specialist.md
├── skills/                      # Agent Skill
│   └── skill-system-expert/
│       └── SKILL.md
├── hooks/                       # Automation hooks
│   └── hooks.json
├── scripts/                     # Validation scripts
│   ├── validate-skill.sh
│   └── detect-skill-intent.sh
├── README.md                    # English documentation
├── README.zh-CN.md             # Chinese documentation
├── LICENSE                      # MIT License
└── CHANGELOG.md                 # Version history
```

## 🔧 Configuration

### Custom Validation

Edit `hooks/hooks.json` to customize validation behavior:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-skill.sh \"${FILE_PATH}\""
          }
        ]
      }
    ]
  }
}
```

### Extending with Custom Scripts

Add your own validation or processing scripts in the `scripts/` directory and reference them in the hooks.

## 🐛 Troubleshooting

### Plugin Not Loading

1. Check plugin is installed: `/plugin`
2. Verify installation: `/plugin list`
3. Check for errors: `claude --debug`

### Commands Not Showing

1. Ensure plugin is enabled: `/plugin enable game-skill-config`
2. Restart Claude Code
3. Check for new commands in `/help`

### Hooks Not Triggering

1. Verify scripts are executable: `chmod +x game-skill-config-plugin/scripts/*.sh`
2. Check hook configuration in `hooks/hooks.json`

### Agents Not Activating

Agents activate automatically based on context. Try:
- Explicitly mentioning "skill configuration"
- Using slash commands first
- Directly referencing skill JSON files

## 📚 Documentation

- [Full Documentation](README.md) (English)
- [Installation Guide](../INSTALLATION.md)
- [Changelog](CHANGELOG.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test locally using development Marketplace
5. Submit Pull Request

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Created for Unity game developers using JSON-based skill configuration systems.

Special thanks to the Claude Code team for providing the excellent plugin system!

---

**Happy skill creation!** 🎮✨
