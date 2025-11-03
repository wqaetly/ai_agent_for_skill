# Load Claude Development Standards

Load specified Claude development standards into the current session. This command intelligently selects and applies appropriate prompt standards based on project requirements and application scenarios.

## Usage

```bash
/standards-load [options]
```

## Options

### Standard Types
- `--all`: Load all standard modules (default)
- `--language`: Load only language expression standards
- `--principles`: Load only core work principles
- `--socratic`: Load only Socratic dialogue standards
- `--analysis`: Load only technical analysis framework

### Application Scenarios
- `--code-review`: Code review scenario optimized configuration
- `--architecture`: Architecture design scenario optimized configuration
- `--planning`: Technical planning scenario optimized configuration
- `--debugging`: Problem debugging scenario optimized configuration

### Configuration Options
- `--interactive`: Interactive selection of standard configuration
- `--force`: Force reload, overriding existing configuration
- `--dry-run`: Preview standards to be loaded without actually applying

## Examples

```bash
# Load all standards
/standards-load

# Load standards specifically for code review scenario
/standards-load --code-review

# Interactive selection of standards
/standards-load --interactive

# Load only language and technical analysis standards
/standards-load --language --analysis
```

## Features

### Intelligent Standard Selection
- Automatically recommend standard combinations based on current project type
- Adjust configuration based on recently used tools and commands
- Detect file types and application scenarios to optimize prompts

### Configuration Persistence
- Save standard configuration to project locally
- Support team sharing of standard configurations
- Versioned standard update mechanism

### Conflict Detection
- Detect configuration conflicts with other plugins
- Provide conflict resolution suggestions
- Support configuration priority settings

## Output Format

### Successful Load
```
✅ Claude development standards loaded successfully

📋 Loaded standard modules:
├── Language Expression Standards (en-US, direct sharp style)
├── Core Work Principles (quality-oriented, architecture-aware)
├── Socratic Dialogue (smart activation)
└── Technical Analysis Framework (systematic analysis)

⚙️ Configuration details:
- Primary language: English
- Expression style: Direct, zero-fluff
- Quality gates: Strict mode
- Dialogue mode: Smart activation

💡 Usage tips:
- Use keywords like "why" to trigger deep discussions
- Code reviews will automatically apply quality gate checks
- Technical analysis will use systematic framework
```

### Interactive Selection
```
🎯 Please select standard modules to load:

1. Language Expression Standards - English communication, direct sharp style
2. Core Work Principles - Quality-oriented, architecture-aware
3. Socratic Dialogue - Deep questioning, smart activation
4. Technical Analysis Framework - Systematic analysis tools

Please enter numbers to select (comma-separated for multiple, or select 0 to load all):
```