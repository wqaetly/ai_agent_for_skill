# 查看 Claude 开发规范状态

显示当前加载的 Claude 开发规范配置、激活状态和使用统计信息。

## 使用方法

```bash
/standards-status [选项]
```

## 选项

### 显示选项
- `--detailed`: 显示详细的配置信息
- `--summary`: 显示摘要信息（默认）
- `--json`: 以 JSON 格式输出
- `--active-only`: 仅显示已激活的规范模块

### 过滤选项
- `--module <name>`: 显示特定模块状态
- `--recent`: 显示最近使用的规范
- `--usage`: 显示使用统计信息

## 输出格式

### 摘要模式
```bash
/standards-status
```

输出：
```
📊 Claude 开发规范状态

🟢 已激活模块 (4/4):
├── 语言表达规范 ✅ 中文交流，直接犀利
├── 核心工作原则 ✅ 质量导向，架构感知
├── 苏格拉底式对话 ✅ 智能激活，深度质疑
└── 技术分析框架 ✅ 系统性分析工具

⚙️ 当前配置:
- 会话语言: 中文 (简体)
- 表达风格: 直接、零废话
- 质量检查: 严格模式
- 对话模式: 智能激活

📈 使用统计:
- 今日激活次数: 15
- 最常用模块: 技术分析框架
- 质量检查触发: 3 次
```

### 详细模式
```bash
/standards-status --detailed
```

输出：
```
📊 Claude 开发规范详细状态

🟢 语言表达规范
├── 主要语言: 中文 (简体)
├── 技术术语处理: 保持英文 + 中文解释
├── 注释格式: // + 空格 + 中文注释
├── 表达风格: 直接犀利，零废话
├── 技术判断: 准确优先于友善
└── 激活状态: ✅ 已激活

🟢 核心工作原则
├── 项目上下文优先: ✅ 启用
├── 架构感知模式: ✅ 启用
├── 质量导向策略: 严格模式
├── 增量改进原则: ✅ 启用
├── 技术债务阈值: 高
└── 激活状态: ✅ 已激活

🟢 苏格拉底式对话
├── 自动激活: ✅ 启用
├── 质疑强度: 深度质疑
├── 激活关键词: 为什么,架构,最佳实践,头脑风暴,why,architecture
├── 对话流程: 质疑→探索→权衡→共识
├── 终止条件: ✅ 智能判断
└── 激活状态: ✅ 已激活

🟢 技术分析框架
├── 数据结构审视: ✅ 启用
├── 数据流追踪: ✅ 启用
├── 效率审查: ✅ 启用
├── 架构决策权衡: ✅ 启用
├── 分析模板: ✅ 已加载
└── 激活状态: ✅ 已激活

📈 使用统计 (最近7天)
├── 语言规范应用: 45 次
├── 工作原则引用: 28 次
├── 苏格拉底对话: 12 次
├── 技术分析执行: 37 次
├── 质量检查触发: 8 次
└── 配置修改次数: 3 次

🔧 配置信息
├── 配置文件: .claude/standards/config.json
├── 最后更新: 2024-01-15 14:30
├── 配置版本: 1.0.0
├── 插件版本: 1.0.0
└── 同步状态: ✅ 已同步

⚠️ 注意事项
- 检测到与其他插件的潜在配置冲突
- 建议定期检查配置更新
```

### JSON 格式
```bash
/standards-status --json
```

输出：
```json
{
  "status": "active",
  "modules": {
    "language_standards": {
      "enabled": true,
      "config": {
        "primary_language": "zh-CN",
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
        "triggers": ["为什么", "架构", "最佳实践"]
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

### 特定模块状态
```bash
/standards-status --module socratic-dialogue
```

输出：
```
🔍 苏格拉底式对话模块状态

✅ 激活状态: 已启用
🎯 质疑强度: 深度质疑
🔑 激活关键词: 6个
⚡ 自动激活: 启用
📊 今日使用: 3次
⏱️ 平均对话时长: 5分钟

最近对话记录:
1. 关于微服务架构的深度讨论 (14:25)
2. 数据库设计方案质疑 (11:30)
3. 缓存策略优化讨论 (09:15)
```

### 使用统计
```bash
/standards-status --usage
```

输出：
```
📈 使用统计分析

🕐 时间分布 (最近7天)
├── 周一: 18次激活
├── 周二: 22次激活
├── 周三: 15次激活
├── 周四: 25次激活
├── 周五: 20次激活
├── 周六: 12次激活
└── 周日: 10次激活

📊 模块使用排行
1. 技术分析框架: 37次 (30.3%)
2. 语言表达规范: 45次 (36.9%)
3. 核心工作原则: 28次 (23.0%)
4. 苏格拉底式对话: 12次 (9.8%)

🎯 触发场景分析
- 代码审查: 35次 (28.7%)
- 架构讨论: 28次 (23.0%)
- 技术方案: 25次 (20.5%)
- 问题调试: 18次 (14.8%)
- 其他: 16次 (13.1%)

💡 使用建议
- 考虑在代码审查时更多使用苏格拉底式对话
- 技术分析框架使用频率良好，继续保持
```

## 故障排查

### 检查配置问题
```bash
/standards-status --check
```

### 显示健康检查
```bash
/standards-status --health
```

### 显示诊断信息
```bash
/standards-status --diagnostic
```