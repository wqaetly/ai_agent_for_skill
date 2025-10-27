# Changelog

All notable changes to the Game Skill Configuration Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-27

### Added

#### Commands
- `/skill-generate` - Generate new skill configurations from natural language descriptions
- `/skill-analyze` - Comprehensive analysis of existing skill configurations
- `/skill-debug` - Debug and fix skill configuration issues

#### Agents
- **Skill Configuration Specialist** - Specialized subagent for skill configuration tasks
  - Automatic invocation based on context
  - Expert knowledge of skill system architecture
  - Batch processing capabilities

#### Skills
- **Game Skill System Expert** - Model-invoked Agent Skill
  - Automatic activation for skill-related tasks
  - Complete knowledge base of action types and balance formulas
  - Read-only tool access for safety
  - Progressive disclosure of supporting documentation

#### Hooks
- **PostToolUse Validation** - Automatic validation after Write/Edit operations
  - JSON syntax checking
  - Required field validation
  - Common issue detection
- **UserPromptSubmit Intent Detection** - Suggests relevant commands
- **SessionStart Context Loading** - Loads skill system context at startup

#### Scripts
- `validate-skill.sh` - Validates skill JSON configurations
- `detect-skill-intent.sh` - Detects skill configuration intent

#### Documentation
- Comprehensive README with usage examples
- Installation instructions for marketplace and local development
- Complete skill system architecture reference
- Balance guidelines and timing recommendations
- Troubleshooting guide

### Features

- **Intelligent Generation**: Create production-ready skill configurations from descriptions
- **Deep Analysis**: Mechanical breakdowns, timeline visualization, balance evaluation
- **Smart Debugging**: Categorized issue detection (critical/warning/suggestion)
- **Automatic Validation**: Real-time validation with helpful error messages
- **Balance Guidelines**: Built-in knowledge of appropriate values for different skill types
- **Scaling Formulas**: Automatic calculation of damage/healing at various levels
- **Timing Optimization**: Frame-perfect timing recommendations
- **Quality Checks**: Code quality assessment and suggestions

### Supported Action Types

- AttributeScaledDamageAction
- UnitTypeCappedDamageAction
- ResourceDependentHealAction
- AttributeScaledShieldAction
- InputDetectionAction
- AnimationAction
- AudioAction
- ResourceAction

### Balance Guidelines

#### Damage Skills
- Basic: 60-100 base, 0.4-0.6 SP ratio
- Major: 100-200 base, 0.6-0.9 SP ratio
- Ultimate: 200-400 base, 0.8-1.2 SP ratio

#### Healing Skills
- Basic: 40-80 base, 0.3-0.5 SP ratio
- Major: 80-150 base, 0.5-0.8 SP ratio

#### Shield Skills
- Basic: 50-100 base, 0.3-0.5 SP ratio
- Major: 100-200 base, 0.5-0.8 SP ratio

### Technical Details

- Supports Unity-based skill systems
- Compatible with SkillData serialization format
- Bash scripts for hooks (requires Bash)
- Python 3 for JSON validation
- Claude Code 1.0+ required

## [Unreleased]

### Planned Features

- Visual skill timeline editor integration
- Balance testing framework
- Multi-skill comparison reports
- Skill template library
- Custom action type support
- Performance profiling for complex skills
- Export to different formats (CSV, XML)
- Skill versioning and migration tools

### Ideas for Future Releases

- Integration with Unity editor via MCP server
- Real-time testing in Unity
- AI-powered balance suggestions
- Community skill library
- Automatic documentation generation
- Localization support for skill descriptions
- Custom validation rules
- Skill dependency graph visualization

---

## Version History Legend

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to this project.

## Support

For issues, questions, or feature requests:
- GitHub Issues: [your-org/game-skill-config-plugin/issues]
- Documentation: [README.md](README.md)
