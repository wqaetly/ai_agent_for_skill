# Unity集成指南 - Skill Agent

## 概述

Skill Agent已完全集成到Unity编辑器中，策划可以通过菜单一键启动整个服务栈（LangGraph + WebUI），无需手动操作命令行。

---

## 快速开始

### 前置条件

在Unity中启动服务前，确保已安装：

1. **Python 3.8+**
   ```bash
   python --version
   # 应显示：Python 3.8.x 或更高版本
   ```

2. **Node.js 18+**
   ```bash
   node --version
   # 应显示：v18.x.x 或更高版本
   ```

3. **DeepSeek API Key**
   - 访问 https://platform.deepseek.com/ 注册并获取API Key
   - 设置环境变量：
     ```bash
     # Windows（管理员CMD）
     setx DEEPSEEK_API_KEY "your-api-key-here"

     # 或在 skill_agent 目录创建 .env 文件
     echo DEEPSEEK_API_KEY=your-api-key-here > .env
     ```

---

## Unity菜单功能

打开Unity编辑器后，可在顶部菜单找到：**技能系统 > Skill Agent**

### 1. 启动服务 (Start Service)

**操作**：`技能系统 > Skill Agent > 启动服务`

**功能**：
- 自动查找并启动 `skill_agent/start_webui.bat`
- 同时启动 LangGraph Server（端口2024）和 Next.js WebUI（端口3000）
- 等待服务就绪后自动打开浏览器
- 显示启动日志窗口

**过程**：
1. 点击菜单后，会看到控制台日志：
   ```
   [Skill Agent] 正在启动服务...
   [Skill Agent] 找到启动脚本: E:\...\skill_agent\start_webui.bat
   [Skill Agent] 服务已启动（PID: 12345）
   [Skill Agent] LangGraph Server + WebUI 正在启动，请稍候30秒...
   ```

2. 启动脚本会打开一个新的控制台窗口，显示：
   - Python依赖安装（仅首次，可能需要5分钟）
   - LangGraph Server启动日志
   - Next.js WebUI启动日志

3. 等待最多60秒，服务启动完成后：
   - 浏览器自动打开 http://localhost:3000
   - 弹出对话框确认启动成功
   - 可以开始对话生成技能

**首次启动注意**：
- 首次启动会自动安装Python和Node.js依赖，可能需要5-10分钟
- 请保持网络连接畅通
- 不要关闭控制台窗口

---

### 2. 停止服务 (Stop Service)

**操作**：`技能系统 > Skill Agent > 停止服务`

**功能**：
- 停止LangGraph和WebUI进程
- 清理所有子进程（Python、Node.js）
- 释放端口2024和3000

**日志**：
```
[Skill Agent] 服务已停止
```

---

### 3. 打开WebUI (Open WebUI)

**操作**：`技能系统 > Skill Agent > 打开WebUI`

**功能**：
- 在默认浏览器打开 http://localhost:3000
- 用于服务已启动但浏览器被关闭的情况

**使用场景**：
- 服务已启动，但不小心关闭了浏览器标签
- 想在另一个浏览器中打开
- 重新开始对话

---

### 4. 检查服务状态 (Check Status)

**操作**：`技能系统 > Skill Agent > 检查服务状态`

**功能**：
- 检测LangGraph API（端口2024）是否运行
- 检测WebUI（端口3000）是否运行
- 显示服务地址

**状态对话框示例**：
```
Skill Agent 服务状态

WebUI (端口 3000): ✓ 运行中
LangGraph API (端口 2024): ✓ 运行中

WebUI地址: http://127.0.0.1:3000
API地址: http://127.0.0.1:2024
```

---

### 5. 配置API Key

**操作**：`技能系统 > Skill Agent > 配置API Key`

**功能**：
- 显示API Key配置指南
- 自动打开 `skill_agent/core_config.yaml` 文件位置

**配置方式**：

**方式1（推荐）- 环境变量**：
```bash
# Windows
setx DEEPSEEK_API_KEY "sk-xxxxxxxxxxxxx"

# Linux/Mac
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxx"
# 并添加到 ~/.bashrc 或 ~/.zshrc
```

**方式2 - .env文件**：
在 `skill_agent` 目录创建 `.env` 文件：
```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
```

**获取API Key**：
- 访问：https://platform.deepseek.com/
- 注册/登录账号
- 进入"API Keys"页面创建

---

## 使用流程

### 完整工作流

```
1. Unity中点击：技能系统 > Skill Agent > 启动服务
   ↓
2. 等待30-60秒（首次5-10分钟）
   ↓
3. 浏览器自动打开WebUI（http://localhost:3000）
   ↓
4. 在对话框输入技能需求：
   "我需要一个火焰系AOE技能，造成范围伤害并附加燃烧debuff"
   ↓
5. AI自动：
   - 检索相似技能（Top 3）
   - 生成技能JSON
   - 验证格式
   - 自动修复错误（如有）
   ↓
6. 复制生成的JSON到Unity技能编辑器
   ↓
7. 完成后点击：技能系统 > Skill Agent > 停止服务
```

---

## WebUI使用示例

### 示例1：生成新技能

**输入**：
```
我需要一个雷电系单体爆发技能：
- 瞬发释放
- 造成高额魔法伤害
- 30%概率触发眩晕
- 冷却时间8秒
```

**AI生成过程**（实时流式显示）：
```
正在检索相似技能...
✓ 找到3个相似技能：
  1. Lightning Strike (相似度 87%)
  2. Thunder Bolt (相似度 76%)
  3. Storm Fury (相似度 68%)

正在生成技能配置...
✓ 已生成初始JSON

正在验证JSON格式...
✓ 验证通过

最终结果：
{
  "skillId": "Lightning_Burst_001",
  "skillName": "雷霆爆裂",
  "skillDescription": "召唤雷电打击单个敌人，造成高额魔法伤害并有概率眩晕",
  "castTime": 0,
  "cooldown": 8.0,
  "tracks": [...]
}
```

### 示例2：修改现有技能

**输入**：
```
基于"火焰冲击波"技能，修改为冰冻版本：
- 伤害类型改为冰霜
- 附加减速效果替代燃烧
- 持续时间3秒
```

**AI会**：
- 检索"火焰冲击波"原始配置
- 保持技能结构不变
- 修改属性为冰霜主题
- 生成对应的JSON

---

## 常见问题排查

### Q1: 点击"启动服务"后无反应？

**检查**：
1. 查看Unity Console日志（Window > General > Console）
2. 查找错误信息：`[Skill Agent]` 前缀

**常见原因**：
- 启动脚本未找到 → 确保 `skill_agent/start_webui.bat` 存在
- Python未安装 → 安装Python 3.8+
- Node.js未安装 → 安装Node.js 18+

**解决方法**：
```bash
# 手动测试启动
cd E:\Study\wqaetly\ai_agent_for_skill\skill_agent
start_webui.bat

# 查看控制台错误信息
```

---

### Q2: 启动超时（60秒）？

**检查控制台窗口日志**：

**情况1 - Python依赖安装失败**：
```bash
# 手动安装依赖
cd skill_agent
pip install -r requirements_langchain.txt
```

**情况2 - Node.js依赖安装失败**：
```bash
# 手动安装依赖
cd webui
npm install
```

**情况3 - 端口被占用**：
```bash
# 检查端口占用
netstat -ano | findstr :2024
netstat -ano | findstr :3000

# 杀掉占用进程
taskkill /PID <进程ID> /F
```

**情况4 - API Key未配置**：
- 查看控制台是否有 "API Key not found" 错误
- 按上文配置API Key

---

### Q3: 浏览器打开了但无法访问？

**检查服务状态**：
1. Unity中点击：`技能系统 > Skill Agent > 检查服务状态`
2. 查看哪个服务未运行

**如果WebUI未运行**：
```bash
# 手动启动WebUI
cd webui
npm run dev
```

**如果API未运行**：
```bash
# 手动启动API
cd skill_agent
python langgraph_server.py
```

---

### Q4: 生成的技能不符合预期？

**优化方法**：

1. **提供更详细的需求**：
   ```
   ❌ 不好：生成一个伤害技能
   ✓  好：生成一个火焰系AOE技能，5米范围，造成100-150魔法伤害，
         附加3秒燃烧效果（每秒10点伤害），冷却6秒
   ```

2. **指定参考技能**：
   ```
   基于"火焰冲击波"技能，增加10%伤害和击退效果
   ```

3. **多轮对话**：
   ```
   第1轮：生成基础技能
   第2轮：增加控制效果
   第3轮：调整数值平衡
   ```

---

### Q5: 如何查看详细日志？

**Unity日志**：
- Window > General > Console
- 过滤：`[Skill Agent]`

**Python日志**：
- 查看启动脚本的控制台窗口
- 或查看 `skill_agent/logs/` 目录（如有）

**WebUI日志**：
- 浏览器开发者工具 > Console（F12）
- 查看网络请求：Network标签

---

## 技术架构

### 服务组件

```
Unity编辑器
    ↓ 启动
SkillRAGServerManager.cs
    ↓ 调用
start_webui.bat
    ↓ 并行启动
┌────────────────┬────────────────┐
│ LangGraph      │ Next.js WebUI  │
│ Server         │                │
│ (端口2024)     │ (端口3000)     │
│                │                │
│ - RAG检索      │ - 对话界面     │
│ - LLM生成      │ - 流式显示     │
│ - 验证修复     │ - 结果展示     │
└────────────────┴────────────────┘
```

### 文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| Unity管理器 | `Assets/Scripts/RAGSystem/Editor/SkillRAGServerManager.cs` | Unity端服务管理 |
| 启动脚本 | `skill_agent/start_webui.bat` | Windows启动脚本 |
| 停止脚本 | `skill_agent/stop_webui.bat` | Windows停止脚本 |
| Python服务 | `skill_agent/langgraph_server.py` | LangGraph HTTP服务器 |
| WebUI | `webui/` | Next.js前端 |
| 核心配置 | `skill_agent/core_config.yaml` | RAG和LLM配置 |

---

## 高级配置

### 修改端口

如果默认端口被占用，可修改：

**1. 修改Python端口（默认2024）**：

编辑 `skill_agent/langgraph_server.py`:
```python
def main():
    host = os.getenv("LANGGRAPH_HOST", "0.0.0.0")
    port = int(os.getenv("LANGGRAPH_PORT", "2024"))  # 改为其他端口
```

**2. 修改WebUI端口（默认3000）**：

编辑 `webui/package.json`:
```json
{
  "scripts": {
    "dev": "next dev -p 3001"  // 改为其他端口
  }
}
```

**3. 同步修改Unity配置**：

编辑 `SkillRAGServerManager.cs`:
```csharp
private const int WEBUI_PORT = 3001;  // 与上面一致
private const int API_PORT = 2025;    // 与上面一致
```

---

## 性能优化

### 加速首次启动

**预安装依赖**：
```bash
# Python依赖
cd skill_agent
pip install -r requirements_langchain.txt

# Node.js依赖
cd ../webui
npm install
```

这样首次Unity启动时就不需要安装依赖，只需10-15秒即可完成。

### 减少等待时间

如果服务启动稳定，可修改 `SkillRAGServerManager.cs`:
```csharp
private static async void WaitAndOpenBrowser()
{
    int maxRetries = 30; // 改为30秒（原60秒）
    // ...
}
```

---

## 更新日志

### 2025-01-12 - Phase 1完成

- ✅ Unity菜单集成
- ✅ 一键启动/停止服务
- ✅ 自动打开浏览器
- ✅ 服务状态检测
- ✅ 健康检查端点
- ✅ 完整错误处理

### 计划中功能

- ⏳ Phase 2: 启动窗口UI（显示日志和进度）
- ⏳ Phase 3: 生成结果直接保存到Assets/Skills
- ⏳ Phase 4: 实时预览技能效果

---

## 支持

遇到问题？

1. 查看本文档的"常见问题排查"
2. 查看Unity Console日志
3. 查看启动脚本控制台窗口
4. 查看 [README.md](README.md) 完整文档
5. 查看 [skill_agent/Docs/](skill_agent/Docs/) 详细文档

---

<div align="center">

**祝你使用愉快！**

Made with ❤️ for Unity Skill Designers

</div>
