# Claude Development Standards Plugin

[![Plugin Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/wqaetly/ai_agent_for_skill)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Category](https://img.shields.io/badge/category-Code%20Quality-orange.svg)](https://claude.ai)

Provides unified development standards for Claude Code, including language expression, work principles, Socratic dialogue, and technical analysis frameworks.

## 🌟 Core Features

### 🗣️ Communication Standards
- **Clarity First**: Prioritize clear, direct communication in all interactions and documentation
- **Direct & Focused**: Eliminate unnecessary pleasantries, get straight to the core issues
- **Technical Accuracy**: Maintain precise technical terminology with clear explanations
- **Zero Fluff**: Every sentence should deliver substantial information value

### ⚙️ Core Work Principles
- **Context Priority**: Develop solutions based on existing technology stack and project constraints
- **Quality Oriented**: Deliver high-quality, targeted solutions with attention to detail
- **Architecture Awareness**: Incremental optimization, avoiding disruptive refactoring
- **Technical Debt Management**: Balance fix costs against refactoring investments

### 🤔 Socratic Dialogue Framework
- **Smart Activation**: Automatically trigger deep discussions based on keyword detection
- **Tiered Questioning**: Gentle inquiry → Deep questioning → Intense challenge
- **Flow Control**: Prevent endless questioning with intelligent termination timing
- **Constructive Challenge**: Every question should provide direction for improvement

### 🔍 Technical Analysis Framework
- **Data Structure Review**: Identify core data entities and their relationships
- **Data Flow Tracking**: Analyze flow patterns, ownership, and modification permissions
- **Efficiency Audit**: Identify redundant operations and performance bottlenecks
- **Architecture Trade-offs**: Balance performance, maintainability, and scalability

## 🚀 Quick Start

### Install Plugin
```bash
# Clone to Claude Code plugins directory
git clone https://github.com/wqaetly/ai_agent_for_skill.git claude_code_plugins/claude-standards

# Or copy plugin files to Claude Code plugins directory
cp -r claude-standards ~/.claude/plugins/
```

### Basic Usage

#### 1. Load All Standards
```bash
/standards-load
```

#### 2. For Specific Scenarios
```bash
/standards-load --code-review    # Code review scenario
/standards-load --architecture   # Architecture design scenario
/standards-load --planning      # Technical planning scenario
```

#### 3. Interactive Selection
```bash
/standards-load --interactive
```

#### 4. Check Current Status
```bash
/standards-status
/standards-status --detailed
```

#### 5. Configure Standard Parameters
```bash
/standards-config language --primary en-US
/standards-config socratic --auto-activate true
/standards-config quality --architecture-decay true
```

## 📋 Command Reference

### `/standards-load` - Load Standards

```bash
/standards-load [options]
```

**Options:**
- `--all`: Load all standards modules (default)
- `--language`: Load only communication standards
- `--principles`: Load only core work principles
- `--socratic`: Load only Socratic dialogue framework
- `--analysis`: Load only technical analysis framework
- `--code-review`: Code review scenario configuration
- `--architecture`: Architecture design scenario configuration
- `--planning`: Technical planning scenario configuration
- `--interactive`: Interactive selection
- `--dry-run`: Preview mode

### `/standards-config` - Configure Standards

```bash
/standards-config <module> <option> <value>
```

**Language Configuration:**
```bash
/standards-config language --primary en-US
/standards-config language --style direct
/standards-config language --comments professional
```

**Work Principles Configuration:**
```bash
/standards-config principles --quality-gate strict
/standards-config principles --architecture-aware true
```

**Socratic Dialogue Configuration:**
```bash
/standards-config socratic --auto-activate true
/standards-config socratic --intensity deep
/standards-config socratic --triggers "why,architecture,best practices"
```

### `/standards-status` - Check Status

```bash
/standards-status [options]
```

**Options:**
- `--detailed`: Show detailed configuration information
- `--summary`: Show summary information
- `--json`: JSON format output
- `--module <name>`: Show specific module status
- `--usage`: Show usage statistics

## ⚙️ Configuration Details

### Language Configuration
```json
{
  "language": {
    "primary": "en-US",
    "technical_terms": "keep_english_with_explanation",
    "comment_style": "professional",
    "expression_style": {
      "directness": "high",
      "sharpness": "high",
      "zero_fluff": true
    }
  }
}
```

### Work Principles Configuration
```json
{
  "work_principles": {
    "context_priority": true,
    "architecture_awareness": true,
    "quality_oriented": "strict",
    "incremental_improvement": true
  }
}
```

### Socratic Dialogue Configuration
```json
{
  "socratic_dialogue": {
    "enabled": true,
    "auto_activate": true,
    "triggers": ["why", "architecture", "best practices", "trade-offs"],
    "intensity_levels": {
      "gentle_inquiry": "Reasonable approach, explore optimizations",
      "deep_questioning": "Potential risks identified, needs justification",
      "intense_refutation": "Critical flaws found, must challenge"
    }
  }
}
```

## 🎯 Usage Scenarios

### Code Review
```bash
/standards-load --code-review
```
- Apply strict quality gate checks
- Focus on architectural soundness
- Identify technical debt and performance issues
- Provide specific improvement recommendations

### Architecture Design
```bash
/standards-load --architecture
```
- Systematic architectural decision trade-offs
- In-depth technology selection analysis
- Design solution comparison and evaluation
- Long-term maintainability considerations

### Technical Planning
```bash
/standards-load --planning
```
- Implementation path design
- Technical debt management strategies
- Team capability matching assessment
- Migration risk analysis

### Debugging
```bash
/standards-load --debugging
```
- Systematic problem analysis
- Root cause localization methodology
- Debugging strategy development
- Solution verification

## 🔧 Advanced Features

### Configuration Templates
```bash
/standards-config template --list
/standards-config template --apply startup
/standards-config template --create --name custom
```

### Team Synchronization
```bash
/standards-config sync --team
/standards-config sync --remote https://github.com/team/standards
```

### Configuration Import/Export
```bash
/standards-config export --file my-standards.json
/standards-config import --file my-standards.json
```

## 📊 Quality Checks

### Automatic Quality Checks
The plugin automatically triggers quality checks in the following situations:
- After code editing (PostToolUse)
- During technical documentation analysis (PreToolUse)
- When user prompts contain deep discussion keywords (UserPrompt)

### Quality Check Rules
- **Architecture Decay Detection**: Complexity, coupling, code duplication
- **Technical Debt Thresholds**: TODO comments, deprecated APIs, security issues
- **Maintainability Checks**: Long methods, deep nesting, naming conventions

## 🔍 Troubleshooting

### Common Issues

**Plugin Not Activated:**
```bash
# Check plugin status
/standards-status --check

# Reload plugin
/standards-load --force
```

**Configuration Conflicts:**
```bash
# Check configuration conflicts
/standards-config check-conflicts

# Reset to default configuration
/standards-config reset --to-default
```

**Language Standards Not Applied:**
```bash
# Check language configuration
/standards-status --module language-standards

# Reapply language standards
/standards-load --language
```

## 🤝 Contributing Guidelines

### Development Environment
```bash
git clone https://github.com/wqaetly/ai_agent_for_skill.git
cd claude_code_plugins/claude-standards
```

### Adding New Standard Modules
1. Create new `.md` file in `prompts/` directory
2. Add configuration in `config/default-config.json`
3. Update module descriptions in `scripts/apply-standards.py`
4. Test new module functionality

### Submission Guidelines
- Follow existing code style
- Update relevant documentation
- Add test cases
- Run full tests before submission

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Thanks to the Claude Code team for providing an excellent plugin architecture that makes development standards management possible.

## 📞 Contact

- Project Homepage: https://github.com/wqaetly/ai_agent_for_skill
- Issue Reporting: https://github.com/wqaetly/ai_agent_for_skill/issues
- Email: wqaetly@example.com

---

**Empowering Claude Code with Professional Development Standards!** 🚀