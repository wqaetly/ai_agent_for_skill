# Claude Code 插件集合 🚀

本目录包含用于游戏开发和 Unity 工具的 Claude Code 插件。

## 📁 目录结构

```
claude_code_plugins/
├── .claude-plugin/
│   └── marketplace.json              # 插件市场配置
├── claude-standards/                 # Claude 开发规范插件 (新增)
├── game-skill-config-plugin/         # 游戏技能配置系统
├── nkg-unity/                        # Unity C# 编译和错误修复
├── _documentation/                   # Claude Code 文档参考
├── INSTALLATION.md                   # 所有插件的安装指南
└── README.md                         # 本文件
```

## 🎮 可用插件

### 1. Claude 开发规范插件 ⭐ (新增)
- **名称**: `claude-standards`
- **用途**: 提供统一的中文开发规范，包括语言表达、工作原则、苏格拉底式对话和技术分析框架
- **特性**:
  - 中文交流规范，直接犀利风格
  - 核心工作原则，质量导向
  - 苏格拉底式技术对话，智能激活
  - 系统性技术分析框架
  - 自动化质量检查钩子

### 2. 游戏技能配置插件
- **名称**: `game-skill-config`
- **用途**: Unity 开发的完整技能配置和管理系统
- **特性**:
  - 生成新的技能配置
  - 分析现有技能
  - 调试技能问题
  - 技能平衡性对比
  - 自动验证钩子

### 3. NKG Unity 插件
- **名称**: `nkg-unity`
- **用途**: Unity C# 编译和错误修复，具有智能程序集匹配功能
- **特性**:
  - 智能程序集名称解析
  - 自动编译错误修复
  - 支持常见的 Unity 程序集别名
  - 安全的文件备份和修复策略

## 🚀 快速安装

### 步骤 1: 添加插件市场
```bash
/plugin marketplace add ./claude_code_plugins
```

### 步骤 2: 安装插件
```bash
# 安装 Claude 开发规范插件
/plugin install claude-standards@nkg-game-development-marketplace

# 安装游戏技能配置插件
/plugin install game-skill-config@nkg-game-development-marketplace

# 安装 Unity 编译插件
/plugin install nkg-unity@nkg-game-development-marketplace
```

### 步骤 3: 重启 Claude Code
退出并重启 Claude Code 以加载插件。

## 📚 文档

- **[安装指南](INSTALLATION.md)** - 详细的安装和测试说明
- **[_documentation/](./_documentation/)** - Claude Code 参考文档
- **[claude-standards/README.md](./claude-standards/README.md)** - 开发规范插件详情
- **[game-skill-config-plugin/README.md](./game-skill-config-plugin/README.md)** - 技能配置插件详情
- **[nkg-unity/README.md](./nkg-unity/README.md)** - Unity 编译插件详情

## 🔧 插件开发

此插件市场为 NKG 开发团队配置，包含专门为 Unity 游戏开发工作流程设计的插件。

## 🎯 推荐使用顺序

1. **首先安装 `claude-standards`** - 建立中文开发规范基础
2. **然后安装 `game-skill-config`** - 配置游戏技能系统
3. **最后安装 `nkg-unity`** - 支持 Unity 编译和调试

## 📄 许可证

各个插件可能有各自的许可证。请参考每个插件的 LICENSE 文件了解具体条款。

---

**用智能的 Claude Code 插件增强您的 Unity 开发工作流程！** 🎮✨

**让 Claude 更懂中文开发规范！** 🇨🇳