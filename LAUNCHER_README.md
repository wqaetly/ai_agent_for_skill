# Skill Agent 统一启动器

## 概述

统一启动脚本系统，支持快速启动 Skill Agent 项目的各种服务组合。

## 快速开始

### 方式一：交互式菜单（推荐初次使用）

直接运行：
```bash
launch.bat
```

会显示菜单，选择对应的启动模式即可。

### 方式二：命令行快速启动

```bash
# 启动完整系统（生产环境）
launch.bat full

# 启动开发调试模式
launch.bat dev

# 仅启动后端服务
launch.bat server

# 仅启动开发后端
launch.bat devserver

# 仅启动前端UI
launch.bat webui

# 停止所有服务
launch.bat stop
```

### 方式三：使用独立停止脚本

```bash
stop_all.bat
```

## 启动模式详解

### 1. 完整系统 (full)
- **服务**: LangGraph Server + WebUI
- **端口**: 2024 (后端) + 3000 (前端)
- **用途**: 生产环境或完整功能测试
- **访问**:
  - WebUI: http://localhost:3000
  - API: http://localhost:2024
  - API 文档: http://localhost:2024/docs

### 2. 开发调试 (dev)
- **服务**: LangGraph Dev Server + WebUI
- **端口**: 8123 (后端) + 3000 (前端)
- **用途**: 开发调试，支持 LangGraph Studio 远程调试
- **访问**:
  - WebUI: http://localhost:3000
  - API: http://localhost:8123
  - API 文档: http://localhost:8123/docs
  - Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123

**优势**:
- 支持热重载
- 可使用 LangGraph Studio 远程调试
- 实时查看 Graph 执行流程

### 3. 仅后端服务 (server)
- **服务**: LangGraph Server
- **端口**: 2024
- **用途**: 后端开发或API测试
- **访问**:
  - API: http://localhost:2024
  - API 文档: http://localhost:2024/docs

### 4. 仅开发后端 (devserver)
- **服务**: LangGraph Dev Server
- **端口**: 8123
- **用途**: 后端开发调试，支持 Studio
- **访问**:
  - API: http://localhost:8123
  - API 文档: http://localhost:8123/docs
  - Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123

### 5. 仅前端界面 (webui)
- **服务**: WebUI
- **端口**: 3000
- **用途**: 前端开发
- **注意**: 需要后端服务已在运行（端口 2024 或 8123）
- **访问**: http://localhost:3000

### 6. 停止所有服务 (stop)
- 自动检测并停止所有正在运行的服务
- 支持的端口: 2024, 8123, 3000, 3001

## 高级选项

### 禁用自动打开浏览器

```bash
launch.bat full --no-browser
launch.bat dev --no-browser
```

## 自动化功能

### 智能端口清理
- 启动前自动检测端口占用
- 如发现冲突，自动停止旧进程
- 确保服务正常启动

### 依赖检测
- 首次启动 WebUI 时自动安装 node 依赖
- 自动检查虚拟环境是否存在
- 自动复制 .env 配置文件（如果不存在）

### 日志管理
- 所有服务在独立窗口运行，便于查看实时日志
- Server 日志保存在 `skill_agent/logs/server.log`

## 文件结构

```
ai_agent_for_skill/
├── launch.bat              # 主启动脚本
├── stop_all.bat            # 统一停止脚本
├── LAUNCHER_README.md      # 本文档
├── skill_agent/            # 后端项目
│   ├── langgraph_server.py # 生产服务器
│   ├── langgraph.json      # LangGraph 配置
│   └── logs/               # 日志目录
└── webui/                  # 前端项目
    └── .env                # 环境配置
```

## 常见问题

### Q: 运行launch.bat闪退怎么办？
A: 已修复闪退问题，最新版本改进了：
- 移除了不稳定的延迟变量扩展
- 移除了Windows不支持的tee命令
- 简化了错误处理逻辑
- 改进了端口检测机制

如果仍然闪退，请检查：
1. 是否有杀毒软件拦截
2. 以管理员身份运行
3. 检查虚拟环境是否完整

### Q: 端口被占用怎么办？
A: 脚本会自动检测并清理端口占用。如果自动清理失败，可以手动运行 `stop_all.bat`。

### Q: 虚拟环境不存在？
A: 确保在 `skill_agent` 目录下已创建 Python 虚拟环境：
```bash
cd skill_agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Q: WebUI 依赖未安装？
A: 首次运行 WebUI 模式时会自动安装。如需手动安装：
```bash
cd webui
pnpm install
```

### Q: Dev Server 和 Server 有什么区别？
A:
- **Server**: 生产模式，性能优化，适合部署和完整测试
- **Dev Server**: 开发模式，支持热重载和 Studio 调试，适合开发

### Q: 如何同时查看多个服务的日志？
A: 每个服务在独立的 CMD 窗口运行，标题显示服务名称，可以分别查看。

## 开发建议

### 前端开发
推荐使用模式 2 (dev) 或模式 5 (webui)：
```bash
# 方式一：完整开发环境
launch.bat dev

# 方式二：仅前端（需后端已运行）
launch.bat webui
```

### 后端开发
推荐使用模式 4 (devserver)，支持热重载和 Studio 调试：
```bash
launch.bat devserver
```

### 完整测试
使用模式 1 (full)：
```bash
launch.bat full
```

## 脚本升级

如需修改启动逻辑，编辑 `launch.bat` 中的对应函数：
- `:start_server` - LangGraph Server 启动逻辑
- `:start_devserver` - LangGraph Dev Server 启动逻辑
- `:start_webui` - WebUI 启动逻辑
- `:check_and_clean_port` - 端口检测和清理逻辑

## 技术支持

遇到问题请检查：
1. Python 虚拟环境是否正确安装
2. Node.js 和 pnpm 是否已安装
3. 端口是否被其他程序占用
4. 防火墙是否阻止了服务启动
