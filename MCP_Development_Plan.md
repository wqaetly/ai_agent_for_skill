# MCP Server 开发计划书

## 📋 文档概览

**项目名称**: Unity技能系统智能助手 - MCP Server集成方案
**创建日期**: 2025-11-07
**目标**: 通过MCP协议让AI直接理解和操作技能配置，实现智能参数推断和Action推荐

---

## 📊 项目全面分析

### 1. 当前技术栈

#### RAG系统架构（预期实现）

**核心模块**:
- **`rag_engine.py`**: RAG引擎核心，整合所有组件
- **`embeddings.py`**: 基于Qwen3-Embedding-0.6B的向量生成器
- **`vector_store.py`**: ChromaDB封装，负责向量CRUD
- **`skill_indexer.py`**: 技能JSON解析和索引构建
- **`action_indexer.py`**: Action脚本元数据索引
- **`server.py`**: FastAPI服务器，提供RESTful API

**工作流程**:
```
技能JSON文件
   ↓ (skill_indexer解析)
技能数据 + Action metadata
   ↓ (embeddings生成向量)
ChromaDB向量数据库 (技能collection + action collection)
   ↓ (RAG检索)
FastAPI服务 → Unity编辑器
```

#### Embedding模型配置
- **模型**: Qwen3-Embedding-0.6B (本地部署)
- **维度**: 1024维向量
- **上下文长度**: 32K tokens
- **内存**: ~2GB (含模型)
- **查询优化**: 使用`prompt_name="query"`提升检索性能

---

### 2. 技能配置结构分析

#### Schema结构示例 (RivenBrokenWings.json)

```json
{
  "$type": "SkillSystem.Data.SkillData",
  "skillName": "Broken Wings",
  "skillDescription": "锐雯向前冲刺...",
  "totalDuration": 300,
  "frameRate": 30,
  "tracks": {
    "$rcontent": [
      {
        "trackName": "Animation Track",
        "actions": {
          "$rcontent": [
            {
              "$type": "SkillSystem.Actions.AnimationAction",
              "frame": 0,
              "duration": 30,
              "animationClipName": "RivenQ1",
              "crossFadeDuration": 0.1
            }
          ]
        }
      },
      {
        "trackName": "Movement Track",
        "actions": [...]
      },
      {
        "trackName": "Damage Track",
        "actions": [...]
      }
    ]
  },
  "skillId": "riven-broken-wings-001"
}
```

**关键特点**:
- **Odin序列化格式**: 使用`$type`, `$rcontent`, `$id`等元数据字段
- **Track-Action结构**: 6个轨道 (Animation, Movement, Damage, AOE, Control, Audio)
- **复杂参数**: Vector3, Color等Unity类型需要特殊解析
- **时间控制**: frame (帧位置) + duration (持续帧数)

**配置规模统计**:
| 技能文件 | 大小 | Tracks | Actions | 复杂度 |
|---------|------|--------|---------|-------|
| RivenBrokenWings.json | 14KB | 6 | 15 | 高 (三段式技能) |
| SionSoulFurnaceV2.json | 11KB | 5 | 5 | 中 (输入控制) |
| FlameShockwave.json | 13KB | 6 | 12 | 中 (范围伤害) |

---

### 3. Action类型和参数定义

#### Action元数据结构示例 (DamageAction)

```json
{
  "action": {
    "typeName": "DamageAction",
    "displayName": "属性伤害",
    "category": "Damage",
    "description": "属性缩放伤害Action...",
    "parameters": [
      {
        "name": "baseDamage",
        "type": "float",
        "defaultValue": "100",
        "label": "Base Damage",
        "group": "Damage Settings",
        "infoBox": "基础伤害值",
        "constraints": {"minValue": "0"}
      },
      {
        "name": "damageType",
        "type": "DamageType",
        "defaultValue": "Physical",
        "isEnum": true,
        "enumValues": ["Physical", "Magical", "Pure"]
      }
    ]
  }
}
```

**Action分类统计** (21个Action类型):
- Damage: 5个 (DamageAction, AttributeScaledDamageAction等)
- Movement: 2个 (MovementAction, TeleportAction)
- Heal: 2个 (HealAction, ResourceDependentHealAction)
- Control: 1个 (ControlAction - 眩晕/击飞)
- Shield: 2个 (ShieldAction, AttributeScaledShieldAction)
- Buff: 1个 (BuffAction)
- Animation/Audio/Camera等: 各1个

---

## 🔥 核心问题诊断

### 问题1: Action选择合理性不足

**现状缺陷**：
```python
# 当前RAG推荐逻辑
query = "造成伤害并击退"
→ 可能返回 DamageAction (✓) + MovementAction (✗)
# MovementAction因为"位移"和"击退"语义相似而被误召回
```

**致命问题**:
1. **语义匹配过于宽泛** - 向量检索只能做单点相似度匹配
2. **使用频率权重污染结果** - 高频Action被推荐到不相关场景
3. **缺乏Action组合验证** - 无法检查推荐组合是否合理

**根本原因**: 向量检索无法理解**Action语义约束**和**组合规则**

---

### 问题2: 参数填充粒度粗糙

**当前返回**:
```python
{
  "action_type": "DamageAction",
  "examples": [
    {"skill_name": "FlameShockwave", "parameters": {...全部14个参数...}}
  ]
}
```

**三大无法解决的问题**:
1. **参数值缺乏上下文关联**
   - 用户在设计"近战突进"技能，但推荐的`movementSpeed=15`来自远程技能

2. **参数间依赖关系缺失**
   - `damageRadius > 0` 时必须设置 `maxTargets > 1`，但系统不会提示

3. **Unity特殊类型处理困难**
   - `Vector3`、`Color`等需要Odin序列化格式，用户容易出错

**根本原因**: RAG系统返回的是**静态示例**，不是**动态推理结果**

---

### 问题3: 超大JSON分析能力不足

**当前RAG系统的致命瓶颈**:
```python
# 只存储技能级别的摘要
def search_skills(self, query: str, top_k: int = 3):
    # 只返回元数据，不返回完整JSON内容
    return [{"skill_id": ..., "file_path": ..., "similarity": ...}]
```

**问题表现**:
- ✅ 能找到相关技能（文件级别）
- ✗ 无法定位到具体的Action片段（缺乏行级索引）
- ✗ 无法比较不同技能中同类Action的参数差异
- ✗ 无法验证参数值的合法性（缺乏schema验证）
- ✗ 无法回答："所有使用DamageAction且baseDamage>200的技能有哪些？"

**上万行JSON的场景**:
假设技能文件是10000行（约20个复杂技能组合），当前RAG系统无法进行细粒度分析。

---

### 问题4: Unity编辑器交互割裂

**当前流程**:
```
用户在Unity编辑器中
  → 打开RAG查询窗口 (独立窗口)
  → 输入查询
  → 查看推荐结果
  → **切换回编辑器**
  → **手动复制参数**
  → 应用到Action
```

**理想流程**:
```
用户在Unity编辑器中
  → 选中Action
  → AI在Inspector旁边自动显示推荐参数
  → 点击"应用"按钮一键填充
  → 根据上下文微调建议
```

---

## 💡 MCP解决方案

### 为什么必须开发MCP?

| 能力维度 | RAG系统 | MCP Server |
|---------|---------|------------|
| **技能检索** | ✓ 向量相似度 | ✓ 结构化查询 + 向量检索 |
| **Action推荐** | ✗ 静态示例 | ✓ 动态推理（基于LLM） |
| **参数填充** | ✗ 手动复制 | ✓ 智能生成 + 验证 |
| **JSON生成** | ✗ 无 | ✓ Odin格式自动化 |
| **上下文理解** | ✗ 单轮查询 | ✓ 多轮对话 |
| **约束验证** | ✗ 无 | ✓ Schema + 业务规则 |

**核心价值**:
1. 向量检索适合**信息召回**，MCP适合**逻辑推理**
2. 参数填充需要**大模型理解能力**（Claude/GPT）
3. 超大JSON需要**结构化查询 + 智能摘要**
4. Unity集成需要**可解释的AI助手**，而非黑盒API

---

### MCP架构设计

```
┌────────────────────────────────────────────────────┐
│         Claude Desktop / AI Client                 │
│         (自然语言技能设计助手)                      │
└─────────────────┬──────────────────────────────────┘
                  │ MCP Protocol (stdio)
┌─────────────────▼──────────────────────────────────┐
│              MCP Server (Python)                   │
│  ┌──────────────────────────────────────────────┐ │
│  │  核心模块:                                    │ │
│  │  1. SkillQueryEngine    - 结构化查询         │ │
│  │  2. ActionRecommender   - 智能推荐引擎       │ │
│  │  3. ParameterInferencer - 参数推理器         │ │
│  │  4. JsonGenerator       - Odin格式生成器     │ │
│  │  5. SchemaValidator     - 约束验证器         │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────┬──────────────────────────────────┘
                  │ 调用现有RAG引擎
┌─────────────────▼──────────────────────────────────┐
│            RAGEngine (复用现有实现)                │
│  - VectorStore (ChromaDB)                          │
│  - EmbeddingGenerator (Qwen3)                      │
│  - SkillIndexer / ActionIndexer                    │
└────────────────────────────────────────────────────┘
```

---

## 🛠️ MCP Tools 详细设计

### Tool 1: search_skills_semantic

**功能**: 基于自然语言查询相关技能配置

**输入参数**:
```typescript
{
  "query": "string",              // "三段突进技能"
  "top_k": "number",              // 返回结果数量
  "filters": {
    "min_actions": "number",      // 最小Action数量
    "action_types": "string[]"    // 必须包含的Action类型
  }
}
```

**返回值**:
```typescript
{
  "skills": [{
    "skill_id": "riven-broken-wings-001",
    "skill_name": "Broken Wings",
    "file_path": "Assets/Skills/RivenBrokenWings.json",
    "similarity": 0.87,
    "summary": "三段突进，每段造成伤害，最后一段击飞",
    "action_counts": {"DamageAction": 3, "MovementAction": 3, ...}
  }]
}
```

---

### Tool 2: get_skill_detail

**功能**: 获取技能的完整配置，支持智能摘要

**输入参数**:
```typescript
{
  "skill_id": "string",
  "summarize": "boolean",     // true=返回摘要，false=完整JSON
  "focus_track": "string"     // 只关注某个轨道
}
```

**返回值**:
```typescript
{
  "skill_data": {...},        // 完整或摘要的JSON
  "metadata": {
    "file_size": "14KB",
    "line_count": 333,
    "complexity_score": 8.5   // 1-10复杂度评分
  }
}
```

---

### Tool 3: recommend_actions_intelligent ⭐

**功能**: 基于技能上下文智能推荐Action类型（核心工具）

**输入参数**:
```typescript
{
  "skill_context": {
    "description": "火焰范围爆炸",
    "existing_actions": [
      {"type": "AnimationAction", "frame": 0}
    ],
    "intended_effects": ["造成伤害", "击退敌人"]
  },
  "constraints": {
    "max_actions": 5,
    "forbidden_types": ["TeleportAction"]
  }
}
```

**返回值**:
```typescript
{
  "recommendations": [{
    "action_type": "DamageAction",
    "confidence": 0.92,
    "reason": "技能描述提到'造成伤害'，且为范围效果",
    "typical_frame_range": [10, 30],
    "compatible_actions": ["ControlAction"]
  }]
}
```

---

### Tool 4: infer_action_parameters ⭐⭐⭐

**功能**: 根据技能上下文推断Action参数的合理值（最关键工具）

**输入参数**:
```typescript
{
  "action_type": "DamageAction",
  "skill_context": {
    "skill_name": "Flame Shockwave",
    "description": "火焰冲击波，范围伤害",
    "skill_tags": ["fire", "aoe", "magical"],
    "frame_position": 25,
    "total_duration": 120
  },
  "related_actions": [
    {"type": "AnimationAction", "frame": 0, "duration": 30}
  ]
}
```

**返回值**:
```typescript
{
  "recommended_parameters": {
    "baseDamage": {
      "value": 150,
      "confidence": 0.88,
      "reason": "基于12个火焰AOE技能的平均值（120-180）",
      "alternative_values": [120, 180],
      "reference_skills": ["FlameShockwave", "InfernoBlast"]
    },
    "damageType": {
      "value": "Magical",
      "confidence": 0.95,
      "reason": "技能标签包含'fire'和'magical'"
    },
    "damageRadius": {
      "value": 5.0,
      "confidence": 0.75,
      "reason": "AOE技能典型半径为3-8米"
    }
  },
  "parameter_dependencies": [
    "damageRadius > 0 时建议设置 maxTargets > 1"
  ]
}
```

**核心实现逻辑**:
```python
class ParameterInferencer:
    def infer_parameters(self, action_type, skill_context, related_actions):
        # 步骤1: RAG检索相似技能
        similar_skills = self.rag_engine.search_skills(
            query=skill_context['description'],
            top_k=20
        )

        # 步骤2: 提取该Action类型的所有参数值
        param_values = defaultdict(list)
        for skill in similar_skills:
            for action in skill['actions']:
                if action['type'] == action_type:
                    for param, value in action['parameters'].items():
                        param_values[param].append({
                            'value': value,
                            'skill': skill['skill_name'],
                            'similarity': skill['similarity']
                        })

        # 步骤3: 应用上下文过滤和规则推理
        recommendations = {}
        for param_name, values in param_values.items():
            # 过滤：只保留高相似度技能的参数
            filtered = [v for v in values if v['similarity'] > 0.5]

            # 统计分布
            stats = self._calculate_statistics([v['value'] for v in filtered])

            # 规则推理（领域知识）
            if param_name == 'damageType':
                if 'fire' in skill_context.get('skill_tags', []):
                    recommended_value = 'Magical'
                    confidence = 0.95
                    reason = "火焰技能通常为魔法伤害"
                else:
                    recommended_value = stats['mode']
                    confidence = 0.7
                    reason = f"基于{len(filtered)}个相似技能的最常用值"
            else:
                recommended_value = stats['median']
                confidence = self._calculate_confidence(stats, filtered)
                reason = f"基于{len(filtered)}个技能的中位数"

            recommendations[param_name] = ParameterRecommendation(
                value=recommended_value,
                confidence=confidence,
                reason=reason,
                alternatives=[stats['percentile_25'], stats['percentile_75']],
                references=[v['skill'] for v in filtered[:3]]
            )

        return recommendations
```

---

### Tool 5: generate_action_json

**功能**: 生成符合Odin序列化格式的Action JSON

**输入参数**:
```typescript
{
  "action_type": "MovementAction",
  "parameters": {...},
  "frame": 15,
  "duration": 20
}
```

**返回值**:
```typescript
{
  "json_snippet": `{
    "$type": "6|SkillSystem.Actions.MovementAction, Assembly-CSharp",
    "$id": "42",
    "frame": 15,
    "duration": 20,
    "movementSpeed": 10.0,
    "targetPosition": {
      "$type": "7|UnityEngine.Vector3, UnityEngine.CoreModule",
      "x": 0.0, "y": 0.0, "z": 3.0
    },
    ...
  }`,
  "validation_result": {
    "valid": true,
    "warnings": []
  }
}
```

---

### Tool 6: validate_skill_config

**功能**: 验证技能JSON的合法性和一致性

**输入参数**:
```typescript
{
  "skill_json": {...},
  "validation_level": "strict" | "normal" | "loose"
}
```

**返回值**:
```typescript
{
  "valid": false,
  "errors": [
    "DamageAction at frame 50 超出技能总时长 (totalDuration=30)"
  ],
  "warnings": [
    "MovementAction和ControlAction同时在frame 20触发，可能冲突"
  ],
  "suggestions": [
    "建议在DamageAction前添加AnimationAction"
  ]
}
```

---

### Tool 7: analyze_skill_pattern

**功能**: 识别技能的设计模式和结构特征

**输入参数**:
```typescript
{
  "skill_id": "string"
}
```

**返回值**:
```typescript
{
  "pattern_type": "Three-Hit Combo",
  "characteristics": [
    "三段式攻击，每段伤害递增",
    "最后一段附带控制效果",
    "Movement和Damage在同一帧触发"
  ],
  "similar_skills": ["YasuoSteelTempest", "MasterYiWujuStyle"],
  "complexity_analysis": {
    "timing_precision": "high",
    "parameter_diversity": "medium",
    "synergy_level": "high"
  }
}
```

---

### Tool 8: query_action_statistics

**功能**: 查询Action参数的统计分布

**输入参数**:
```typescript
{
  "action_type": "DamageAction",
  "parameter_name": "baseDamage",
  "filters": {
    "skill_tags": ["melee", "physical"]
  }
}
```

**返回值**:
```typescript
{
  "statistics": {
    "count": 23,
    "mean": 125.5,
    "median": 120,
    "std_dev": 35.2,
    "min": 80,
    "max": 200,
    "percentiles": {
      "25th": 100,
      "75th": 150
    }
  },
  "distribution_chart": "ASCII图表"
}
```

---

### Tool 9: explain_action_choice

**功能**: 解释为什么推荐某个Action，提供可解释性

**输入参数**:
```typescript
{
  "recommended_action": "DamageAction",
  "skill_context": {...}
}
```

**返回值**:
```typescript
{
  "explanation": {
    "semantic_match": "技能描述中'造成伤害'直接对应DamageAction",
    "frequency_analysis": "在15个相似技能中，DamageAction出现12次",
    "pattern_recognition": "识别为'Burst Damage'模式，通常使用DamageAction",
    "alternative_choices": [
      {"action": "AttributeScaledDamageAction", "reason": "如果需要属性缩放"}
    ]
  }
}
```

---

## 📋 实施计划

### 阶段1: 基础设施（3天）

#### 任务1.1: MCP Server框架搭建
- 安装mcp-sdk-python
- 创建项目目录结构
- 实现Tool注册和调用机制
- 编写与现有RAG系统的集成层

**目录结构**:
```
mcp_server/
├── __init__.py
├── main.py                  # MCP Server主入口
├── tools/                   # MCP工具实现
│   ├── __init__.py
│   ├── search.py           # 搜索相关工具
│   ├── recommend.py        # 推荐相关工具
│   ├── infer.py            # 参数推理工具
│   ├── generate.py         # JSON生成工具
│   ├── validate.py         # 验证工具
│   └── analyze.py          # 分析工具
├── core/                    # 核心模块
│   ├── __init__.py
│   ├── parameter_inferencer.py
│   ├── action_recommender.py
│   ├── json_generator.py
│   ├── schema_validator.py
│   └── pattern_analyzer.py
├── rag_integration/         # RAG系统集成
│   ├── __init__.py
│   └── rag_client.py       # RAG引擎适配器
├── config/
│   └── settings.yaml
├── tests/
│   ├── test_tools.py
│   └── test_core.py
└── requirements.txt
```

#### 任务1.2: 工具定义和Schema设计
- 定义9个MCP Tools的输入输出schema
- 实现Resource URI路由
- 编写单元测试框架

---

### 阶段2: 核心智能模块（5天）

#### 任务2.1: ParameterInferencer - 参数推理器（P0）
**工作量**: 3天

**功能点**:
- 基于RAG的参数统计分析
- 业务规则引擎（如fire→Magical）
- 生成推理理由和置信度计算
- 处理参数依赖关系

**关键算法**:
```python
def _calculate_confidence(self, stats, filtered_values):
    # 置信度计算公式
    sample_size = len(filtered_values)
    std_dev_normalized = stats['std_dev'] / stats['mean'] if stats['mean'] > 0 else 1

    # 样本数量权重: 样本越多，置信度越高
    size_weight = min(sample_size / 20, 1.0)

    # 离散度权重: 标准差越小，置信度越高
    variance_weight = max(1 - std_dev_normalized, 0.3)

    # 综合置信度
    confidence = (size_weight * 0.6 + variance_weight * 0.4)

    return round(confidence, 2)
```

#### 任务2.2: ActionRecommender - Action推荐引擎（P0）
**工作量**: 2天

**功能点**:
- 基于上下文的Action过滤
- Action组合验证逻辑
- 生成推荐理由和可解释性输出

#### 任务2.3: OdinJsonGenerator - JSON生成器（P1）
**工作量**: 2天

**功能点**:
- 实现Odin序列化格式生成
- 处理Unity类型（Vector3, Color等）
- 自动分配$id字段

---

### 阶段3: 验证和分析（4天）

#### 任务3.1: SchemaValidator - 约束验证器（P1）
**工作量**: 2天

**功能点**:
- 参数约束检查（minValue/maxValue）
- 时间轴一致性验证（frame < totalDuration）
- Action冲突检测

#### 任务3.2: SkillPatternAnalyzer - 模式识别（P2）
**工作量**: 3天

**功能点**:
- 技能模式分类（Combo/Burst/Sustain等）
- 相似技能推荐
- 复杂度评分算法

#### 任务3.3: 统计分析工具（P2）
**工作量**: 1天

**功能点**:
- 实现query_action_statistics
- 参数分布可视化（ASCII图表）

---

### 阶段4: 集成测试（2天）

#### 任务4.1: 端到端测试
- 使用Claude Desktop测试完整工作流
- 验证推理准确性和性能
- 优化prompt和工具描述

#### 任务4.2: 文档和示例
- 编写MCP工具使用文档
- 提供典型对话示例
- 录制demo视频

---

## 📦 技术栈

### 核心依赖

```yaml
Python版本: 3.9+

必需依赖:
  - mcp-server-sdk: ^1.0.0      # MCP协议实现
  - pydantic: ^2.0.0            # 数据验证
  - numpy: ^1.24.0              # 数值计算
  - pandas: ^2.0.0              # 数据分析

RAG系统集成:
  - lancedb: ^0.17.0            # 向量数据库
  - transformers: ^4.30.0       # Qwen3-Embedding
  - fastapi: ^0.100.0           # HTTP服务器

可选依赖:
  - jsonschema: ^4.17.0         # JSON验证
  - networkx: ^3.0              # 技能依赖图分析
  - redis: ^4.5.0               # 缓存推理结果
  - langchain: ^0.1.0           # 如需LLM深度集成
```

### 开发工具

```yaml
代码质量:
  - black: 代码格式化
  - pylint: 代码检查
  - mypy: 类型检查

测试:
  - pytest: ^7.0.0
  - pytest-asyncio: ^0.21.0
  - pytest-cov: ^4.0.0
```

---

## 📊 工作量估算

| 模块 | 优先级 | 工作量 | 依赖 | 负责人 |
|------|--------|--------|------|-------|
| **MCP Server框架搭建** | P0 | 2天 | mcp-sdk-python | - |
| **ParameterInferencer** | P0 | 3天 | RAGEngine | - |
| **ActionRecommender** | P1 | 2天 | RAGEngine | - |
| **OdinJsonGenerator** | P1 | 2天 | 现有序列化逻辑 | - |
| **SchemaValidator** | P1 | 2天 | Action元数据JSON | - |
| **SkillPatternAnalyzer** | P2 | 3天 | RAGEngine + 规则引擎 | - |
| **统计分析工具** | P2 | 1天 | - | - |
| **集成测试和文档** | P1 | 2天 | 所有模块 | - |

**总计**: 约17个工作日（单人）

---

## 🎯 关键交付物

### 必需交付物（MVP）
- ✅ 可运行的MCP Server（支持9个工具）
- ✅ ParameterInferencer模块（智能参数推断）
- ✅ ActionRecommender模块（智能Action推荐）
- ✅ 完整的单元测试和集成测试
- ✅ 使用文档和示例对话

### 可选交付物
- ⚠️ Unity集成插件（P3，需额外4天）
- ⚠️ Web管理界面
- ⚠️ 性能监控Dashboard

---

## 🚀 使用场景示例

### 场景1: 创建新技能

**用户**: "帮我设计一个火焰冲击波技能，在角色前方5米处爆炸，造成范围魔法伤害并击退敌人"

**AI工作流**:
```
1. 调用 recommend_actions_intelligent
   → 推荐: DamageAction, AreaOfEffectAction, ControlAction

2. 调用 infer_action_parameters (DamageAction)
   → baseDamage: 150 (基于火焰AOE技能统计)
   → damageType: Magical (规则推理: fire → Magical)
   → range: 5.0 (用户明确指定)

3. 调用 infer_action_parameters (ControlAction)
   → controlType: Knockback
   → intensity: 1.0

4. 调用 generate_action_json
   → 生成完整的Odin格式JSON

5. 调用 validate_skill_config
   → 验证通过，返回可用配置
```

**AI回复**:
"我已经为你设计了火焰冲击波技能配置。这个技能包含3个Action：

1. **DamageAction** (frame 25):
   - baseDamage: 150（基于12个相似火焰技能的平均值）
   - damageType: Magical（火焰技能通常为魔法伤害）
   - range: 5.0米

2. **AreaOfEffectAction** (frame 25):
   - shape: Circle
   - radius: 3.0米（AOE技能典型半径）

3. **ControlAction** (frame 28):
   - controlType: Knockback
   - intensity: 1.0

以下是完整的JSON配置：
```json
{...}
```

这个配置参考了FlameShockwave和InfernoBlast等相似技能。建议在frame 0添加AnimationAction来播放施法动画。"

---

### 场景2: 优化现有技能

**用户**: "分析RivenBrokenWings技能，告诉我可以如何优化"

**AI工作流**:
```
1. 调用 get_skill_detail("riven-broken-wings-001")
   → 获取完整技能JSON

2. 调用 analyze_skill_pattern
   → 识别为"Three-Hit Combo"模式

3. 调用 query_action_statistics (DamageAction.baseDamage)
   → 比较该技能的伤害值与同类技能

4. 调用 validate_skill_config
   → 检查潜在问题
```

**AI回复**:
"我分析了RivenBrokenWings技能，发现以下优化建议：

**技能模式**: Three-Hit Combo（三段式连击）
- 每段伤害递增设计合理
- Movement和Damage在同一帧触发，协同性强

**优化建议**:
1. **伤害平衡**: 当前baseDamage=45，低于同类近战Combo技能的中位数（60）。建议提升到50-55。

2. **时间优化**: 第一段和第二段间隔100帧（3.3秒），略长。参考MasterYiWujuStyle，建议缩短到80帧。

3. **控制效果**: 第三段的击飞效果很好，但建议增加AreaOfEffectAction的伤害值（当前为0），增强视觉反馈。

4. **音效**: 音量设置合理，但第三段的pitch=0.9可能略低，建议保持1.0以增强打击感。"

---

## 📝 后续规划

### Phase 2: Unity深度集成（预计4周）
- 开发Unity MCP客户端插件
- 实现Inspector实时推荐
- 添加可视化参数调试工具

### Phase 3: 性能优化（预计2周）
- 实现参数推理结果缓存
- 优化向量检索性能
- 添加异步处理和批量操作

### Phase 4: 高级功能（预计3周）
- 技能平衡性分析
- 自动生成测试用例
- 技能链组合推荐

---

## 📞 联系方式

**项目负责人**: [待定]
**技术支持**: [待定]
**问题反馈**: [GitHub Issues]

---

**文档版本**: 1.0
**最后更新**: 2025-11-07
