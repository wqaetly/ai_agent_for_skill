# View Claude Development Standards Status

Display currently loaded Claude development standards configuration, activation status, and usage statistics.

## Usage

```bash
/standards-status [options]
```

## Options

### Display Options
- `--detailed`: Show detailed configuration information
- `--summary`: Show summary information (default)
- `--json`: Output in JSON format
- `--active-only`: Show only activated standard modules

### Filter Options
- `--module <name>`: Show specific module status
- `--recent`: Show recently used standards
- `--usage`: Show usage statistics

## Output Format

### Summary Mode
```bash
/standards-status
```

Output:
```
📊 Claude development standards status

🟢 Active modules (4/4):
├── Language Expression Standards ✅ English communication, direct sharp
├── Core Work Principles ✅ Quality-oriented, architecture-aware
├── Socratic Dialogue ✅ Smart activation, deep questioning
└── Technical Analysis Framework ✅ Systematic analysis tools

⚙️ Current configuration:
- Session language: English (US)
- Expression style: Direct, zero-fluff
- Quality checks: Strict mode
- Dialogue mode: Smart activation

📈 Usage statistics:
- Today's activations: 15
- Most used module: Technical Analysis Framework
- Quality checks triggered: 3 times
```

### Detailed Mode
```bash
/standards-status --detailed
```

Output:
```
📊 Claude development standards detailed status

🟢 Language Expression Standards
├── Primary language: English (US)
├── Technical terms handling: Keep English + English explanations
├── Comment format: // + space + English comments
├── Expression style: Direct sharp, zero-fluff
├── Technical judgment: Accurate over friendly
└── Activation status: ✅ Activated

🟢 Core Work Principles
├── Project context priority: ✅ Enabled
├── Architecture awareness mode: ✅ Enabled
├── Quality-oriented strategy: Strict mode
├── Incremental improvement principle: ✅ Enabled
├── Technical debt threshold: High
└── Activation status: ✅ Activated

🟢 Socratic Dialogue
├── Auto activation: ✅ Enabled
├── Questioning intensity: Deep questioning
├── Trigger keywords: why,architecture,best practices,brainstorm,why,architecture
├── Dialogue flow: Question→Explore→Trade-off→Consensus
├── Termination conditions: ✅ Smart judgment
└── Activation status: ✅ Activated

🟢 Technical Analysis Framework
├── Data structure scrutiny: ✅ Enabled
├── Data flow tracking: ✅ Enabled
├── Efficiency review: ✅ Enabled
├── Architecture decision trade-offs: ✅ Enabled
├── Analysis templates: ✅ Loaded
└── Activation status: ✅ Activated

📈 Usage statistics (last 7 days)
├── Language standards applications: 45 times
├── Work principles references: 28 times
├── Socratic dialogues: 12 times
├── Technical analysis executions: 37 times
├── Quality checks triggered: 8 times
└── Configuration modifications: 3 times

🔧 Configuration information
├── Configuration file: .claude/standards/config.json
├── Last updated: 2024-01-15 14:30
├── Configuration version: 1.0.0
├── Plugin version: 1.0.0
└── Sync status: ✅ Synchronized

⚠️ Notes
- Potential configuration conflicts detected with other plugins
- Recommend regular configuration update checks
```

### JSON Format
```bash
/standards-status --json
```

Output:
```json
{
  "status": "active",
  "modules": {
    "language_standards": {
      "enabled": true,
      "config": {
        "primary_language": "en-US",
        "expression_style": "direct_sharp",
        "technical_terms": "keep_english_with_explanation"
      },
      "usage_count": 45
    },
    "work_principles": {
      "enabled": true,
      "config": {
        "context_priority": true,
        "architecture_awareness": true,
        "quality_level": "strict"
      },
      "usage_count": 28
    },
    "socratic_dialogue": {
      "enabled": true,
      "config": {
        "auto_activate": true,
        "intensity_level": "deep",
        "triggers": ["why", "architecture", "best practices"]
      },
      "usage_count": 12
    },
    "technical_analysis": {
      "enabled": true,
      "config": {
        "data_structure_scrutiny": true,
        "architectural_trade_offs": true
      },
      "usage_count": 37
    }
  },
  "statistics": {
    "total_activations": 122,
    "quality_checks_triggered": 8,
    "last_updated": "2024-01-15T14:30:00Z"
  }
}
```

### Specific Module Status
```bash
/standards-status --module socratic-dialogue
```

Output:
```
🔍 Socratic Dialogue Module Status

✅ Activation status: Enabled
🎯 Questioning intensity: Deep questioning
🔑 Trigger keywords: 6 keywords
⚡ Auto activation: Enabled
📊 Today's usage: 3 times
⏱️ Average dialogue duration: 5 minutes

Recent dialogue records:
1. Deep discussion about microservices architecture (14:25)
2. Database design scheme questioning (11:30)
3. Cache strategy optimization discussion (09:15)
```

### Usage Statistics
```bash
/standards-status --usage
```

Output:
```
📈 Usage Statistics Analysis

🕐 Time distribution (last 7 days)
├── Monday: 18 activations
├── Tuesday: 22 activations
├── Wednesday: 15 activations
├── Thursday: 25 activations
├── Friday: 20 activations
├── Saturday: 12 activations
└── Sunday: 10 activations

📊 Module usage ranking
1. Technical Analysis Framework: 37 times (30.3%)
2. Language Expression Standards: 45 times (36.9%)
3. Core Work Principles: 28 times (23.0%)
4. Socratic Dialogue: 12 times (9.8%)

🎯 Trigger scenario analysis
- Code reviews: 35 times (28.7%)
- Architecture discussions: 28 times (23.0%)
- Technical solutions: 25 times (20.5%)
- Problem debugging: 18 times (14.8%)
- Other: 16 times (13.1%)

💡 Usage suggestions
- Consider using Socratic dialogue more during code reviews
- Technical analysis framework usage frequency is good, keep it up
```

## Troubleshooting

### Check Configuration Issues
```bash
/standards-status --check
```

### Show Health Check
```bash
/standards-status --health
```

### Show Diagnostic Information
```bash
/standards-status --diagnostic
```