# Skill Agent 快速启动指南

## 🚀 一键启动整个系统

### 方式一：Unity中启动（推荐）

1. **打开Unity Editor**
   - 打开项目：`ai_agent_for_skill/ai_agent_for_skill`

2. **启动服务**
   ```
   菜单: Tools → SkillAgent → 启动服务器 (Start Server)
   ```

3. **自动完成以下操作**：
   - ✅ 启动LangGraph后端服务器（端口2024）
   - ✅ 启动WebUI前端（端口3000）
   - ✅ 自动打开浏览器到RAG查询页面
   - ✅ 显示所有访问地址

4. **浏览器自动打开**：
   - 等待8秒后自动打开：`http://localhost:3000/rag`
   - 如未自动打开，可手动点击菜单：`Tools → SkillAgent → 打开Web UI`

---

### 方式二：双击bat文件启动

1. **Windows文件管理器**
   - 进入目录：`E:\Study\wqaetly\ai_agent_for_skill\skill_agent`
   - 双击：`start_webui.bat`

2. **自动完成以下操作**：
   - ✅ 创建Python虚拟环境（首次运行）
   - ✅ 安装Python依赖
   - ✅ 启动LangGraph服务器（端口2024）
   - ✅ 安装Node.js依赖（首次运行）
   - ✅ 启动WebUI（端口3000）
   - ✅ 等待8秒后自动打开浏览器到 `http://localhost:3000/rag`

3. **控制台输出**：
   ```
   🚀 启动 skill_agent 技能分析系统...

   📁 skill_agent 目录: E:\...\skill_agent\
   📁 WebUI 目录: E:\...\webui

   1️⃣ 启动 LangGraph 服务器...
   ✅ LangGraph 服务器已启动

   2️⃣ 配置并启动 WebUI...
   ✅ WebUI 已启动

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ✨ skill_agent 技能分析系统已启动！

   📊 LangGraph 服务器: http://localhost:2024
   🌐 WebUI 界面: http://localhost:3000

   📝 日志文件: E:\...\langgraph_server.log

   ⏹️  停止服务: stop_webui.bat
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   等待 WebUI 启动完成...
   🌐 正在打开浏览器...

   按任意键退出（服务将继续在后台运行）...
   ```

---

### 方式三：命令行启动

**选项A：一键启动（bat脚本）**
```cmd
cd E:\Study\wqaetly\ai_agent_for_skill\skill_agent
start_webui.bat
```

**选项B：手动启动（分步）**
```cmd
# 终端1: 启动后端
cd E:\Study\wqaetly\ai_agent_for_skill\skill_agent
python langgraph_server.py

# 终端2: 启动WebUI
cd E:\Study\wqaetly\ai_agent_for_skill\webui
npm install  # 首次运行
npm run dev
```

---

## 🌐 访问地址

启动成功后，可以访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **WebUI主页** | http://localhost:3000 | Next.js首页 |
| **RAG查询页面** | http://localhost:3000/rag | ⭐ 主要功能页面 |
| **LangGraph API** | http://localhost:2024 | 后端API根路径 |
| **API文档** | http://localhost:2024/docs | FastAPI自动生成的文档 |
| **RAG健康检查** | http://localhost:2024/rag/health | RAG服务状态 |

---

## 🔍 检查服务状态

### Unity中检查

```
菜单: Tools → SkillAgent → 检查服务器状态 (Check Status)
```

显示内容：
```
SkillAgent服务器状态

WebUI (端口 3000): ✓ 运行中
LangGraph API (端口 2024): ✓ 运行中

✅ 所有服务运行正常！

WebUI主页: http://127.0.0.1:3000
RAG查询: http://127.0.0.1:3000/rag
API文档: http://127.0.0.1:2024/docs
```

### 命令行检查

```cmd
# 检查端口占用
netstat -ano | findstr "3000"
netstat -ano | findstr "2024"

# 测试API健康
curl http://localhost:2024/health
curl http://localhost:2024/rag/health
```

---

## ⏹️ 停止服务

### 方式一：Unity中停止

```
菜单: Tools → SkillAgent → 停止服务器 (Stop Server)
```

### 方式二：bat脚本停止

```cmd
cd E:\Study\wqaetly\ai_agent_for_skill\skill_agent
stop_webui.bat
```

### 方式三：手动停止

**查找进程**：
```cmd
# 查找Node.js进程（WebUI）
tasklist | findstr "node.exe"

# 查找Python进程（LangGraph）
tasklist | findstr "python.exe"
```

**杀死进程**：
```cmd
# 方式1: 通过进程名
taskkill /F /IM node.exe
taskkill /F /IM python.exe

# 方式2: 通过PID
taskkill /F /PID <进程ID>
```

---

## 📁 目录结构

```
ai_agent_for_skill/
├── skill_agent/
│   ├── start_webui.bat          ⭐ 一键启动脚本
│   ├── stop_webui.bat           ⭐ 停止脚本
│   ├── langgraph_server.py      后端主服务器
│   ├── requirements_langchain.txt  Python依赖
│   └── core/                    RAG核心引擎
│
├── webui/
│   ├── package.json             Node.js依赖
│   ├── next.config.js           Next.js配置
│   └── src/app/
│       ├── page.tsx             首页
│       └── rag/
│           └── page.tsx         ⭐ RAG查询页面
│
└── ai_agent_for_skill/          Unity项目
    └── Assets/Scripts/RAGSystem/Editor/
        └── SkillAgentServerManager.cs  ⭐ Unity启动管理器
```

---

## ❓ 常见问题

### Q1: 双击bat后闪退？

**原因**: Python环境未配置或依赖缺失

**解决**:
```cmd
# 1. 检查Python版本
python --version  # 需要 3.8+

# 2. 手动安装依赖
cd skill_agent
pip install -r requirements_langchain.txt
```

### Q2: 浏览器没有自动打开？

**原因**: 可能是防火墙或浏览器设置

**解决**:
- 手动访问：http://localhost:3000/rag
- 或在Unity中点击：`Tools → SkillAgent → 打开Web UI`

### Q3: Unity提示"未找到启动脚本"？

**原因**: 项目目录结构不正确

**检查**:
- `start_webui.bat` 必须在 `skill_agent/` 目录下
- Unity项目必须在 `ai_agent_for_skill/ai_agent_for_skill/`

**验证**:
```cmd
dir E:\Study\wqaetly\ai_agent_for_skill\skill_agent\start_webui.bat
```

### Q4: 端口3000已被占用？

**查找占用进程**:
```cmd
netstat -ano | findstr "3000"
```

**杀死进程**:
```cmd
taskkill /F /PID <PID>
```

### Q5: WebUI显示"无法连接后端"？

**检查后端状态**:
```cmd
curl http://localhost:2024/health
```

**如果失败**:
- 检查 `skill_agent/langgraph_server.log` 日志
- 确认端口2024未被占用
- 重启后端服务

---

## 🧪 测试验证

### 快速测试

**1. 测试后端API**:
```cmd
cd skill_agent
python test_rag_api.py
```

**2. 测试集成**:
```cmd
cd ai_agent_for_skill
python test_integration.py
```

### 功能测试

**1. RAG查询页面**:
- 访问：http://localhost:3000/rag
- 切换4个Tab：技能搜索、Action推荐、参数推荐、索引管理
- 输入测试查询：`AOE伤害技能`

**2. API测试**:
```cmd
# 搜索技能
curl -X POST http://localhost:2024/rag/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"治疗技能\", \"top_k\": 3}"

# 健康检查
curl http://localhost:2024/rag/health
```

---

## 📖 相关文档

- **迁移指南**: `MIGRATION_GUIDE.md` - 详细的功能迁移说明
- **WebUI使用**: `webui/src/app/rag/README.md` - RAG查询页面使用说明
- **API文档**: http://localhost:2024/docs - FastAPI自动生成的API文档
- **集成测试**: `test_integration.py` - 完整的测试脚本

---

## 🎉 成功标志

看到以下内容说明启动成功：

✅ Unity菜单显示：`Tools → SkillAgent → 启动服务器` ✓
✅ 浏览器自动打开：`http://localhost:3000/rag`
✅ WebUI显示4个Tab：技能搜索、Action推荐、参数推荐、索引管理
✅ 索引管理Tab显示绿色健康状态
✅ 可以输入查询并获得结果

---

**版本**: v2.0.0
**最后更新**: 2025-11-13
**支持平台**: Windows
