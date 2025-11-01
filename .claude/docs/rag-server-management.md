# RAG服务器一键启动功能

## 功能概述

在Unity RAG窗口中直接启动/停止Python RAG服务器，无需手动打开命令行。

## 使用方法

### 1. 打开RAG窗口

在Unity编辑器中：
```
菜单栏 -> 技能系统 -> RAG查询窗口
```

### 2. 启动服务器

点击工具栏左侧的**"启动服务器"**按钮：

```
[启动服务器] ● 未连接  服务器: 127.0.0.1  8765  [连接]
```

启动后按钮会变为：
```
[● 服务器运行中] [停止服务器] ● 已连接  服务器: 127.0.0.1  8765
```

### 3. 查看服务器输出

点击**"● 服务器运行中"**按钮可在Unity Console查看服务器输出日志。

### 4. 停止服务器

- 点击**"停止服务器"**按钮手动停止
- 或关闭RAG窗口时自动停止

## 功能特性

### ✅ 自动功能

- **自动检测Python环境**：自动查找系统中的Python可执行文件（python/python3/py）
- **自动连接**：服务器启动3秒后自动尝试连接
- **自动停止**：关闭RAG窗口时自动停止服务器进程
- **状态监控**：实时监控服务器进程状态

### 📊 状态显示

| 显示文本 | 含义 |
|---------|------|
| "启动服务器" | 服务器未运行，点击启动 |
| "● 服务器运行中" | 服务器正在运行（绿色） |
| "停止服务器" | 点击停止服务器 |
| "● 已连接" | Unity已连接到服务器（绿色） |
| "● 未连接" | Unity未连接到服务器（红色） |

### 📝 日志输出

服务器的所有输出都会显示在Unity Console中：
- 标准输出：`[RAG Server] xxx`
- 错误输出：`[RAG Server] [ERROR] xxx`

## 前置条件

### 1. Python环境

确保已安装Python 3.7+：
```bash
python --version
# 或
python3 --version
# 或
py --version
```

### 2. 依赖安装

首次使用前需安装Python依赖：
```bash
cd SkillRAG/Python
pip install -r requirements.txt
```

### 3. 目录结构

确保项目根目录下有SkillRAG文件夹：
```
项目根目录/
├── ai_agent_for_skill/      # Unity项目
│   └── Assets/
└── SkillRAG/                 # RAG服务器
    └── Python/
        └── server.py
```

## 故障排查

### 问题1: "未找到Python环境"

**原因**：系统未安装Python或未添加到PATH

**解决**：
1. 安装Python 3.7+：https://www.python.org/
2. 确保安装时勾选"Add Python to PATH"
3. 重启Unity

### 问题2: "未找到服务器脚本"

**原因**：SkillRAG目录不在项目根目录

**解决**：
1. 检查SkillRAG文件夹位置
2. 确保路径为：`项目根目录/SkillRAG/Python/server.py`

### 问题3: 服务器启动后无法连接

**原因**：依赖未安装或端口被占用

**解决**：
1. 安装依赖：`pip install -r requirements.txt`
2. 检查端口8765是否被占用
3. 查看Unity Console中的错误信息

### 问题4: 服务器意外停止

**原因**：Python运行时错误

**解决**：
1. 点击"● 服务器运行中"查看完整日志
2. 检查Unity Console中的错误信息
3. 手动运行`python server.py`查看详细错误

## 手动启动（备选方案）

如果一键启动功能无法使用，可手动启动：

```bash
cd SkillRAG/Python
python server.py
```

然后在Unity RAG窗口点击"连接"按钮。

## 技术实现

### 核心代码

**启动服务器** (SkillRAGWindow.cs:706-792)
```csharp
private void StartServer()
{
    // 1. 查找Python可执行文件
    string pythonPath = FindPythonExecutable();

    // 2. 构建服务器脚本路径
    string serverScriptPath = Path.Combine(projectPath, "SkillRAG", "Python", "server.py");

    // 3. 启动进程并监听输出
    serverProcess = new Process { StartInfo = startInfo };
    serverProcess.OutputDataReceived += ...
    serverProcess.Start();

    // 4. 延迟3秒后自动连接
    Task.Delay(3000).ContinueWith(t => CheckConnectionAsync());
}
```

**停止服务器** (SkillRAGWindow.cs:797-824)
```csharp
private void StopServer()
{
    if (serverProcess != null && !serverProcess.HasExited)
    {
        serverProcess.Kill();
        serverProcess.WaitForExit(5000);
        serverProcess.Dispose();
    }
}
```

### 生命周期管理

- **窗口打开**：不自动启动（用户手动控制）
- **窗口关闭**：自动停止服务器进程
- **状态更新**：每次绘制GUI时检查进程状态

## 使用建议

1. **首次使用**：先手动启动一次，确保依赖安装正确
2. **开发流程**：使用一键启动功能，方便快捷
3. **调试问题**：查看Unity Console中的完整日志
4. **长时间运行**：关闭RAG窗口会停止服务器，如需保持运行请手动启动

## 相关文档

- [Timeline-Based Skill Editor](timeline-skill-editor.md)
- [RAG功能初版](../../../README.md)
