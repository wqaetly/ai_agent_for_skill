# 🚀 skill_agent WebUI 快速开始

> 让策划人员通过网页界面进行技能分析、开发和修复

## ⚡ 一键启动

### Windows
```bash
cd skill_agent
start_webui.bat
```

### Linux/Mac
```bash
cd skill_agent
chmod +x start_webui.sh
./start_webui.sh
```

启动后访问 **http://localhost:3000**

## 📋 前置要求

- ✅ Python 3.8+
- ✅ Node.js 18+ 和pnpm
- ✅ 设置环境变量 `DEEPSEEK_API_KEY`

## 💬 使用示例

在WebUI 中输入：

```
创建一个火球术技能，造成100点火焰伤害，冷却时间5秒
```

系统会自动：
1. 🔍 检索相似技能
2. 🤖 生成技能配置JSON
3. ✅验证并修复错误
4. 📄 返回最终结果

## 📚 完整文档

详细使用指南请查看 [WEBUI_GUIDE.md](./WEBUI_GUIDE.md)

## 🛑 停止服务

### Windows
```bash
stop_webui.bat
```

### Linux/Mac
```bash
./stop_webui.sh
```

## 🎯 功能特性

- ✨ **可视化对话界面** - 友好的聊天式交互
- 🔄 **流式响应** - 实时查看生成过程
- 🎨 **多助手模式** - 技能生成、搜索、详情查询
- 🔧 **自动修复** - 智能验证和错误修复
- 📊 **RAG 增强** - 基于历史技能的智能生成

## 🏗️ 架构

```
WebUI (3000) ←→ LangGraph Server (2024) ←→ skill_agent Core
```

## 🆘 遇到问题?

查看 [故障排除](./WEBUI_GUIDE.md#🔧-故障排除) 章节
