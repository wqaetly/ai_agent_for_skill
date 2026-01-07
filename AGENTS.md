# AI Agent for Skill - 开发指南

## 项目概述

Unity技能配置智能助手系统，通过RAG（检索增强生成）+ LangGraph工作流实现技能配置的智能分析、自动修复和快速生成。

## 技术栈

- **后端**: Python 3.10+, FastAPI, LangGraph, LangChain
- **LLM**: DeepSeek Reasoner (思考链模型)
- **向量化**: Qwen3-Embedding-0.6B (本地部署)
- **向量数据库**: LanceDB (嵌入式)
- **前端**: Next.js 14, React, Tailwind CSS
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
│   │   ├── vector_store.py   # ChromaDB封装
│   │   └── odin_json_parser.py # Odin格式JSON解析
│   ├── orchestration/        # LangGraph编排层
│   │   ├── graphs/           # 工作流定义
│   │   ├── nodes/            # 工作流节点
│   │   ├── schemas.py        # Pydantic Schema定义
│   │   └── prompts/          # Prompt模板
│   ├── Data/                 # 数据目录
│   │   ├── models/           # 本地Embedding模型
│   │   ├── vector_db/        # 向量数据库
│   │   └── checkpoints/      # LangGraph状态持久化
│   └── langgraph_server.py   # FastAPI服务入口
├── webui/                    # Next.js前端
│   └── src/app/              # App Router页面
└── ai_agent_for_skill/       # Unity项目
    └── Assets/Scripts/       # C#脚本
```

## 开发命令

```bash
# 启动后端服务 (端口2024)
cd skill_agent
python langgraph_server.py

# 启动前端 (端口3000/7860)
cd webui
npm install && npm run dev

# 运行测试
cd skill_agent
python -m pytest tests/

# 一键启动 (Windows)
cd skill_agent
start_webui.bat
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| LangGraph Server | 2024 | 技能生成/搜索API |
| WebUI | 3000/7860 | Next.js前端 |
| Unity RPC | 8766 | Unity Inspector参数推荐 |

## 代码规范

- Python代码遵循PEP8规范
- 使用Pydantic V2进行Schema验证
- LangGraph节点使用TypedDict定义状态
- Prompt模板集中在 `orchestration/prompts/` 目录

## 关键配置文件

- `skill_agent/config/` - 服务配置
- `skill_agent/core_config.yaml` - RAG引擎配置
- `skill_agent/.env` - API密钥 (DEEPSEEK_API_KEY)
- `webui/.env` - 前端环境变量

## 常见任务

### 添加新的LangGraph节点
1. 在 `orchestration/nodes/` 创建节点函数
2. 在 `orchestration/graphs/` 注册到工作流
3. 更新状态Schema (如需要)

### 修改Prompt模板
- 编辑 `orchestration/prompts/prompts.yaml`
- 或在 `orchestration/prompts/` 添加新模板文件

### 扩展技能Schema
- 修改 `orchestration/schemas.py` 中的Pydantic模型
- 确保与Unity侧的JSON结构一致
