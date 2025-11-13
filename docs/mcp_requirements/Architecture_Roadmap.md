# MCP Server 架构演进路线图

**文档版本**: v1.0
**更新日期**: 2025-11-11
**状态**: 执行中

---

## 核心架构决策

### 决策 1: 废弃 Unity Inspector 集成（REQ-04）

**背景**:
- REQ-04 实现了 Unity Editor 内的 HTTP API 集成，提供实时参数推荐和一键写回功能
- 该实现高度绑定 Unity Editor，无法复用到其他场景
- MCP 协议设计为 Stdio 通信，与 Unity Editor 的集成模式不兼容

**决策**:
- **完全废弃** REQ-04 的 Unity Inspector 集成功能
- **专注** Claude Code 工作流，通过 MCP 协议提供技能配置能力
- Unity Editor 集成不再维护，相关代码保留但不更新

**理由**:
1. **避免双轨制**: HTTP API（Unity）+ MCP Server（Claude）架构混乱，维护成本高
2. **聚焦核心价值**: LLM 的核心能力是分析、生成、修改超大 JSON，不是 Unity UI 集成
3. **技术限制**: MCP Stdio 协议不适合 Unity Editor 的集成场景
4. **投入产出比**: Unity 集成属于"锦上添花"，MVP 阶段不应投入

**影响范围**:
- ✅ 保留代码: `ai_agent_for_skill/Assets/Scripts/RAGSystem/Editor/` 下的代码保留但不更新
- ❌ 废弃功能: Inspector 实时推荐、一键写回、参数验证面板
- ✅ 复用逻辑: REQ-04 中的 `recommend_parameters()` 和 `validate_parameters()` 可迁移到 MCP Server

**后续可能**:
如果 Unity Editor 集成成为强需求，可考虑以下方案：
1. **轻量级 HTTP Proxy**: MCP Server 提供可选的 HTTP 网关，Unity 通过 HTTP 调用 MCP 内部逻辑
2. **独立插件**: 开发独立的 Unity MCP Client Plugin（需克服 Stdio 通信限制）
3. **手工集成**: 用户通过 Claude Code 生成 JSON，手动复制到 Unity

---

### 决策 2: 删除重复和过度设计的 REQ

**删除清单**（17 个文档）:

#### 功能重叠（删除 3 个）
- **REQ-07**: `recommend_actions_intelligent` - 与 REQ-01 的 Action 推荐功能完全重叠
- **REQ-13**: `explain_action_choice` - LLM 本身可以生成解释，无需独立工具
- **REQ-17**: ActionRecommender 任务 - 与 REQ-01 实现重复

#### Unity 集成增强（删除 3 个）
- **REQ-24**: Unity MCP Plugin - MCP 协议不适合 Unity Editor
- **REQ-25**: Inspector 实时推荐 - 与 REQ-04 重复，且已废弃
- **REQ-26**: 可视化参数调试工具 - 与 LLM 核心能力无关

#### 性能优化（删除 3 个）
- **REQ-27**: 参数推理缓存 - 当前无性能瓶颈，过早优化
- **REQ-28**: 向量检索性能优化 - REQ-03 已优化查询性能
- **REQ-29**: 异步与批量处理 - 当前无大量并发请求场景

#### 高级分析（删除 3 个）
- **REQ-30**: 技能平衡性分析 - 需游戏设计领域专家，LLM 难以判断
- **REQ-31**: 自动生成测试用例 - Unity 自动化测试复杂度高，ROI 低
- **REQ-32**: 技能链组合推荐 - 组合空间爆炸，需大量领域知识

#### Unity 集成文档（删除 5 个）
- **REQ-04 系列**: `REQ04_Implementation_Summary.md`, `REQ04_IPC_Protocol.md`, `REQ04_TestPlan.md`, `REQ04_UserGuide.md`, `REQ04_UnityInspectorFlow.md`

**理由**:
- 节省 **50%+ 开发工作量**，聚焦 MVP 核心功能
- 避免架构腐化和技术债务累积
- 简化决策流程，加快迭代速度

---

### 决策 3: MCP Server 统一架构

**架构原则**:
1. **单一职责**: MCP Server 专注服务 Claude Code，不兼容其他客户端
2. **模块化设计**: 5 个核心 Tool 对应 5 个独立 Python 模块
3. **复用现有能力**: REQ-01（Action 推荐）、REQ-03（结构化查询）作为基础设施

**架构图**:
```
┌─────────────────────────────────────────────┐
│           Claude Code (MCP Client)          │
└──────────────────┬──────────────────────────┘
                   │ Stdio Protocol
┌──────────────────▼──────────────────────────┐
│           MCP Server (Python)               │
├─────────────────────────────────────────────┤
│  5 Core Tools (REQ-05/06/08/09/10)          │
│  ├─ search_skills_semantic                  │
│  ├─ get_skill_detail                        │
│  ├─ infer_action_parameters                 │
│  ├─ generate_action_json                    │
│  └─ validate_skill_config                   │
├─────────────────────────────────────────────┤
│  Core Modules                               │
│  ├─ ParameterInferencer (REQ-16)            │
│  ├─ OdinJsonGenerator (REQ-18)              │
│  ├─ SchemaValidator (REQ-19)                │
│  ├─ RAG Engine (现有)                       │
│  └─ StructuredQueryEngine (REQ-03)          │
└─────────────────────────────────────────────┘
```

**技术栈**:
- **MCP SDK**: `mcp` Python SDK
- **数据建模**: `pydantic` (Schema 验证)
- **向量检索**: Sentence-Transformers + Chroma (复用现有)
- **结构化查询**: REQ-03 的 ChunkedJsonStore + StructuredQueryEngine
- **测试**: `pytest` + `pytest-cov`

**目录结构**:
```
skill_agent/Python/
├── mcp_server.py              # MCP Server 主入口
├── mcp_config.json            # 配置文件
├── mcp_schemas.py             # Pydantic 模型定义
├── mcp_tools.py               # Tool 注册入口
├── parameter_inferencer.py    # 参数推理核心逻辑 (REQ-16)
├── odin_json_generator.py     # JSON 生成核心 (REQ-18)
├── schema_validator.py        # Schema 校验核心 (REQ-19)
├── requirements_mcp.txt       # MCP 依赖包
├── rag_engine.py              # 现有 RAG Engine（复用）
├── server.py                  # 现有 HTTP Server（废弃）
└── tests/
    ├── test_mcp_integration.py
    └── test_scenarios/
```

---

## MVP 开发路线（14 天）

### Phase 1: 基础框架（Day 1-3）
- **REQ-14**: MCP Server 框架搭建
- **REQ-15**: 工具 Schema 设计

### Phase 2: 核心能力（Day 4-10）
- **REQ-16**: ParameterInferencer（参数推理）
- **REQ-18**: OdinJsonGenerator（JSON 生成）
- **REQ-19**: SchemaValidator（Schema 校验）

### Phase 3: 测试与文档（Day 11-14）
- **REQ-22**: 端到端测试
- **REQ-23**: 文档与示例

---

## 非 MVP 功能路线图

### P1 - 近期可选（MVP 后 1-2 周）
1. **REQ-06 summarize 模式**: 技能 JSON 智能摘要（1 天）
2. **REQ-12 统计查询优化**: ASCII 图表、分位点展示（1 天）
3. **REQ-23 文档完善**: 整体使用手册、对话示例（2 天）

### P2 - 延后优化（按需实施）
1. **REQ-11 技能模式识别**: 自动标注 Combo、Burst 等模式（3 天，需 ML 模型）
2. **REQ-20 SkillPatternAnalyzer**: 对应的实现任务（3 天）
3. **REQ-21 统计分析工具增强**: 缓存、可视化（1 天）

### P3 - 性能优化（出现瓶颈时）
1. **REQ-27 参数推理缓存**: 减少重复计算（按需）
2. **REQ-28 向量检索优化**: GPU 加速、量化（按需）
3. **REQ-29 异步批量处理**: 支持高并发场景（按需）

### 暂不考虑（已删除）
- Unity 集成增强（REQ-24/25/26）
- 高级分析功能（REQ-30/31/32）
- 功能重叠的工具（REQ-07/13/17）

---

## 架构演进原则

### 1. 渐进式开发
- **先 MVP，再优化**: 不做过早优化，先验证核心能力
- **快速迭代**: 14 天完成 MVP，立即收集用户反馈
- **数据驱动**: 根据实际使用数据决定是否实施 P1/P2 功能

### 2. 简洁优先
- **删除重复代码**: REQ-01/07 功能合并，避免维护两套逻辑
- **避免过度抽象**: 不为"未来需求"预留复杂接口
- **可读性 > 灵活性**: 清晰的代码比高度配置化的系统更易维护

### 3. 复用现有资产
- **REQ-01**: Action 推荐与约束校验逻辑（完整保留）
- **REQ-03**: 结构化查询与流式加载（核心依赖）
- **REQ-04**: `recommend_parameters()` 和 `validate_parameters()` 可迁移

### 4. 明确边界
- **MCP Server**: 专注 Claude Code，不兼容 Unity Editor
- **核心能力**: 分析、生成、修改超大 JSON，不做游戏设计决策
- **LLM 职责**: 参数推理、解释生成，不替代人工验证

---

## 技术债务管理

### 当前技术债
1. **REQ-01 过度复杂**: 500+ 行配置、UI 管理工具，需简化
2. **REQ-04 绑定 Unity**: EditorRAGClient 难以复用，需抽象为通用模块
3. **双轨制残留**: HTTP API 代码保留但未删除，可能造成混淆

### 偿还计划
1. **MVP 阶段**: 不修改 REQ-01/04，专注新功能开发
2. **P1 阶段**: 提取 REQ-04 的通用逻辑到 MCP Server
3. **P2 阶段**: 简化 REQ-01，去掉复杂的 UI 管理工具

### 债务红线
如果出现以下情况，必须立即重构：
- 新功能实现成本 > 3 天（超出预期 50%+）
- 测试覆盖率 < 70%（质量无法保证）
- 用户反馈核心功能不可用（MVP 失败）

---

## 成功标准

### MVP 验收标准
1. **功能完整性**: 5 个核心 Tool 打通技能配置全流程
2. **测试覆盖率**: > 80%，至少 3 个完整对话测试
3. **文档质量**: 用户能在 5 分钟内跑通第一个测试
4. **性能指标**:
   - 语义检索 < 2 秒
   - 参数推理 < 5 秒
   - JSON 生成 < 1 秒
   - Schema 校验 < 3 秒

### 用户价值验证
Claude Code 应能完成以下工作流：
1. **从零创建技能**: 搜索 → 推断参数 → 生成 JSON → 校验
2. **修改现有技能**: 获取详情 → 修改字段 → 重新校验
3. **分析超大技能**: 获取摘要 → 结构化查询 → 统计分析

### 业务指标
- 技能配置效率提升 **3 倍**（对比手工编辑）
- LLM 生成的 JSON 准确率 > **90%**（无语法错误）
- 用户满意度 > **4.0/5.0**（基于反馈问卷）

---

## 风险与应对

### 风险 1: Odin 序列化格式复杂
**概率**: 高 | **影响**: 中
**应对**: 优先支持常用 Action 类型，复杂类型使用占位符

### 风险 2: 参数推理准确率不足
**概率**: 中 | **影响**: 高
**应对**: 降低置信度阈值，让 LLM 辅助决策，提供 `context` 参数

### 风险 3: 测试数据不足
**概率**: 低 | **影响**: 中
**应对**: 从现有 150+ 技能 JSON 中抽取典型案例，Mock 边界情况

### 风险 4: MCP 协议理解偏差
**概率**: 中 | **影响**: 高
**应对**: 参考 MCP 官方示例，优先实现最简单的 Tool，逐步迭代

---

## 附录

### 相关文档
- `MVP_14Day_Plan.md`: 14 天开发计划详细描述
- `REQ-01` ~ `REQ-23`: 保留的需求文档（已添加状态标签）
- `REQ-03_Implementation.md`: 结构化查询实现参考

### 决策历史
| 日期 | 决策内容 | 决策人 | 理由 |
|------|----------|--------|------|
| 2025-11-11 | 废弃 Unity Inspector 集成 | 用户 | 避免双轨制，聚焦 Claude Code |
| 2025-11-11 | 删除 17 个过度设计的 REQ | 用户 | 节省 50% 工作量，聚焦 MVP |
| 2025-11-11 | 采用 MCP Server 统一架构 | 用户 | 简化架构，提高复用性 |

### 更新记录
- **v1.0** (2025-11-11): 初始版本，完成架构决策和路线图规划
