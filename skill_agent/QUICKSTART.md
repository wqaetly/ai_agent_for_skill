# skill_agent 快速开始指南
## 🎯 系统概述

skill_agent是一个LLM无关的Unity技能配置中间件，通过Web UI + RPC通信实现：
- **对话生成技能配置** - 用自然语言描述技能，AI自动生成JSON配置
- **语义搜索技能** - 快速找到相似技能作为参考
- **智能参数推荐** - 基于历史数据推荐Action参数
- **Unity直接集成** - Web生成的配置可通过RPC直接同步到Unity

## 📋 前置要求

1. **Python 3.8+**
2. **DeepSeek API Key**（或其他LLM API Key）
3. **Unity 2021.3+**（可选，仅Unity集成时需要）

## 🚀 快速启动（5分钟）
### 步骤1：配置API Key

在系统环境变量中设置：
```bash
# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your-api-key-here"
$env:DASHSCOPE_API_KEY="your-qwen-api-key"  # 用于embedding

# 或者修改skill_agent/Python/config.yaml
```

### 步骤2：启动服务
**双击运行**：`skill_agent/启动技能助手.bat`

首次启动会自动：
1. 创建Python虚拟环境
2. 安装依赖包
3. 启动Web UI（http://127.0.0.1:7860）
4. 启动Unity RPC服务器（端口8766）
### 步骤3：在浏览器中使用

访问 http://127.0.0.1:7860，你将看到4个Tab：
#### Tab1：对话生成技能
```
用户: 创建一个火球术，造成50点火焰伤害，并附加3秒燃烧效果
AI: [自动搜索相似技能] → [生成JSON配置] → [显示预览]
```

点击"同步到Unity"即可将配置发送到Unity编辑器。
#### Tab2：技能语义搜索
- 输入：`火焰范围攻击`
- 过滤：最小Action数 = 3
- 结果：返回Top 5相似技能，显示相似度和摘要

#### Tab3：参数智能推荐
- Action类型：`DamageAction`
- 上下文：`高爆发单体伤害`
- 结果：推荐参数值（伤害、范围、CD等）

#### Tab4：操作历史记录
查看所有通过AI生成的技能配置历史。
## 🔧 Unity集成（可选）

### 1. 添加RPC客户端到场景

```csharp
// 在Unity编辑器中
1. 创建空GameObject，命名为"RAGSystem"
2. 添加组件：UnityRPCClient
3. 添加组件：UnityRPCBridge
4. 运行场景
```

### 2. 验证连接

点击Unity菜单 `Tools > skill_agent > Test Connection`

### 3. 使用Web UI生成技能
1. 在Web UI中生成技能配置
2. 点击"同步到Unity"
3. Unity自动创建技能文件
## 📁 目录结构

```
skill_agent/
├── Python/
│  ├── config.yaml              # 配置文件（API Key等）
│  ├── web_ui.py                # Web UI主程序
│  ├── llm_providers.py         # LLM抽象层
│  ├── unity_rpc_server.py      # RPC服务器
│  ├── rag_engine.py            # RAG核心引擎（复用）
│  └── requirements_webui.txt   # 依赖包
├── 启动技能助手.bat              # 一键启动脚本
└── QUICKSTART.md                # 本文档
ai_agent_for_skill/Assets/Scripts/RAGSystem/
├── UnityRPCClient.cs            # Unity RPC客户端
└── UnityRPCBridge.cs            # Unity RPC桥接器
```

## ⚙️ 配置说明

### 切换LLM提供商
编辑 `config.yaml`：
```yaml
llm_providers:
  default: "deepseek"  # 改为 "openai" 或"claude"

  openai_compatible:
    enabled: true
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"
    model: "gpt-4"
```

### 调整端口

```yaml
server:
  web_port: 7860        # Gradio Web UI端口
  unity_rpc_port: 8766  # Unity RPC端口
```

## 🔍 常见问题

### Q1: Web UI无法启动?
检查：
1. Python版本是否 >= 3.8
2. API Key是否设置
3. 端口7860是否被占用
### Q2: Unity连接失败?
检查：
1. 启动脚本是否运行成功
2. Unity场景中是否添加了UnityRPCClient组件
3. Unity Console查看连接日志

### Q3: 搜索结果为空?
确保：
1. 技能文件目录配置正确（config.yaml中的skill_indexer.skills_directory）
2. 技能文件为Odin序列化的JSON格式
3. 已运行过索引构建（首次启动自动构建）

## 📚 下一步
- **开发文档**: 查看 `docs/mcp_requirements/` 了解详细技术设计
- **API参考**: 查看 `llm_providers.py` 的文档字符串
- **Unity集成**: 查看 `UnityRPCClient.cs` 的API说明

## 🆘 获取帮助

遇到问题：
1. 查看日志：`skill_agent/Python/logs/skill_agent_server.log`
2. 检查配置：`skill_agent/Python/config.yaml`
3. 提Issue或联系开发团队
---

**享受智能化的技能配置体验！** 🎮
