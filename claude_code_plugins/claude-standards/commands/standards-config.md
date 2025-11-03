# Configure Claude Development Standards

Configure and manage specific parameters and settings for Claude development standards, supporting project-level personalized configurations.

## Usage

```bash
/standards-config [options] [parameters]
```

## Configuration Options

### Language Settings
```bash
/standards-config language --primary en-US
/standards-config language --style direct
/standards-config language --comments english_with_space
```

### Work Principles Settings
```bash
/standards-config principles --quality-gate strict
/standards-config principles --architecture-aware true
/standards-config principles --incremental-improvement true
```

### Socratic Dialogue Settings
```bash
/standards-config socratic --auto-activate true
/standards-config socratic --intensity deep
/standards-config socratic --triggers "why,architecture,best practices"
```

### Quality Gate Settings
```bash
/standards-config quality --architecture-decay true
/standards-config quality --technical-debt threshold:high
/standards-config quality --performance-alert true
```

## Detailed Configuration Options

### Language Configuration (language)
- `--primary <lang>`: Primary language (en-US, zh-CN)
- `--style <style>`: Expression style (direct, formal, friendly)
- `--terms <format>`: Technical terms handling (keep_english, translate, mixed)
- `--comments <format>`: Comment format (english, chinese, mixed)

### Work Principles Configuration (principles)
- `--context-priority <bool>`: Project context priority
- `--architecture-aware <bool>`: Architecture awareness mode
- `--quality-oriented <level>`: Quality orientation level (strict, moderate, relaxed)
- `--incremental-only <bool>`: Allow only incremental improvements

### Socratic Dialogue Configuration (socratic)
- `--auto-activate <bool>`: Auto-activate deep dialogue
- `--intensity <level>`: Questioning intensity (gentle, deep, intense)
- `--triggers <keywords>`: Trigger keyword list
- `--timeout <seconds>`: Dialogue timeout

### Quality Gate Configuration (quality)
- `--architecture-decay <bool>`: Architecture decay detection
- `--debt-threshold <level>`: Technical debt threshold (low, medium, high)
- `--performance-alert <bool>`: Performance degradation alert
- `--maintainability-check <bool>`: Maintainability check

## Configuration File Management

### Save Configuration
```bash
/standards-config save --name my-project-config
/standards-config save --global
/standards-config save --project
```

### Load Configuration
```bash
/standards-config load --name my-project-config
/standards-config load --default
/standards-config load --file /path/to/config.json
```

### List Configurations
```bash
/standards-config list
/standards-config list --global
/standards-config list --local
```

### Delete Configuration
```bash
/standards-config delete --name my-project-config
/standards-config reset --to-default
```

## Configuration Examples

### Startup Project Configuration
```bash
/standards-config language --primary en-US --style direct
/standards-config principles --quality-oriented moderate --incremental-only true
/standards-config socratic --auto-activate false
/standards-config quality --debt-threshold medium
/standards-config save --name startup-config
```

### Enterprise Project Configuration
```bash
/standards-config language --primary en-US --style formal
/standards-config principles --quality-oriented strict --architecture-aware true
/standards-config socratic --auto-activate true --intensity deep
/standards-config quality --architecture-decay true --performance-alert true
/standards-config save --name enterprise-config
```

### Personal Project Configuration
```bash
/standards-config language --primary en-US --style direct
/standards-config principles --context-priority true
/standards-config socratic --auto-activate true --triggers "why,why this way"
/standards-config quality --maintainability-check true
/standards-config save --name personal-config
```

## Configuration Validation

### Validate Current Configuration
```bash
/standards-config validate
/standards-config validate --strict
/standards-config validate --show-conflicts
```

### Check Configuration Conflicts
```bash
/standards-config check-conflicts
/standards-config check-conflicts --with-plugin game-skill-config
```

## Advanced Features

### Configuration Templates
```bash
/standards-config template --list
/standards-config template --apply startup
/standards-config template --create --name custom-template
```

### Configuration Import/Export
```bash
/standards-config export --format json --file standards.json
/standards-config import --file standards.json
/standards-config import --url https://example.com/standards.json
```

### Team Synchronization
```bash
/standards-config sync --team
/standards-config sync --remote https://github.com/team/standards
/standards-config sync --push
```

## Output Format

### Configuration Success
```
✅ Claude development standards configuration updated

📋 Current configuration overview:
Language settings: English (direct style)
Work principles: Quality-oriented (strict mode)
Socratic dialogue: Smart activation (deep questioning)
Quality gates: All enabled

💾 Configuration saved to: .claude/standards/config.json
🔄 Restart session to apply new configuration
```

### Configuration Validation Results
```
🔍 Configuration validation results

✅ Passed checks:
- Language setting consistency
- Work principles compatibility
- Quality gate completeness

⚠️ Warnings:
- Socratic dialogue may conflict with other plugins
- Consider reducing questioning intensity to avoid over-questioning

❌ Errors:
- None

📊 Configuration health: 85/100
```