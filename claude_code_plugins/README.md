# Claude Code Plugins 🚀

This directory contains Claude Code plugins for game development and Unity tools.

## 📁 Directory Structure

```
claude_code_plugins/
├── .claude-plugin/
│   └── marketplace.json              # Plugin marketplace configuration
├── game-skill-config-plugin/         # Game skill configuration system
├── nkg-unity/                        # Unity C# compilation and error fixing
├── _documentation/                   # Claude Code documentation reference
├── INSTALLATION.md                   # Installation guide for all plugins
└── README.md                         # This file
```

## 🎮 Available Plugins

### 1. Game Skill Configuration Plugin
- **Name**: `game-skill-config`
- **Purpose**: Complete skill configuration and management system for Unity development
- **Features**:
  - Generate new skill configurations
  - Analyze existing skills
  - Debug skill issues
  - Compare skills for balance
  - Automatic validation hooks

### 2. NKG Unity Plugin
- **Name**: `nkg-unity`
- **Purpose**: Unity C# compilation and error fixing with intelligent assembly matching
- **Features**:
  - Smart assembly name resolution
  - Automatic compilation error fixing
  - Support for common Unity assembly aliases
  - Safe file backup and修复 strategies

## 🚀 Quick Installation

### Step 1: Add Marketplace
```bash
/plugin marketplace add ./claude_code_plugins
```

### Step 2: Install Plugins
```bash
# Install game skill configuration plugin
/plugin install game-skill-config@nkg-game-development-marketplace

# Install Unity compilation plugin
/plugin install nkg-unity@nkg-game-development-marketplace
```

### Step 3: Restart Claude Code
Exit and restart Claude Code to load the plugins.

## 📚 Documentation

- **[Installation Guide](INSTALLATION.md)** - Detailed installation and testing instructions
- **[_documentation/](./_documentation/)** - Claude Code reference documentation
- **[game-skill-config-plugin/README.md](./game-skill-config-plugin/README.md)** - Skill configuration plugin details
- **[nkg-unity/README.md](./nkg-unity/README.md)** - Unity compilation plugin details

## 🔧 Plugin Development

This marketplace is configured for the NKG Development Team and contains plugins specifically designed for Unity game development workflows.

## 📄 License

Individual plugins may have their own licenses. Please refer to each plugin's LICENSE file for specific terms.

---

**Enhance your Unity development workflow with intelligent Claude Code plugins!** 🎮✨