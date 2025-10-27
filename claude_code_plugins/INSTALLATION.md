# Installation Guide

Quick guide to install and test the Game Skill Configuration Plugin.

## Quick Start (Local Testing)

Since you're in the development directory, you can install directly:

### Step 1: Add the Marketplace

In Claude Code, run:
```
/plugin marketplace add E:\Study\wqaetly\ai_agent_for_skill\claude_code_plugins
```

Or use relative path from your project root:
```
/plugin marketplace add ./claude_code_plugins
```

### Step 2: Install the Plugin

```
/plugin install game-skill-config@game-dev-plugins
```

### Step 3: Restart Claude Code

Exit and restart Claude Code to load the plugin.

### Step 4: Verify Installation

Check that the plugin is loaded:
```
/help
```

You should see new commands:
- `/skill-generate` - Generate new skill configurations
- `/skill-analyze` - Analyze existing skills
- `/skill-debug` - Debug skill issues
- `/skill-list` - List all skills
- `/skill-compare` - Compare skills

## Testing the Plugin

### Test 1: Generate a Simple Skill

```
/skill-generate

Create a simple fireball skill that deals 100 magic damage
```

Claude should:
1. Ask clarifying questions if needed
2. Generate a complete JSON configuration
3. Save it to `Assets/Skills/` directory
4. Explain the mechanics

### Test 2: Analyze an Existing Skill

```
/skill-analyze

Analyze Assets/Skills/TryndamereBloodlust.json
```

Claude should:
1. Read the file
2. Provide detailed mechanical breakdown
3. Show timeline visualization
4. Calculate values at different levels
5. Give recommendations

### Test 3: List All Skills

```
/skill-list
```

Claude should show a formatted list of all skills in your project.

### Test 4: Compare Skills

```
/skill-compare

Compare TryndamereBloodlust.json and SionSoulFurnaceV2.json
```

Claude should show side-by-side comparison with balance analysis.

### Test 5: Natural Language (Agent/Skill Activation)

Try natural language instead of commands:
```
I need a healing skill that consumes mana to restore health.
The healing should scale with spell power.
```

The Skill Configuration Specialist agent or Game Skill System Expert should automatically activate.

### Test 6: Validation Hook

Create or edit a skill file and the validation hook should run automatically:
```
Create a new file: Assets/Skills/TestSkill.json

Then modify it and save
```

You should see validation messages after saving.

## Troubleshooting

### Commands Not Showing

If commands don't appear in `/help`:

1. Check plugin is installed:
   ```
   /plugin
   ```

2. Verify marketplace is added:
   ```
   /plugin marketplace list
   ```

3. Check plugin is enabled:
   ```
   /plugin list
   ```

4. Try reinstalling:
   ```
   /plugin uninstall game-skill-config@game-dev-plugins
   /plugin install game-skill-config@game-dev-plugins
   ```

5. Restart Claude Code

### Hooks Not Working

If validation hooks aren't firing:

1. Check scripts are executable:
   ```bash
   cd claude_code_plugins/game-skill-config-plugin/scripts
   ls -la
   ```

   If not executable:
   ```bash
   chmod +x *.sh
   ```

2. Test script manually:
   ```bash
   ./validate-skill.sh "../../../ai_agent_for_skill/Assets/Skills/TryndamereBloodlust.json"
   ```

3. Check Python is available:
   ```bash
   python3 --version
   ```

### Agent Not Activating

The agent should activate automatically when you mention skill configuration. If it doesn't:

1. Try using a command first: `/skill-generate`
2. Be explicit: "Use the skill configuration specialist to help me..."
3. Reference skill files directly: "Analyze TryndamereBloodlust.json"

### Path Issues on Windows

If you encounter path issues on Windows:

Use forward slashes or escape backslashes:
```
/plugin marketplace add E:/Study/wqaetly/ai_agent_for_skill/claude_code_plugins
```

Or from within your project:
```
cd E:\Study\wqaetly\ai_agent_for_skill
claude
/plugin marketplace add ./claude_code_plugins
```

## Plugin Structure

Your installed plugin has this structure:

```
claude_code_plugins/
├── .claude-plugin/
│   └── marketplace.json         # Marketplace definition
└── game-skill-config-plugin/
    ├── .claude-plugin/
    │   └── plugin.json          # Plugin manifest
    ├── commands/
    │   ├── skill-generate.md    # Generate new skills
    │   ├── skill-analyze.md     # Analyze existing skills
    │   ├── skill-debug.md       # Debug skill issues
    │   ├── skill-list.md        # List all skills
    │   └── skill-compare.md     # Compare skills
    ├── agents/
    │   └── skill-config-specialist.md  # Specialized agent
    ├── skills/
    │   └── skill-system-expert/
    │       └── SKILL.md         # Agent Skill
    ├── hooks/
    │   └── hooks.json           # Hook configuration
    ├── scripts/
    │   ├── validate-skill.sh    # Validation script
    │   └── detect-skill-intent.sh  # Intent detection
    ├── README.md                # Documentation
    ├── LICENSE                  # MIT License
    └── CHANGELOG.md             # Version history
```

## Next Steps

Once installed successfully:

1. **Generate your first skill** - Try `/skill-generate` with a simple concept
2. **Analyze existing skills** - Use `/skill-analyze` to understand your current skills
3. **Compare for balance** - Use `/skill-compare` to check balance across skills
4. **Use natural language** - Just describe what you need, let the agent help

## Support

If you encounter issues:

1. Check this installation guide
2. Review the main [README.md](game-skill-config-plugin/README.md)
3. Run Claude Code with debug: `claude --debug`
4. Check the [CHANGELOG.md](game-skill-config-plugin/CHANGELOG.md)

## Development Mode

If you want to modify the plugin:

1. Make changes to files in `game-skill-config-plugin/`
2. Uninstall: `/plugin uninstall game-skill-config@game-dev-plugins`
3. Reinstall: `/plugin install game-skill-config@game-dev-plugins`
4. Restart Claude Code
5. Test your changes

Happy skill crafting! 🎮✨
