# SkillRAG WebUI 使用指南

## 📖 概述

SkillRAG WebUI 是一个基于 LangGraph 和 agent-chat-ui 的可视化技能分析系统，让策划人员可以通过网页界面进行技能的分析、开发和修复工作。

## 🏗️ 架构

```
┌─────────────────┐      HTTP API      ┌──────────────────┐
│                 │ ◄─────────────────► │                  │
│  agent-chat-ui  │                     │ LangGraph Server │
│   (Next.js)     │                     │   (FastAPI)      │
│   Port: 3000    │                     │   Port: 2024     │
└─────────────────┘                     └──────────────────┘
                                                 │
                                                 ▼
                                        ┌──────────────────┐
                                        │   SkillRAG Core  │
                                        │   (RAG Engine)   │
                                        └──────────────────┘
```

## 🚀 快速开始

### 前置要求

1. **Python 3.8+**
   - 用于运行 LangGraph 服务器
   
2. **Node.js 18+** 和 **pnpm**
   - 用于运行 agent-chat-ui
   - 安装 pnpm: `npm install -g pnpm`

3. **环境变量**
   - `DEEPSEEK_API_KEY`: DeepSeek API 密钥（用于 LLM 调用）

### 一键启动

#### Windows

```bash
cd SkillRAG
start_webui.bat
```

#### Linux/Mac

```bash
cd SkillRAG
chmod +x start_webui.sh
./start_webui.sh
```

启动后：
- 🌐 WebUI 界面: http://localhost:3000
- 📊 LangGraph API: http://localhost:2024

### 手动启动

如果一键启动脚本不工作，可以手动启动：

#### 1. 启动 LangGraph 服务器

```bash
cd SkillRAG

# 创建虚拟环境（首次）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements_langchain.txt

# 启动服务器
python langgraph_server.py
```

服务器将在 `http://localhost:2024` 启动。

#### 2. 配置 agent-chat-ui

```bash
cd ../../agent-chat-ui

# 复制环境配置
cp ../ai_agent_for_skill/SkillRAG/webui.env .env

# 或手动创建 .env 文件，内容如下：
# NEXT_PUBLIC_API_URL=http://localhost:2024
# NEXT_PUBLIC_ASSISTANT_ID=skill-generation
```

#### 3. 启动 WebUI

```bash
# 安装依赖（首次）
pnpm install

# 启动开发服务器
pnpm dev
```

WebUI 将在 `http://localhost:3000` 启动。

## 💡 使用方法

### 1. 打开 WebUI

在浏览器中访问 http://localhost:3000

### 2. 开始对话

在输入框中输入你的需求，例如：

```
创建一个火球术技能，造成100点火焰伤害，冷却时间5秒
```

### 3. 查看结果

系统会：
1. 🔍 检索相似技能作为参考
2. 🤖 使用 LLM 生成技能配置 JSON
3. ✅ 验证 JSON 格式和业务规则
4. 🔧 如果有错误，自动修复并重试
5. 📄 返回最终的技能配置

### 4. 切换助手

系统提供三种助手模式：

- **skill-generation**: 技能生成助手（默认）
  - 根据需求描述生成完整的技能配置 JSON
  
- **skill-search**: 技能搜索助手
  - 语义搜索技能库，查找相似技能
  
- **skill-detail**: 技能详情助手
  - 查询特定技能的详细信息

要切换助手，修改 `.env` 文件中的 `NEXT_PUBLIC_ASSISTANT_ID`：

```bash
# 使用技能生成助手
NEXT_PUBLIC_ASSISTANT_ID=skill-generation

# 使用技能搜索助手
NEXT_PUBLIC_ASSISTANT_ID=skill-search

# 使用技能详情助手
NEXT_PUBLIC_ASSISTANT_ID=skill-detail
```

## 🛠️ 高级配置

### 环境变量

#### LangGraph 服务器 (langgraph_server.py)

```bash
# 服务器监听地址
LANGGRAPH_HOST=0.0.0.0

# 服务器端口
LANGGRAPH_PORT=2024

# DeepSeek API 密钥
DEEPSEEK_API_KEY=your_api_key_here
```

#### agent-chat-ui (.env)

```bash
# LangGraph 服务器地址
NEXT_PUBLIC_API_URL=http://localhost:2024

# 默认助手ID
NEXT_PUBLIC_ASSISTANT_ID=skill-generation

# LangSmith API Key（可选，用于追踪）
LANGSMITH_API_KEY=
```

### 自定义端口

如果需要修改端口：

1. **修改 LangGraph 服务器端口**
   ```bash
   export LANGGRAPH_PORT=8080
   python langgraph_server.py
   ```

2. **更新 WebUI 配置**
   ```bash
   # .env
   NEXT_PUBLIC_API_URL=http://localhost:8080
   ```

## 📊 API 端点

LangGraph 服务器提供以下 API 端点：

### 1. 健康检查
```
GET /health
```

### 2. 列出助手
```
GET /assistants
```

### 3. 创建流式运行
```
POST /threads/{thread_id}/runs/stream
```

### 4. 创建运行
```
POST /threads/{thread_id}/runs
```

### 5. 获取线程
```
GET /threads/{thread_id}
```

详细 API 文档请访问: http://localhost:2024/docs

## 🔧 故障排除

### 问题 1: LangGraph 服务器启动失败

**症状**: `ModuleNotFoundError` 或依赖缺失

**解决方案**:
```bash
pip install -r requirements_langchain.txt
```

### 问题 2: WebUI 无法连接到服务器

**症状**: 网页显示连接错误

**解决方案**:
1. 确认 LangGraph 服务器正在运行: http://localhost:2024/health
2. 检查 `.env` 文件中的 `NEXT_PUBLIC_API_URL` 配置
3. 检查防火墙设置

### 问题 3: CORS 错误

**症状**: 浏览器控制台显示 CORS 错误

**解决方案**:
LangGraph 服务器已配置允许所有来源。如果仍有问题，检查浏览器扩展（如广告拦截器）。

### 问题 4: 端口被占用

**症状**: `Address already in use`

**解决方案**:
```bash
# Windows
netstat -ano | findstr :2024
taskkill /F /PID <PID>

# Linux/Mac
lsof -ti:2024 | xargs kill
```

## 🛑 停止服务

### 使用停止脚本

#### Windows
```bash
stop_webui.bat
```

#### Linux/Mac
```bash
./stop_webui.sh
```

### 手动停止

1. 在启动脚本的终端按 `Ctrl+C`
2. 或者查找并终止进程：
   ```bash
   # Windows
   taskkill /F /IM python.exe
   taskkill /F /IM node.exe
   
   # Linux/Mac
   pkill -f langgraph_server.py
   pkill -f "pnpm dev"
   ```

## 📝 日志

- **LangGraph 服务器日志**: `SkillRAG/langgraph_server.log`
- **WebUI 日志**: 在启动 WebUI 的终端中查看

## 🎨 自定义

### 修改 Prompt

编辑 `SkillRAG/orchestration/prompts/` 目录下的 Prompt 模板。

### 添加新的助手

1. 在 `SkillRAG/orchestration/graphs/` 中创建新的图
2. 在 `langgraph_server.py` 中注册新的助手
3. 更新 `/assistants` 端点

### 自定义 UI

agent-chat-ui 是一个标准的 Next.js 应用，可以自由修改：
- 样式: `src/app/globals.css`
- 组件: `src/components/`
- 布局: `src/app/layout.tsx`

## 🚀 生产部署

### 部署 LangGraph 服务器

1. 使用 Docker:
   ```dockerfile
   FROM python:3.10
   WORKDIR /app
   COPY SkillRAG/ .
   RUN pip install -r requirements_langchain.txt
   CMD ["python", "langgraph_server.py"]
   ```

2. 或使用 Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker langgraph_server:app
   ```

### 部署 WebUI

1. 构建生产版本:
   ```bash
   cd agent-chat-ui
   pnpm build
   ```

2. 启动生产服务器:
   ```bash
   pnpm start
   ```

3. 或使用 Docker:
   ```dockerfile
   FROM node:18
   WORKDIR /app
   COPY agent-chat-ui/ .
   RUN pnpm install
   RUN pnpm build
   CMD ["pnpm", "start"]
   ```

### 环境变量（生产）

```bash
# LangGraph 服务器
LANGGRAPH_HOST=0.0.0.0
LANGGRAPH_PORT=2024
DEEPSEEK_API_KEY=your_production_key

# WebUI
NEXT_PUBLIC_API_URL=https://your-domain.com/api
NEXT_PUBLIC_ASSISTANT_ID=skill-generation
```

## 📚 相关文档

- [SkillRAG 核心文档](./README.md)
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [agent-chat-ui 文档](https://github.com/langchain-ai/agent-chat-ui)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
