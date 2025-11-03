# NKG Unity Plugin 🚀

Intelligent Claude Code plugin for Unity C# compilation and error fixing.

## ✨ Core Features

- **Smart Assembly Matching**: Use aliases and fuzzy matching to find the correct assembly
- **Automatic Compilation Fixing**: Intelligently identify and fix common Unity C# compilation errors
- **Safety Mechanisms**: File backups and conservative fixing strategies
- **User-Friendly**: No need to remember complex assembly names

## 🚀 Quick Start

### Plugin Installation
```bash
# Add NKG Game Development Marketplace
/plugin marketplace add ./claude_code_plugins

# Install NKG Unity Compilation Plugin
/plugin install nkg-unity@nkg-game-development-marketplace

# Restart Claude Code
```

### Usage

#### Smart Compilation Commands
```bash
# Compile using aliases - no need to remember full assembly names!
/compile main          # Compile main assembly (Assembly-CSharp)
/compile editor        # Compile editor assembly (Assembly-CSharp-Editor)
/compile MyGame        # Smart match MyGameLogic.csproj
/compile UI            # Smart match UIManager.csproj

# Find assemblies
/find-assembly main
/find-assembly editor
/find-assembly MyGame
```

#### Supported Alias Mapping Table
| Input Alias | Maps to Assembly | Description |
|-------------|-----------------|-------------|
| `main`, `primary`, `game`, `runtime` | `Assembly-CSharp` | Main game logic assembly |
| `editor`, `edit`, `editor-scripts` | `Assembly-CSharp-Editor` | Editor extension assembly |
| `firstpass`, `preimport`, `pre-import` | `Assembly-CSharp-firstpass` | Pre-import assembly |
| `editor-firstpass`, `editor-preimport` | `Assembly-CSharp-Editor-firstpass` | Editor pre-import assembly |

## 🔧 Supported Error Fixes

The plugin can automatically fix the following types of compilation errors:

- ✅ **CS0103**: Missing using statements → Automatically add `using UnityEngine;` etc.
- ✅ **CS0246**: Type or namespace does not exist → Fix typos, add references
- ✅ **CS0117**: Member does not exist → Fix API call errors
- ✅ **CS1061**: Extension method does not exist → Add `using System.Linq;`
- ✅ **CS0029**: Type conversion error → Add explicit conversion
- ✅ **CS1503**: Parameter mismatch → Fix method signatures

## 📁 Plugin Structure

```
nkg-unity/
├── .claude-plugin/
│   └── plugin.json                    # Plugin metadata
├── commands/
│   ├── compile.md                     # 🔨 Smart compilation command
│   └── find-assembly.md               # 🔍 Assembly search command
│   └── nkg-git-commit.md              # 🚀 Git rebase, commit, push command
├── scripts/
│   └── smart-assembly-resolver.sh     # 🧠 Smart matching script
└── README.md                          # This documentation
```

## 🎮 Usage Examples

### Scenario 1: Quick Main Assembly Compilation
```bash
/compile main
```
Output:
```
🔍 Searching for assembly: main
📝 Resolved alias: main → Assembly-CSharp
✅ Found exact match: ./Assembly-CSharp.csproj
🎨 Compiling and fixing errors...
✅ Build succeeded! Fixed 2 errors automatically.
```

### Scenario 2: Smart Custom Assembly Matching
```bash
/compile MyGame
```
Output:
```
🔍 Searching for assembly: MyGame
🎯 Fuzzy match: ./MyGameLogic.csproj
🎨 Compiling and fixing errors...
✅ Build succeeded! No errors found.
```

## 🛠️ Technical Features

### Smart Matching Algorithm
- **Multi-level Search**: Exact match → Alias mapping → Fuzzy matching → Pattern matching
- **Priority Sorting**: Select best match based on relevance
- **Fault-tolerant Design**: Handle various user input scenarios

### Safe Fixing Mechanism
- **File Backup**: Automatically create backups before modifications
- **Conservative Strategy**: Only fix confident error types
- **Verification Mechanism**: Re-compile to verify fixes

## 🤝 Contributing

Issues and Pull Requests are welcome to improve this plugin!

## 📄 License

MIT License

---

**Making Unity compilation simple and intelligent!** 🎮✨