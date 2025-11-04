# Installation Guide

Quick guide for installing and testing all Claude Code plugins from the remote GitHub repository.

## 🚀 Remote Installation (Recommended)

Since the plugins are hosted on GitHub, you can install them directly from the remote repository:

### Step 1: Add Plugin Marketplace from GitHub

Run in Claude Code:
```
/plugin marketplace add https://github.com/wqaetly/ai_agent_for_skill.git
```

This will add the entire repository as a plugin marketplace, giving you access to all plugins.

### Step 2: Install Plugins

#### Install Claude Development Standards Plugin (Recommended first)
```
/plugin install claude-standards@ai_agent_for_skill
```

#### Install Game Skill Configuration Plugin
```
/plugin install game-skill-config@ai_agent_for_skill
```

#### Install Unity Compilation Plugin
```
/plugin install nkg-unity@ai_agent_for_skill
```

### Step 3: Restart Claude Code

Exit and restart Claude Code to load the plugins.

### Step 4: Verify Installation

Check if plugins are loaded:
```
/help
```

## 🛠️ Local Installation (For Developers)

If you have cloned this repository locally, you can install from the local directory:

### Step 1: Add Plugin Marketplace Locally

Run in Claude Code:
```
/plugin marketplace add ./claude_code_plugins
```

Or use the absolute path:
```
/plugin marketplace add E:\Study\wqaetly\ai_agent_for_skill\claude_code_plugins
```

### Step 2: Install Plugins

#### Install Claude Development Standards Plugin (Recommended first)
```
/plugin install claude-standards@nkg-game-development-marketplace
```

#### Install Game Skill Configuration Plugin
```
/plugin install game-skill-config@nkg-game-development-marketplace
```

#### Install Unity Compilation Plugin
```
/plugin install nkg-unity@nkg-game-development-marketplace
```

### Step 3: Restart Claude Code

Exit and restart Claude Code to load the plugins.

### Step 4: Verify Installation

Check if plugins are loaded:
```
/help
```

You should see the following new commands:

#### Claude Development Standards Plugin Commands:
- `/standards-load` - Load development standards
- `/standards-config` - Configure standards parameters
- `/standards-status` - View standards status

#### Game Skill Configuration Plugin Commands:
- `/skill-generate` - Generate new skill configurations
- `/skill-analyze` - Analyze existing skills
- `/skill-debug` - Debug skill issues
- `/skill-list` - List all skills
- `/skill-compare` - Compare skills

#### Unity Compilation Plugin Commands:
- `/compile` - Intelligently compile Unity project
- `/find-assembly` - Find assembly

## 🧪 Plugin Testing

### Test Claude Development Standards Plugin

#### Test 1: Load Development Standards
```
/standards-load
```

Claude should:
1. Display successfully loaded standard modules
2. List current configuration details
3. Provide usage tips

#### Test 2: Configure Standards Parameters
```
/standards-config language --primary en-US
/standards-config socratic --auto-activate true
```

#### Test 3: View Standards Status
```
/standards-status --detailed
```

#### Test 4: Trigger Socratic Dialogue
Try using keywords:
```
Why was this architecture solution chosen?
```

Claude should automatically enter deep questioning mode.

### Test Game Skill Configuration Plugin

#### Test 1: Generate Simple Skill
```
/skill-generate

Create a simple fireball skill that deals 100 magic damage
```

Claude should:
1. Ask clarification questions if needed
2. Generate complete JSON configuration
3. Save to `Assets/Skills/` directory
4. Explain skill mechanics

#### Test 2: Analyze Existing Skill
```
/skill-analyze

Analyze Assets/Skills/TryndamereBloodlust.json
```

Claude should:
1. Read the file
2. Provide detailed mechanics analysis
3. Show timeline visualization
4. Calculate values for different levels
5. Give improvement suggestions

#### Test 3: List All Skills
```
/skill-list
```

Claude should display a formatted list of all skills in the project.

#### Test 4: Compare Skills
```
/skill-compare

Compare TryndamereBloodlust.json and SionSoulFurnaceV2.json
```

Claude should show side-by-side comparison and balance analysis.

#### Test 5: Natural Language Activation (Agent/Skill Activation)
Try natural language instead of commands:
```
I need a healing skill that consumes mana to restore health.
The healing effect should scale with spell power.
```

The Skill Configuration Expert agent or Game Skill System Expert should automatically activate.

#### Test 6: Validation Hooks
Create or edit a skill file, validation hooks should run automatically:
```
Create new file: Assets/Skills/TestSkill.json

Then modify and save
```

You should see validation messages after saving.

### Test Unity Compilation Plugin

#### Test 1: Intelligent Compilation
```
/compile
```

Claude should intelligently identify project type and execute compilation.

#### Test 2: Find Assembly
```
/find-assembly UnityEngine
```

## 🔧 Troubleshooting

### Commands Not Showing

If commands don't appear in `/help`:

1. Check if plugins are installed:
   ```
   /plugin
   ```

2. Verify marketplace is added:
   ```
   /plugin marketplace list
   ```

3. Check if plugins are enabled:
   ```
   /plugin list
   ```

4. Try reinstalling:
   ```
   # For remote installation:
   /plugin uninstall claude-standards@ai_agent_for_skill
   /plugin install claude-standards@ai_agent_for_skill

   # For local installation:
   /plugin uninstall claude-standards@nkg-game-development-marketplace
   /plugin install claude-standards@nkg-game-development-marketplace
   ```

5. Restart Claude Code

### Hooks Not Working

If validation hooks don't trigger:

1. Check if scripts are executable:
   ```bash
   cd claude_code_plugins/game-skill-config-plugin/scripts
   ls -la
   ```

   If not executable:
   ```bash
   chmod +x *.sh
   ```

2. Test scripts manually:
   ```bash
   ./validate-skill.sh "../../../ai_agent_for_skill/Assets/Skills/TryndamereBloodlust.json"
   ```

3. Check if Python is available:
   ```bash
   python3 --version
   ```

### Agents Not Activating

Agents should activate automatically when you mention skill configuration. If not:

1. Try using command first: `/skill-generate`
2. Specify explicitly: "Use the Skill Configuration Expert to help me..."
3. Reference skill file directly: "Analyze TryndamereBloodlust.json"

### Windows Path Issues

If you encounter path issues on Windows with local installation:

Use forward slashes or escaped backslashes:
```
/plugin marketplace add E:/Study/wqaetly/ai_agent_for_skill/claude_code_plugins
```

Or within your project:
```
cd E:\Study\wqaetly\ai_agent_for_skill
claude
/plugin marketplace add ./claude_code_plugins
```

**Recommended**: Use remote GitHub installation to avoid path issues:
```
/plugin marketplace add https://github.com/wqaetly/ai_agent_for_skill.git
```

### Development Standards Not Effective

If professional development standards are not effective:

1. Check if standards are loaded:
   ```
   /standards-status --module language-standards
   ```

2. Reload language standards:
   ```
   /standards-load --language
   ```

3. Check for configuration conflicts:
   ```
   /standards-config check-conflicts
   ```

## 📁 Plugin Structure

Your installed plugins have the following structure:

```
claude_code_plugins/
├── .claude-plugin/
│   └── marketplace.json         # Marketplace definition
├── claude-standards/            # Development standards plugin
│   ├── .claude-plugin/
│   │   └── plugin.json          # Plugin manifest
│   ├── prompts/                 # Prompt modules
│   ├── commands/                # Management commands
│   ├── hooks/                   # Hook configuration
│   ├── config/                  # Configuration files
│   ├── scripts/                 # Management scripts
│   └── README.md                # Documentation
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
    │       └── SKILL.md         # Agent skill
    ├── hooks/
    │   └── hooks.json           # Hook configuration
    ├── scripts/
    │   ├── validate-skill.sh    # Validation script
    │   └── detect-skill-intent.sh  # Intent detection
    ├── README.md                # Documentation
    ├── LICENSE                  # MIT License
    └── CHANGELOG.md             # Version history
```

## 🎯 Next Steps

After successful installation:

1. **Establish Development Standards** - First run `/standards-load` to establish professional development foundation
2. **Generate Your First Skill** - Try `/skill-generate` with simple concepts
3. **Analyze Existing Skills** - Use `/skill-analyze` to understand current skills
4. **Compare Balance** - Use `/skill-compare` to check skill balance
5. **Use Natural Language** - Describe requirements directly, let agents help

## 📞 Support

If you encounter issues:

1. Check this installation guide
2. Review main [README.md](claude-standards/README.md) and [README.md](game-skill-config-plugin/README.md)
3. Run Claude Code in debug mode: `claude --debug`
4. Check [CHANGELOG.md](game-skill-config-plugin/CHANGELOG.md)

## 🛠️ Development Mode

If you want to modify plugins:

1. Modify files in the relevant plugin directory
2. Uninstall:
   - Remote: `/plugin uninstall [plugin-name]@ai_agent_for_skill`
   - Local: `/plugin uninstall [plugin-name]@nkg-game-development-marketplace`
3. Reinstall:
   - Remote: `/plugin install [plugin-name]@ai_agent_for_skill`
   - Local: `/plugin install [plugin-name]@nkg-game-development-marketplace`
4. Restart Claude Code
5. Test your changes

## 🎮 Recommended Usage Workflow

1. **Installation Order**: claude-standards → game-skill-config → nkg-unity
2. **First Use**: Run `/standards-load` first to establish development standards
3. **Daily Development**: Use natural language to activate appropriate agents
4. **Quality Control**: Rely on automated hooks and validation mechanisms

Happy development! 🎮✨

**Professional development standards for modern development!** 🌟
