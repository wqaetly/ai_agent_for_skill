# Langflow 集成（基于 fork: wqaetly/langflow @ dev）

> 本目录承载本项目对 Langflow 的全部接入资产：自定义组件源码、flow JSON 导出文件、本地 docker-compose 与构建脚本。  
> **重要约束**：本项目**只**使用 [wqaetly/langflow @ dev](https://github.com/wqaetly/langflow/tree/dev) 这个 fork，**不得**使用 `pip install langflow` 或官方 `langflowai/langflow` Docker 镜像，以保证用户自有的魔改特性可用。

---

## Fork 锁定信息

| 项目 | 值 |
|------|-----|
| 仓库 | https://github.com/wqaetly/langflow |
| 分支 | `dev` |
| 锁定 commit SHA | `0a3f184750cf...` (`0a3f18475`) |
| 锁定 commit 标题 | `docs: add upstream sync workflow as guideline 4` (2026-05-12) |
| 引入方式 | `git submodule` → 本仓库路径 `external/langflow` |

> 上一次锁定 SHA：`ee567b98c0f50065b0e270e06c47326e08913eb5`（`feat：优化flow dump功能`，2026-05-11）。本轮 fork bump 新增 3 个 commit：(1) `2e7782b7e` 引入 `restart_langflow.bat` / `LOCAL_DEV_GUIDELINES.md` / `setup_defender_exclusions.ps1` 等本地开发工具，刷新 starter projects、custom_proxy 与 frontend node-class normalization 测试；(2) `62babbc88` Auto-format（`langflow run`）；(3) `0a3f18475` 增补 upstream sync workflow 为指南条目 4。

升级 fork 时：

```bash
git submodule update --remote external/langflow
git -C external/langflow log -n 1
# 在本 README 更新锁定 SHA 后再提交
```

---

## 目录结构

```
langflow/
├── README.md                # 本文件
├── FORK_CHANGELOG.md        # fork 相对上游的关键改动列表（由维护者维护）
├── docker-compose.yml       # 基于 ../external/langflow 源码本地构建并启动 Langflow @7860
├── components/              # 项目侧 Custom Components Python 源码（任务 3.1）
├── flows/                   # 通过 Langflow UI 导出的 *.flow.json（任务 3.2）
└── scripts/
    ├── build_image.sh       # 强制重建 fork 镜像（含 git submodule update）
    └── upload_flows.py      # Langflow ready 后批量导入 flows/*.json
```

---

## 端口与服务编排

| 服务 | 端口 | 说明 |
|------|------|------|
| Langflow Server | 7860 | 基于 fork 源码本地构建的 `skill-agent/langflow:dev` 镜像 |
| OpenAI 兼容适配层 | 2024 | `skill_agent/openai_compat`（FastAPI），转发到 Langflow Run API |
| Lobe Chat | 3210 | 官方镜像 `lobehub/lobe-chat`，前端 |
| Unity RPC | 8766 | `skill_agent/Python/unity_rpc_server.py`，Unity Editor 使用 |

完整启动入口：仓库根目录 `launch.bat`（任务 7 重写）。

---

## Custom Components 与 RAG 复用约定

- 所有需要 RAG 的 Component **必须** `from skill_agent.core.enhanced_rag_engine import ...` 复用现有引擎，**禁止**在 Component 内部重写 RAG 逻辑。
- 所有需要 LLM 的 Component **必须**用 OpenAI 客户端（`base_url=https://api.deepseek.com`）直连 DeepSeek Reasoner，**不得**依赖 Langflow 内置 LLM 节点（避免与 fork 行为冲突）。
- 复杂图（progressive / skill_generation / action_batch）以**粗粒度** Component 承载，内部直接调用 `skill_agent/orchestration/runners/*` 中的纯函数 runner（任务 2 输出）。
- 简单图（skill_search）拆为细粒度节点流，每个节点可在 Langflow Playground 中单步调试。

---

## Flow 与 OpenAI Model ID 对照

| Flow 名 | flows/ 文件名 | OpenAI model id | 类型 |
|---------|---------------|-----------------|------|
| Skill Search | `skill_search.flow.json` | `skill-search` | 细粒度 |
| Skill Detail | `skill_detail.flow.json` | `skill-detail` | 细粒度 |
| Skill Validation | `skill_validation.flow.json` | `skill-validation` | 细粒度 |
| Parameter Inference | `parameter_inference.flow.json` | `parameter-inference` | 细粒度 |
| Skill Generation | `skill_generation.flow.json` | `skill-generation` | 粗粒度 |
| Progressive Skill Generation | `progressive_skill_generation.flow.json` | `progressive-skill-generation` | 粗粒度 |
| Action Batch Skill Generation | `action_batch_skill_generation.flow.json` | `action-batch-skill-generation` | 粗粒度 |
| Smart Skill Generation | `smart_skill_generation.flow.json` | `smart` | 路由 |

每张 flow 的输入/输出 schema、关键 Component 与 fork 锁定 SHA 在任务 3.2 阶段补齐到本节末尾。

---

## 待补齐

- [ ] 任务 3.1 完成后：列出 `components/` 下每个 Custom Component 的输入/输出 schema
- [ ] 任务 3.2 完成后：补齐每张 flow 的输入/输出 schema 与节点拓扑示意
- [ ] 任务 4 完成后：补齐 docker-compose 关键 volume 挂载点说明
