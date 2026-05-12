# AI Agent for Skill - 开发指南

## 项目概述

Unity技能配置智能助手系统，通过RAG（检索增强生成）+ LangGraph工作流实现技能配置的智能分析、自动修复和快速生成。

## 技术栈

- **后端**: Python 3.10+, FastAPI（OpenAI 兼容适配层）
- **编排**: [Langflow](https://github.com/wqaetly/langflow/tree/dev) fork（可视化拖拽，端口 7860）
- **LLM**: DeepSeek Reasoner (思考链模型)
- **向量化**: Qwen3-Embedding-0.6B (本地部署)
- **向量数据库**: LanceDB (嵌入式)
- **前端**: [Lobe Chat](https://github.com/lobehub/lobe-chat) **桌面版 exe**（由使用者从 [lobehub.com](https://lobehub.com/) 下载后手动启动，仓库不再提供部署资产）
- **Unity集成**: C# Editor Scripts

## MCP 工具使用指引

项目配置了 mcp-router，可使用以下 MCP 工具辅助开发：

### Context7 (文档查询)
查询第三方库的最新文档和 API 用法。遇到不确定，不认识的API需求时，请必须使用context7进行查询

```
# 先解析库 ID
resolve-library-id: gradio

# 再查询文档
get-library-docs: /gradio/gradio, topic="Blocks"
```

**适用场景**: 查询 Gradio、Pydantic、httpx 等依赖库的 API 文档

### Codex (代码执行)
在隔离环境中执行代码任务。

```
codex: PROMPT="分析 src/pipeline 目录结构", cd="E:\Study\wqaetly\xiaoshuo_video"
```

**适用场景**:
- 代码分析和重构建议
- 批量文件操作
- 复杂的代码生成任务

### 使用建议

1. **文档查询优先用 Context7**: 比搜索引擎更精准，直接获取 API 示例
2. **Codex 用于隔离任务**: 需要独立环境执行的代码任务

## 目录结构

```
ai_agent_for_skill/
├── skill_agent/              # Python RAG服务 (核心)
│   ├── core/                 # RAG引擎核心
│   │   ├── rag_engine.py     # RAG引擎主逻辑
│   │   ├── embeddings.py     # Qwen3向量生成
│   │   ├── vector_store.py   # LanceDB封装
│   │   └── odin_json_parser.py # Odin格式JSON解析
│   ├── orchestration/        # 框架无关的纯 Python 业务 runner
│   │   ├── runners/          # 替代原 LangGraph 图的 while/match 循环
│   │   ├── nodes/            # 节点函数（dict-state，弱耦合）
│   │   ├── schemas.py        # Pydantic Schema定义
│   │   └── prompts/          # Prompt模板
│   ├── openai_compat/        # OpenAI Chat Completions 兼容适配层 (FastAPI @2024)
│   │   ├── server.py         # FastAPI 入口
│   │   ├── langflow_client.py
│   │   └── stream_adapter.py # Langflow 事件 → OpenAI SSE
│   └── Data/                 # 数据目录
│       ├── models/           # 本地Embedding模型
│       └── lancedb/          # 向量数据库
├── langflow/                 # Langflow 编排资产
│   ├── components/           # Custom Components 源码
│   ├── flows/                # 导出的 *.flow.json
│   └── scripts/run_local.bat # 本地 uv run langflow run 启动脚本
├── external/langflow/        # git submodule → wqaetly/langflow @ dev
└── ai_agent_for_skill/       # Unity项目
    └── Assets/Scripts/       # C#脚本
```

## 开发命令

```bash
# 一键启动全部后端（推荐；Lobe Chat 桌面端请自行启动）
launch.bat

# 仅后端：Langflow + OpenAI 适配层
launch.bat backend

# 仅 OpenAI 适配层（端口 2024，需要 Langflow 已在 7860 运行）
cd skill_agent
python -m skill_agent.openai_compat.server

# 运行测试
cd skill_agent
python -m pytest tests/

# 更新 Langflow fork（fork dev 分支更新后）
git submodule update --remote external/langflow
# 下一次 launch.bat → [1] 会自动重跑 uv sync
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Langflow Server | 7860 | 基于 fork 本地 `uv run langflow run`，无 Docker |
| OpenAI 兼容适配层 | 2024 | FastAPI；将 OpenAI Chat Completions 转发为 Langflow Run API |
| Lobe Chat | 本地进程 | 桌面版 exe 启动后不占用固定端口；在设置中填入 `OPENAI_PROXY_URL=http://localhost:2024/v1` |
| Unity RPC | 8766 | Unity Inspector 参数推荐 |

## 代码规范

- Python代码遵循PEP8规范
- 使用Pydantic V2进行Schema验证
- 后端 runner 使用 dict-state（纯 Python、不依赖 LangGraph）
- Prompt模板集中在 `orchestration/prompts/` 目录

## 关键配置文件

- `skill_agent/config/` - 服务配置
- `skill_agent/core_config.yaml` - RAG引擎配置
- `skill_agent/.env` - API密钥 (DEEPSEEK_API_KEY)
- Lobe Chat 桌面端设置 → OpenAI - 一次性填入 `OPENAI_PROXY_URL` / `OPENAI_API_KEY` / 模型列表（详见 [`README.md § Lobe Chat 桌面版配置指南`](./README.md)）

## 常见任务

### 新增 Langflow Custom Component
1. 在 `langflow/components/` 创建继承 `Component` 的类
2. 重启 Langflow（`launch.bat → [4]` 后重跑 `[1]`）使其被加载
3. 在 Langflow Playground 中拖进 flow、连边、导出为 `langflow/flows/*.flow.json`
4. `python langflow\scripts\upload_flows.py` 同步上传

### 新增后端 runner（纯 Python）
1. 在 `skill_agent/orchestration/runners/` 创建 runner 函数
2. 暴露到 `runners/__init__.py`
3. 在 [`skill_agent/openai_compat/`](skill_agent/openai_compat) 中增加 model id 到2 runner 的路由

### 修改Prompt模板
- 编辑 `orchestration/prompts/prompts.yaml`
- 或在 `orchestration/prompts/` 添加新模板文件

### 扩展技能Schema
- 修改 `orchestration/schemas.py` 中的Pydantic模型
- 确保与Unity侧的JSON结构一致

### 扩展技能Schema
- 修改 `orchestration/schemas.py` 中的Pydantic模型
- 确保与Unity侧的JSON结构一致
