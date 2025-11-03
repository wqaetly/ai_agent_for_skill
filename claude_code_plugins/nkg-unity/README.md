# NKG Unity Plugin 🚀

Unity C# 编译和错误修复的智能Claude Code插件。

## ✨ 核心特性

- **智能程序集匹配**: 使用别名和模糊匹配找到正确的程序集
- **自动编译修复**: 智能识别并修复常见Unity C#编译错误
- **安全机制**: 文件备份和保守修复策略
- **用户友好**: 无需记住复杂的程序集名称

## 🚀 快速开始

### 安装插件
```bash
# 添加NKG游戏开发市场
/plugin marketplace add ./claude_code_plugins

# 安装NKG Unity编译插件
/plugin install nkg-unity@nkg-game-development-marketplace

# 重启Claude Code
```

### 使用方法

#### 智能编译命令
```bash
# 使用别名编译 - 无需记住完整程序集名称！
/compile main          # 编译主程序集 (Assembly-CSharp)
/compile editor        # 编译编辑器程序集 (Assembly-CSharp-Editor)
/compile MyGame        # 智能匹配 MyGameLogic.csproj
/compile UI            # 智能匹配 UIManager.csproj

# 查找程序集
/find-assembly main
/find-assembly editor
/find-assembly MyGame
```

#### 支持的别名对照表
| 输入别名 | 映射到程序集 | 用途说明 |
|---------|-------------|----------|
| `main`, `primary`, `game`, `runtime` | `Assembly-CSharp` | 主游戏逻辑程序集 |
| `editor`, `edit`, `editor-scripts` | `Assembly-CSharp-Editor` | 编辑器扩展程序集 |
| `firstpass`, `preimport`, `pre-import` | `Assembly-CSharp-firstpass` | 预导入程序集 |
| `editor-firstpass`, `editor-preimport` | `Assembly-CSharp-Editor-firstpass` | 编辑器预导入程序集 |

## 🔧 支持的错误修复

插件可以自动修复以下类型的编译错误：

- ✅ **CS0103**: 缺失using语句 → 自动添加 `using UnityEngine;` 等
- ✅ **CS0246**: 类型或命名空间不存在 → 修复拼写错误，添加引用
- ✅ **CS0117**: 成员不存在 → 修复API调用错误
- ✅ **CS1061**: 扩展方法不存在 → 添加 `using System.Linq;`
- ✅ **CS0029**: 类型转换错误 → 添加显式转换
- ✅ **CS1503**: 参数不匹配 → 修复方法签名

## 📁 插件结构

```
nkg-unity/
├── .claude-plugin/
│   └── plugin.json                    # 插件元数据
├── commands/
│   ├── compile.md                     # 🔨 智能编译命令
│   └── find-assembly.md               # 🔍 程序集查找命令
├── scripts/
│   └── smart-assembly-resolver.sh     # 🧠 智能匹配脚本
└── README.md                          # 本文档
```

## 🎮 使用示例

### 场景1: 快速编译主程序集
```bash
/compile main
```
输出：
```
🔍 Searching for assembly: main
📝 Resolved alias: main → Assembly-CSharp
✅ Found exact match: ./Assembly-CSharp.csproj
🎨 Compiling and fixing errors...
✅ Build succeeded! Fixed 2 errors automatically.
```

### 场景2: 智能匹配自定义程序集
```bash
/compile MyGame
```
输出：
```
🔍 Searching for assembly: MyGame
🎯 Fuzzy match: ./MyGameLogic.csproj
🎨 Compiling and fixing errors...
✅ Build succeeded! No errors found.
```

## 🛠️ 技术特点

### 智能匹配算法
- **多层级搜索**: 精确匹配 → 别名映射 → 模糊匹配 → 模式匹配
- **优先级排序**: 根据相关性选择最佳匹配项
- **容错设计**: 处理各种用户输入情况

### 安全修复机制
- **文件备份**: 修改前自动创建备份
- **保守策略**: 只修复确信的错误类型
- **验证机制**: 修复后重新编译验证

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个插件！

## 📄 许可证

MIT License

---

**让Unity编译变得简单而智能！** 🎮✨