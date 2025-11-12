# MCP Server MVP 开发计划（14天）

**状态**: [P0-执行中]
**目标**: 让 Claude Code 通过 MCP 协议分析、生成、修改超大技能 JSON 文件
**时间**: 14 个工作日
**验收标准**: 5 个核心 Tool 完成技能配置全流程，测试覆盖率 > 80%

---

## 核心原则

### 聚焦必需功能
- **只做 P0**: MCP Server 基础框架 + 5 个核心 Tool
- **废弃 Unity 集成**: REQ-04 的 Unity Inspector 功能不再维护
- **复用现有能力**: REQ-01（Action 推荐）、REQ-03（结构化查询）作为基础

### 架构决策
- **MCP Server 独立运行**: Python + Stdio 协议，专注服务 Claude Code
- **避免双轨制**: 不维护 HTTP API，统一通过 MCP 协议
- **模块化设计**: 5 个 Tool 对应 5 个独立 Python 模块

---

## 任务列表

### Phase 1: 基础框架搭建（Day 1-3）

#### Task 1.1 MCP Server 框架 [REQ-14]
**时间**: Day 1-2
**依赖**: 无
**输出**:
- `SkillRAG/Python/mcp_server.py` - MCP Server 主入口
- `SkillRAG/Python/mcp_config.json` - 服务器配置
- `SkillRAG/Python/requirements_mcp.txt` - MCP 依赖包

**验收标准**: Claude Code 能发现并连接服务器

#### Task 1.2 工具 Schema 设计 [REQ-15]
**时间**: Day 3
**依赖**: Task 1.1
**输出**:
- `SkillRAG/Python/mcp_schemas.py` - Pydantic 模型定义
- `SkillRAG/Python/mcp_tools.py` - Tool 注册入口

**验收标准**: 5 个核心 Tool 的 Schema 定义清晰

---

### Phase 2: 核心能力实现（Day 4-10）

#### Task 2.1 参数推理增强 [REQ-16]
**时间**: Day 4-6
**输出**: `SkillRAG/Python/parameter_inferencer.py`
**验收**: 返回参数值、置信度、推理理由

#### Task 2.2 Odin JSON 生成器 [REQ-18]
**时间**: Day 7-8
**输出**: `SkillRAG/Python/odin_json_generator.py` + 模板库
**验收**: 生成符合 Odin 格式的 JSON 片段

#### Task 2.3 Schema 校验扩展 [REQ-19]
**时间**: Day 9-10
**输出**: `SkillRAG/Python/schema_validator.py`
**验收**: 能校验整个技能 JSON 的完整性和时序一致性

---

### Phase 3: 测试与文档（Day 11-14）

#### Task 3.1 端到端测试 [REQ-22]
**时间**: Day 11-12
**验收**: 测试覆盖率 > 80%，至少 3 个完整对话测试

#### Task 3.2 文档与示例 [REQ-23]
**时间**: Day 13-14
**输出**: 用户手册、对话示例、快速开始指南

---

## 5 个核心 Tool 定义

### Tool 1: search_skills_semantic [REQ-05]
**功能**: 语义检索相似技能
**状态**: [P0-基础功能已有，需 MCP 封装]

### Tool 2: get_skill_detail [REQ-06]
**功能**: 获取技能完整 JSON 或摘要
**状态**: [P0-底层已实现，需添加 summarize 模式]

### Tool 3: infer_action_parameters [REQ-08]
**功能**: 推断 Action 参数的合理值
**状态**: [P0-核心算法需开发]

### Tool 4: generate_action_json [REQ-09]
**功能**: 生成符合 Odin 格式的 Action JSON 片段
**状态**: [P0-完全未实现，需从零开发]

### Tool 5: validate_skill_config [REQ-10]
**功能**: 校验技能 JSON 的完整性和一致性
**状态**: [P0-基础版已有，需扩展为整体校验]

---

## 成功标准

MVP 完成后，Claude Code 应能通过自然语言对话完成以下工作流：

### 工作流 1: 从零创建技能
用户: "帮我创建一个火焰爆发技能，造成 200 点范围伤害"
Claude: 搜索 → 推断参数 → 生成 JSON → 校验 → 返回完整配置

### 工作流 2: 修改现有技能
用户: "把 '烈火斩' 的伤害提升到 300"
Claude: 获取详情 → 修改字段 → 重新校验 → 返回更新后的 JSON

### 工作流 3: 分析超大技能
用户: "分析 'UltimateCombo' 技能的伤害输出模式"
Claude: 获取摘要 → 结构化查询 → 统计分析 → 返回报告

---

## 非 MVP 功能（暂不实施）

### P1 - 近期可选
- REQ-11: 技能模式识别（需 ML 模型）
- REQ-12: Action 统计查询（REQ-03 已有基础）

### P2 - 延后优化
- REQ-27: 参数推理缓存
- REQ-28: 向量检索性能优化
- REQ-29: 异步批量处理

### 已删除（过度设计）
- REQ-04: Unity Inspector 集成
- REQ-07: Action 推荐（与 REQ-01 重复）
- REQ-13: 推荐解释（LLM 自行解释）
- REQ-24-26: Unity 集成增强
- REQ-30-32: 高级分析功能

---

## 时间表

| 日期 | 任务 | 里程碑 |
|------|------|--------|
| Day 1-2 | MCP Server 框架 | ✅ 服务器能启动 |
| Day 3 | 工具 Schema 设计 | ✅ Claude Code 能发现 5 个 Tool |
| Day 4-6 | 参数推理增强 | ✅ 推理结果包含置信度和理由 |
| Day 7-8 | Odin JSON 生成器 | ✅ 生成的 JSON 符合 Odin 格式 |
| Day 9-10 | Schema 校验扩展 | ✅ 能校验整个技能 JSON |
| Day 11-12 | 端到端测试 | ✅ 测试覆盖率 > 80% |
| Day 13-14 | 文档与示例 | ✅ 用户能在 5 分钟内跑通测试 |
