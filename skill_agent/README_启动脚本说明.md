# skill_agent 启动脚本使用说明

## 📋 脚本对比

项目提供了两个启动脚本，根据不同使用场景选择：

| 脚本名称 | 适用场景 | 日志显示 | 窗口数量 | 推荐用途 |
|---------|---------|---------|---------|---------|
| **start_webui.bat** | 生产使用 | 后台运行，日志写入文件 | 1个（启动后可关闭） | 日常使用、稳定运行 |
| **start_webui_with_logs.bat** | 开发调试 | 实时显示在独立窗口 | 3个（主控制台+2个日志窗口） | 开发调试、问题排查 |

---

## 🚀 快速启动

### 方式一：后台运行（推荐日常使用）

```bash
# 双击运行或命令行执行
start_webui.bat
```

**特点：**
- ✅ 启动后可关闭命令行窗口
- ✅ 日志保存到 `langgraph_server.log`
- ✅ 进程在后台运行
- ✅ 自动打开浏览器

**适合场景：**
- 正常使用系统功能
- 不需要频繁查看日志
- 追求简洁的工作环境

---

### 方式二：实时日志（推荐开发调试）

```bash
# 双击运行或命令行执行
start_webui_with_logs.bat
```

**特点：**
- ✅ 三个窗口实时显示日志
- ✅ 可见后端 API 请求和响应
- ✅ 可见前端编译和热重载状态
- ✅ 交互式菜单快速访问功能
- ✅ 健康检查确保服务正常启动

**窗口说明：**

1. **主控制台窗口**
   - 显示启动进度和整体状态
   - 提供交互式菜单：
     - `[1]` 打开 LangGraph API 文档
     - `[2]` 打开 RAG 查询页面
     - `[3]` 检查服务健康状态
     - `[Q]` 退出主控制台（服务继续运行）
     - `[S]` 停止所有服务并退出

2. **⚡ LangGraph Server 窗口**
   - 显示 FastAPI 服务日志
   - API 请求和响应日志
   - 错误堆栈跟踪

3. **🎨 WebUI Dev Server 窗口**
   - Next.js 编译日志
   - 热重载 (HMR) 状态
   - 前端错误和警告

**适合场景：**
- 开发新功能或修改代码
- 调试 API 接口问题
- 排查前端编译错误
- 监控系统运行状态
- 学习系统工作流程

---

## 🛑 停止服务

### 统一停止脚本（推荐）

```bash
stop_webui.bat
```

自动停止所有服务（LangGraph 和 WebUI）

### 手动停止

**后台运行版本 (`start_webui.bat`)：**
- 运行 `stop_webui.bat`
- 或通过任务管理器结束 `python.exe` 和 `node.exe` 进程

**实时日志版本 (`start_webui_with_logs.bat`)：**
- 在主控制台窗口输入 `S` 停止所有服务
- 或关闭所有服务窗口
- 或运行 `stop_webui.bat`

---

## 🔍 访问地址

启动成功后可访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| **RAG 查询页面** | http://localhost:3000/rag | ⭐ 主要功能页面 |
| **WebUI 首页** | http://localhost:3000 | 导航页面 |
| **LangGraph API** | http://localhost:2024 | 后端 API 根路径 |
| **API 文档** | http://localhost:2024/docs | FastAPI 自动生成文档 |
| **健康检查** | http://localhost:2024/health | 服务状态检查 |

---

## 🐛 常见问题

### 1. 端口被占用

**错误信息：** `Address already in use: 2024` 或 `Port 3000 is already in use`

**解决方法：**
```bash
# 停止现有服务
stop_webui.bat

# 或手动查找并结束占用端口的进程
netstat -ano | findstr :2024
netstat -ano | findstr :3000
taskkill /PID <进程ID> /F
```

### 2. Python 虚拟环境问题

**错误信息：** `venv\Scripts\activate.bat` 不存在

**解决方法：**
```bash
# 删除旧的虚拟环境
rmdir /s /q venv

# 重新运行启动脚本（会自动创建）
start_webui.bat
```

### 3. Node.js 依赖问题

**错误信息：** `Cannot find module` 或 `Module not found`

**解决方法：**
```bash
cd webui
rmdir /s /q node_modules
npm install
```

### 4. 健康检查超时

**现象：** 启动脚本提示 "LangGraph 服务器启动超时"

**解决方法：**
1. 使用 `start_webui_with_logs.bat` 查看详细日志
2. 检查 LangGraph Server 窗口的错误信息
3. 常见原因：
   - Python 依赖未正确安装
   - DeepSeek API Key 未配置
   - 向量数据库初始化失败

### 5. Windows 编译错误（重要）

**错误信息：** `error: Microsoft Visual C++ 14.0 or greater is required`

**原因：** `chromadb` 的依赖 `chroma-hnswlib` 需要编译 C++ 扩展

**✅ 已自动解决：**
启动脚本已集成预编译包策略，会自动使用 `--only-binary=:all:` 参数，**无需安装 Visual Studio Build Tools**。

**手动安装（如果需要）：**
```bash
# 激活虚拟环境
call skill_agent\venv\Scripts\activate.bat

# 升级 pip
python -m pip install --upgrade pip

# 强制使用预编译包
pip install --only-binary=:all: -r requirements_ml.txt
```

**说明：**
- 预编译包（wheel）已包含编译好的二进制文件
- 避免安装 7GB+ 的 Visual Studio Build Tools
- 所有 Windows 用户推荐此方案

---

## 💡 最佳实践

### 日常使用

```bash
# 启动系统
start_webui.bat

# 使用完毕后停止
stop_webui.bat
```

### 开发调试

```bash
# 启动系统（实时日志版）
start_webui_with_logs.bat

# 观察以下窗口：
# - LangGraph Server 窗口：查看 API 日志
# - WebUI Dev Server 窗口：查看前端编译状态
# - 主控制台：使用交互式菜单

# 修改代码后自动热重载（无需重启）
```

### 问题排查

1. **使用实时日志版本启动**
   ```bash
   start_webui_with_logs.bat
   ```

2. **查看 LangGraph Server 窗口**
   - 检查是否有 Python 错误
   - 查看 API 请求是否正常

3. **查看 WebUI Dev Server 窗口**
   - 检查前端编译错误
   - 查看热重载状态

4. **使用主控制台健康检查功能**
   - 输入 `3` 检查服务状态

---

## 🎯 高级用法

### 修改默认端口

编辑 `langgraph_server.py`：
```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2024)  # 修改此处端口
```

编辑 `webui/.env`：
```env
# 修改后端地址
NEXT_PUBLIC_API_URL=http://localhost:2024
```

WebUI 端口由 Next.js 默认使用 3000，如需修改：
```bash
# 在 webui/package.json 中修改 dev 脚本
"dev": "next dev -p 3001"
```

### 查看历史日志

```bash
# 后台运行版本的日志文件
type skill_agent\langgraph_server.log

# 实时查看日志
powershell Get-Content skill_agent\langgraph_server.log -Wait
```

---

## 📞 技术支持

遇到问题时，请提供以下信息：

1. 使用的启动脚本版本
2. 完整的错误日志（实时日志版本截图更佳）
3. Python 和 Node.js 版本
   ```bash
   python --version
   node --version
   npm --version
   ```
4. 操作系统版本

---

## 🔄 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2025-11 | 初始版本，后台运行脚本 |
| v2.0 | 2025-11 | 新增实时日志版本，交互式菜单，健康检查 |

---

**祝使用愉快！** 🎉
