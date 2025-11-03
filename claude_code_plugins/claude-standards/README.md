# Claude 开发规范插件

[![Plugin Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/wqaetly/ai_agent_for_skill)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Category](https://img.shields.io/badge/category-Code%20Quality-orange.svg)](https://claude.ai)

为 Claude Code 提供统一的中文开发规范，包括语言表达、工作原则、苏格拉底式对话和技术分析框架。

## 🌟 核心特性

### 🗣️ 语言表达规范
- **中文优先**: 所有对话和文档优先使用中文
- **直接犀利**: 去除客套话，直击问题核心
- **技术准确**: 技术术语保持英文，提供中文解释
- **零废话**: 每句话都有实质信息价值

### ⚙️ 核心工作原则
- **项目上下文优先**: 基于现有技术栈制定方案
- **质量导向**: 高质量针对性解决方案
- **架构感知**: 增量优化，避免破坏性重构
- **技术债务管理**: 权衡修复成本与重构成本

### 🤔 苏格拉底式对话
- **智能激活**: 基于关键词自动启动深度讨论
- **分级质疑**: 温和探询 → 深度质疑 → 激烈反驳
- **流程控制**: 防止无休止质疑，智能判断终止时机
- **建设性质疑**: 每个质疑都提供改进方向

### 🔍 技术分析框架
- **数据结构审视**: 识别核心数据和关系
- **数据流追踪**: 分析流向、所有权和修改权限
- **效率审查**: 找出冗余操作和性能瓶颈
- **架构权衡**: 平衡性能、可维护性、扩展性

## 🚀 快速开始

### 安装插件
```bash
# 克隆到 Claude Code 插件目录
git clone https://github.com/wqaetly/ai_agent_for_skill.git claude_code_plugins/claude-standards

# 或复制插件文件到 Claude Code 插件目录
cp -r claude-standards ~/.claude/plugins/
```

### 基本使用

#### 1. 加载所有规范
```bash
/standards-load
```

#### 2. 针对特定场景
```bash
/standards-load --code-review    # 代码审查场景
/standards-load --architecture   # 架构设计场景
/standards-load --planning      # 技术规划场景
```

#### 3. 交互式选择
```bash
/standards-load --interactive
```

#### 4. 查看当前状态
```bash
/standards-status
/standards-status --detailed
```

#### 5. 配置规范参数
```bash
/standards-config language --primary zh-CN
/standards-config socratic --auto-activate true
/standards-config quality --architecture-decay true
```

## 📋 命令参考

### `/standards-load` - 加载规范

```bash
/standards-load [选项]
```

**选项:**
- `--all`: 加载所有规范模块（默认）
- `--language`: 仅加载语言表达规范
- `--principles`: 仅加载核心工作原则
- `--socratic`: 仅加载苏格拉底式对话规范
- `--analysis`: 仅加载技术分析框架
- `--code-review`: 代码审查场景配置
- `--architecture`: 架构设计场景配置
- `--planning`: 技术规划场景配置
- `--interactive`: 交互式选择
- `--dry-run`: 预览模式

### `/standards-config` - 配置规范

```bash
/standards-config <模块> <选项> <值>
```

**语言配置:**
```bash
/standards-config language --primary zh-CN
/standards-config language --style direct
/standards-config language --comments chinese_with_space
```

**工作原则配置:**
```bash
/standards-config principles --quality-gate strict
/standards-config principles --architecture-aware true
```

**苏格拉底对话配置:**
```bash
/standards-config socratic --auto-activate true
/standards-config socratic --intensity deep
/standards-config socratic --triggers "为什么,架构,最佳实践"
```

### `/standards-status` - 查看状态

```bash
/standards-status [选项]
```

**选项:**
- `--detailed`: 显示详细配置信息
- `--summary`: 显示摘要信息
- `--json`: JSON 格式输出
- `--module <name>`: 显示特定模块状态
- `--usage`: 显示使用统计

## ⚙️ 配置详解

### 语言配置
```json
{
  "language": {
    "primary": "zh-CN",
    "technical_terms": "keep_english_with_explanation",
    "comment_style": "chinese_with_space",
    "expression_style": {
      "directness": "high",
      "sharpness": "high",
      "zero_fluff": true
    }
  }
}
```

### 工作原则配置
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

### 苏格拉底对话配置
```json
{
  "socratic_dialogue": {
    "enabled": true,
    "auto_activate": true,
    "triggers": ["为什么", "架构", "最佳实践", "why", "architecture"],
    "intensity_levels": {
      "gentle_inquiry": "基本合理，探索优化",
      "deep_questioning": "存在风险，需要论证",
      "intense_refutation": "致命缺陷，必须质疑"
    }
  }
}
```

## 🎯 使用场景

### 代码审查
```bash
/standards-load --code-review
```
- 应用严格的质量底线检查
- 重点关注架构合理性
- 识别技术债务和性能问题
- 提供具体的改进建议

### 架构设计
```bash
/standards-load --architecture
```
- 系统性架构决策权衡
- 技术选型深度分析
- 设计方案对比评估
- 长期维护性考虑

### 技术规划
```bash
/standards-load --planning
```
- 实施路径设计
- 技术债务管理策略
- 团队能力匹配评估
- 迁移风险分析

### 问题调试
```bash
/standards-load --debugging
```
- 系统性问题分析
- 根因定位方法论
- 调试策略制定
- 解决方案验证

## 🔧 高级功能

### 配置模板
```bash
/standards-config template --list
/standards-config template --apply startup
/standards-config template --create --name custom
```

### 团队同步
```bash
/standards-config sync --team
/standards-config sync --remote https://github.com/team/standards
```

### 配置导入导出
```bash
/standards-config export --file my-standards.json
/standards-config import --file my-standards.json
```

## 📊 质量检查

### 自动质量检查
插件会自动在以下情况触发质量检查：
- 代码编辑后 (PostToolUse)
- 技术文档分析时 (PreToolUse)
- 用户提示包含深度讨论关键词时 (UserPrompt)

### 质量检查规则
- **架构腐化检测**: 复杂度、耦合度、代码重复
- **技术债务阈值**: TODO注释、废弃API、安全问题
- **可维护性检查**: 长方法、深度嵌套、命名规范

## 🔍 故障排查

### 常见问题

**插件未激活:**
```bash
# 检查插件状态
/standards-status --check

# 重新加载插件
/standards-load --force
```

**配置冲突:**
```bash
# 检查配置冲突
/standards-config check-conflicts

# 重置为默认配置
/standards-config reset --to-default
```

**语言规范未生效:**
```bash
# 检查语言配置
/standards-status --module language-standards

# 重新应用语言规范
/standards-load --language
```

## 🤝 贡献指南

### 开发环境
```bash
git clone https://github.com/wqaetly/ai_agent_for_skill.git
cd claude_code_plugins/claude-standards
```

### 添加新的规范模块
1. 在 `prompts/` 目录创建新的 `.md` 文件
2. 在 `config/default-config.json` 中添加配置
3. 更新 `scripts/apply-standards.py` 中的模块描述
4. 测试新模块功能

### 提交规范
- 遵循现有的代码风格
- 更新相关文档
- 添加测试用例
- 提交前运行完整测试

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢 Claude Code 团队提供的优秀插件架构，使得开发规范管理成为可能。

## 📞 联系方式

- 项目主页: https://github.com/wqaetly/ai_agent_for_skill
- 问题反馈: https://github.com/wqaetly/ai_agent_for_skill/issues
- 邮箱: wqaetly@example.com

---

**让 Claude Code 更懂中文开发规范！** 🚀