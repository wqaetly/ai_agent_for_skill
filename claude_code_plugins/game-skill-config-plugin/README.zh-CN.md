# 游戏技能配置插件

Unity 技能系统的全面 Claude Code 插件。从自然语言描述生成、分析、调试和优化游戏技能 JSON 配置。

> **语言：** [English](README.md) | 简体中文

## ✨ 功能特性

### 🎯 专业命令

**`/skill-generate [描述]`** - 生成新技能配置
- 从自然语言描述创建完整的技能 JSON
- 智能询问以收集需求
- 基于游戏设计原则的平衡数值
- 生产就绪的输出，包含所有必需字段

**`/skill-analyze <文件路径>`** - 分析现有技能
- 全面的机制分解
- 时间轴可视化
- 不同等级的平衡评估
- 质量评估和建议
- 多技能对比分析

**`/skill-debug <文件路径>`** - 调试技能问题
- 验证 JSON 语法和结构
- 识别时机和逻辑错误
- 修复平衡和性能问题
- 分类问题报告（严重/警告/建议）
- 自动更正并附带说明

**`/skill-list`** - 列出所有技能
- 显示项目中所有技能的摘要
- 统计信息和快速概览
- 按类型、英雄或复杂度过滤

**`/skill-compare <技能1> <技能2>`** - 对比技能
- 并排机制对比
- 平衡分析
- 识别设计模式和不一致性

### 🤖 智能代理

**技能配置专家 (Skill Configuration Specialist)**
- 处理技能配置任务时自动调用
- 理解完整的技能系统架构
- 提供生成、分析和调试的专家指导
- 批处理能力

### 🧠 Agent Skill

**游戏技能系统专家 (Game Skill System Expert)**
- 模型自动调用的专业知识
- 深入了解 SkillData、轨道、Action 和时机
- 平衡公式和缩放指南
- 最佳实践和质量标准
- 只读工具访问，确保安全

### 🔌 自动化钩子

**自动验证**
- Write/Edit 操作后验证技能 JSON
- 检查语法、必填字段和常见问题
- 提供潜在问题的警告

**意图检测**
- 根据你的请求建议相关命令
- 处理技能时提供有用提示

**会话上下文**
- 启动时加载技能系统上下文
- 随时准备提供帮助

## 🚀 安装

### 从本地目录

1. 添加 Marketplace：
   ```
   /plugin marketplace add E:\Study\wqaetly\ai_agent_for_skill\claude_code_plugins
   ```

2. 安装插件：
   ```
   /plugin install game-skill-config@game-dev-plugins
   ```

3. 重启 Claude Code

4. 验证安装：
   ```
   /help
   ```
   你应该能看到所有新命令。

详细安装指南请参见 [INSTALLATION.md](../INSTALLATION.md)

## 📖 使用方法

### 快速开始

**生成新技能：**
```
/skill-generate 为法师创建一个火球技能，造成魔法伤害
```

**分析现有技能：**
```
/skill-analyze Assets/Skills/TryndamereBloodlust.json
```

**调试技能：**
```
/skill-debug Assets/Skills/SionSoulFurnace.json
```

**列出所有技能：**
```
/skill-list
```

**对比技能平衡：**
```
/skill-compare TryndamereBloodlust.json SionSoulFurnaceV2.json
```

### 自然语言

插件会在你使用自然语言时自动激活：

```
"我需要一个消耗怒气来恢复生命的治疗技能"
"分析所有伤害技能并对比它们的平衡性"
"为什么我的护盾技能不工作？"
"创建 5 个闪电打击技能的变体"
```

技能配置专家代理或游戏技能系统专家会自动介入。

## 🎮 技能系统架构

### 支持的 Action 类型

**伤害类：**
- `AttributeScaledDamageAction` - 基于属性缩放的伤害
- `UnitTypeCappedDamageAction` - 对不同单位类型有伤害上限

**治疗类：**
- `ResourceDependentHealAction` - 基于资源消耗的治疗

**护盾类：**
- `AttributeScaledShieldAction` - 基于属性缩放的护盾

**控制类：**
- `InputDetectionAction` - 玩家输入检测以触发条件效果

**动画/音频：**
- `AnimationAction` - 播放动画
- `AudioAction` - 播放音效（2D/3D 空间音频）

**资源：**
- `ResourceAction` - 修改资源（法力、怒气、能量等）

### 平衡指南

内置的平衡数值知识：

| 技能类型 | 基础伤害 | 法强系数 | 每级成长 |
|----------|---------|---------|---------|
| 基础技能 | 60-100 | 0.4-0.6 | 10-15 |
| 主要技能 | 100-200 | 0.6-0.9 | 15-25 |
| 终极技能 | 200-400 | 0.8-1.2 | 25-40 |

### 时间指南

| 类型 | 持续时间 | 帧数 @ 30fps |
|------|----------|--------------|
| 瞬发 | 0.1-0.3秒 | 3-9 |
| 快速 | 0.25-0.5秒 | 8-15 |
| 标准 | 0.5-1.5秒 | 15-45 |
| 引导 | 2-4秒 | 60-120 |

## 📁 插件结构

```
game-skill-config-plugin/
├── .claude-plugin/
│   └── plugin.json              # 插件清单
├── commands/                    # 5 个专业命令
│   ├── skill-generate.md
│   ├── skill-analyze.md
│   ├── skill-debug.md
│   ├── skill-list.md
│   └── skill-compare.md
├── agents/                      # 专业代理
│   └── skill-config-specialist.md
├── skills/                      # Agent Skill
│   └── skill-system-expert/
│       └── SKILL.md
├── hooks/                       # 自动化钩子
│   └── hooks.json
├── scripts/                     # 验证脚本
│   ├── validate-skill.sh
│   └── detect-skill-intent.sh
├── README.md                    # 英文文档
├── README.zh-CN.md             # 中文文档（本文件）
├── LICENSE                      # MIT 许可
└── CHANGELOG.md                 # 版本历史
```

## 🔧 配置

### 自定义验证

编辑 `hooks/hooks.json` 以自定义验证行为：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-skill.sh \"${FILE_PATH}\""
          }
        ]
      }
    ]
  }
}
```

### 使用自定义脚本扩展

在 `scripts/` 目录中添加你自己的验证或处理脚本，并在钩子中引用它们。

## 🐛 故障排除

### 插件未加载

1. 检查插件已安装：`/plugin`
2. 验证安装：`/plugin list`
3. 检查错误：`claude --debug`

### 命令未显示

1. 确保插件已启用：`/plugin enable game-skill-config`
2. 重启 Claude Code
3. 检查 `/help` 中的新命令

### 钩子未触发

1. 验证脚本可执行：`chmod +x game-skill-config-plugin/scripts/*.sh`
2. 检查 `hooks/hooks.json` 中的钩子配置

### 代理未激活

代理基于上下文自动激活。尝试：
- 明确提及"技能配置"
- 首先使用斜杠命令
- 直接引用技能 JSON 文件

## 📚 文档

- [完整文档](README.md)（英文）
- [安装指南](../INSTALLATION.md)
- [变更日志](CHANGELOG.md)

## 🤝 贡献

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 使用开发 Marketplace 在本地测试
5. 提交 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 鸣谢

为使用基于 JSON 的技能配置系统的 Unity 游戏开发者创建。

特别感谢 Claude Code 团队提供的出色插件系统！

---

**快乐的技能创作！** 🎮✨
