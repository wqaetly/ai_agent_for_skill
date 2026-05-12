# Migration Notes — v2.x → v3.0 (Langflow + Lobe Chat)

> 主线：删除 LangGraph 与自研 WebUI → 用 [`wqaetly/langflow @ dev`](https://github.com/wqaetly/langflow/tree/dev) fork 重建编排 → 新增 OpenAI 兼容适配层 → Lobe Chat 接入 → Unity 集成回归。  
> 设计文档：[`.codebuddy/plan/langflow_lobechat_migration/requirements.md`](./.codebuddy/plan/langflow_lobechat_migration/requirements.md)、[`.codebuddy/plan/langflow_lobechat_migration/task-item.md`](./.codebuddy/plan/langflow_lobechat_migration/task-item.md)

---

## 端口与服务总览（v3.0）

| 服务 | 端口 | 启动方式 | 说明 |
|------|------|----------|------|
| Langflow Server | 7860 | `langflow/scripts/run_local.bat`（被 `launch.bat` 拉起） | 基于 fork 本地 `uv run langflow run`，无 Docker |
| OpenAI 兼容适配层 | 2024 | `python -m skill_agent.openai_compat.server` | FastAPI；将 OpenAI Chat Completions 转发为 Langflow Run API |
| Lobe Chat | 本地进程 | 从 [lobehub.com](https://lobehub.com/) 下载 **桌面版 exe** 后由用户自行启动 | 首次在设置中填入供应商（详见 [`README.md § Lobe Chat 桌面版配置指南`](./README.md)） |
| Unity RPC | 8766 | `python -m Python.unity_rpc_server`（由 Unity 端按需触发） | 协议未变，内部对 Langflow 的调用走 [`unity_rpc_langflow_client.py`](skill_agent/Python/unity_rpc_langflow_client.py) |

后端一键启动：仓库根目录 `launch.bat` → `[1] Full Backend (Langflow + Adapter)`。Lobe Chat 不再由脚本拉起。

---

## 删除清单

| 路径 | 类型 | 替代方案 |
|------|------|----------|
| `skill_agent/langgraph_server.py` | 文件 | `skill_agent/openai_compat/server.py`（FastAPI @2024）+ Langflow fork 本地 `uv run`（@7860） |
| `skill_agent/graphs.py` | 文件 | `skill_agent/orchestration/runners/__init__.py` 公开导出 |
| `skill_agent/langgraph.json` | 文件 | 不需要：Langflow 用 flow JSON（在 `langflow/flows/`）替代 LangGraph CLI 入口 |
| `skill_agent/orchestration/graphs/` | 目录（10 个图文件） | `skill_agent/orchestration/runners/`（纯 Python while/match 循环） |
| `skill_agent/orchestration/nodes/agentic_rag_nodes.py` | 文件 | 该图未在 v3.0 的 8 张 flow 之列；如需可后续单独立项 |
| `skill_agent/Data/checkpoints/` | 目录 | OpenAI 协议 stateless；多轮历史由 Lobe Chat 桌面端本地存储 |
| `skill_agent/.langgraph_api/` | 目录 | LangGraph dev server 缓存；不再需要 |
| `webui/` | 目录 | Lobe Chat 桌面版 exe（仓库不再维护部署资产，详见 [`README.md`](./README.md)） |
| `lobechat/` | 目录 | 原本仓库为 Lobe Chat 官方 docker 镜像提供的 docker-compose / smoke-test；**已于 v3.0 定稿阶段物理删除**，所有以前在 docker-compose 里设置的环境变量（`OPENAI_PROXY_URL` / `OPENAI_API_KEY` / `OPENAI_MODEL_LIST`）现在由用户在桌面端 *设置 → 语言模型 → OpenAI* 中一次性填写 |

> `webui/` 中间状态曾存为 `webui.deprecated/`，**已于 v3.0 物理删除**。如需查看历史代码请走 `git log --all -- webui/` 或 `feat/legacy-langgraph-archive` 分支。

---

## 新增清单

| 路径 | 用途 |
|------|------|
| `external/langflow/` | git submodule，pin 到 fork dev 分支 SHA `0a3f184750cf...`（详见 [`langflow/FORK_CHANGELOG.md`](./langflow/FORK_CHANGELOG.md)） |
| `langflow/scripts/run_local.bat` | 本地 `uv sync` + `uv run langflow run` 启动脚本（被 `launch.bat` 拉起） |
| `langflow/components/` | Custom Components 源码 |
| `langflow/flows/` | flow JSON 导出目录 |
| `langflow/scripts/upload_flows.py` | flow 批量上传脚本 |
| `skill_agent/openai_compat/` | FastAPI 适配层（schemas / server / langflow_client / stream_adapter） |
| `skill_agent/orchestration/runners/` | 框架无关的纯 Python 业务 runner（替代 LangGraph 图） |
| `skill_agent/orchestration/_compat.py` | LangGraph helper shim（`add_messages` / `StreamWriter` / `get_stream_writer`） |
| `skill_agent/Python/unity_rpc_langflow_client.py` | Unity RPC 内部直调 Langflow Run API 的薄客户端 |
| `skill_agent/tests/test_runners_smoke.py` | runner 包 import + 调度表 + smart router 行为快照 |
| `skill_agent/tests/test_openai_compat.py` | 适配层 6 个端到端场景 |
| `skill_agent/tests/test_unity_rpc_signature.py` | RPC 协议（Python 内置 / Unity / JSON-RPC 包络）快照 |

---

## 依赖变更

`skill_agent/requirements.txt`：

| 操作 | 包 | 说明 |
|------|----|------|
| 删除 | `langgraph` | LangGraph 运行时彻底移除 |
| 删除 | `langgraph-checkpoint` | 持久化由 Lobe Chat IndexedDB 接管 |
| 新增 | `structlog>=24.1.0` | 适配层 JSON 行结构化日志 |
| 保留 | `langchain` / `langchain-core` / `langchain-openai` / `langchain-anthropic` | 仅用于 message 类型与 LLM 客户端，不再涉及 LangGraph 编排 |

`httpx` 早已存在，沿用。

---

## fork 锁定与升级

- 锁定 commit SHA：`0a3f184750cf...`（详见 [`langflow/FORK_CHANGELOG.md`](./langflow/FORK_CHANGELOG.md)）
- 升级方式：`git submodule update --remote external/langflow` 后重跑 `uv sync`（首次 `launch.bat → [1]` 会自动触发）
- fork 与上游差异列表与 Component 依赖声明：见 [`langflow/FORK_CHANGELOG.md`](./langflow/FORK_CHANGELOG.md)（由维护者维护）

---

## 待维护者补齐（合入 main 前必须完成）

- [ ] 启动 Langflow → 在 UI 中拖拽组装并导出 8 张 flow 到 `langflow/flows/*.flow.json`（任务 3.2）
  - 需要的 8 个文件名（与 OpenAI model id 一一对应）：
    - `skill_search.flow.json`、`skill_detail.flow.json`、`skill_validation.flow.json`、`parameter_inference.flow.json`
    - `skill_generation.flow.json`、`progressive_skill_generation.flow.json`、`action_batch_skill_generation.flow.json`
    - `smart_skill_generation.flow.json`
- [ ] 走 3 个端到端验收用例（火球术 / 技能搜索 / 智能路由）——在 Lobe Chat 桌面版上手动跑。验收要点：思考链折叠区包含 `[skeleton_generator]` / `[track_generator]` / `[skill_assembler]` 阶段、最终输出为 ` ```json` 围栏代码块、`/v1/chat/completions` 以 SSE 传输并以 `data: [DONE]` 结尾。
- [ ] Unity Editor 中手动验证 ①参数推荐 RPC 通过；②"打开 WebUI"按钮跳转到 Lobe Chat 桌面版默认 deep link / 可执行路径（该设置项在 Unity 侧 RAGConfig.asset中可调）
- [ ] 在 [`langflow/FORK_CHANGELOG.md`](./langflow/FORK_CHANGELOG.md) 补齐 fork 相对上游的关键改动列表

合入门槛与 tag 策略详见 [`task-item.md`](./.codebuddy/plan/langflow_lobechat_migration/task-item.md) 任务 10。

---

## 回滚指引（30 分钟内执行）

如果 v3.0 上线后 24 小时内出现 P0/P1 问题且无法修复：

```bash
# 1. 切到归档分支
git checkout feat/legacy-langgraph-archive

# 2. 或者基于 tag 创建临时回滚分支
git checkout -b hotfix/rollback-from-v3 v2.x-final

# 3. 停止 v3 服务
launch.bat stop                               # v3 launcher 仅接管 Langflow + Adapter；Lobe Chat 桌面版 exe 请自行关闭

# 4. 老分支自带 v2 launch.bat 与 webui/结构，按其菜单启动
launch.bat
```

回滚后请把问题归档到下方"已知问题"章节。

---

## 已知问题

> 上线后发现的非阻塞问题写在这里，每条带提交 SHA 与跟进 issue 链接。

- _（无）_
