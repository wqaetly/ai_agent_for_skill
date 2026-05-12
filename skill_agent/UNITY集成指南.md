# Unity集成指南 - 从Unity启动skill_agent服务器

## 🎯 功能说明

通过Unity Editor菜单，可以一键启动skill_agent服务器，无需手动运行bat脚本。

- ✅ Unity菜单一键启动/停止
- ✅ 自动检测服务器状态
- ✅ 自动打开浏览器到Web UI
- ✅ 进程管理（Unity关闭时可选自动关闭服务器）

---

## 📋 首次设置（仅需一次）

### 步骤1：安装Python依赖

**方法A：通过Unity菜单安装**

1. 打开Unity编辑器
2. 点击菜单：`Tools > skill_agent > 安装依赖 (Install Dependencies)`
3. 在弹出的控制台窗口中等待安装完成（约2-5分钟）
4. 看到"安装完成！"后关闭控制台窗口

**方法B：手动运行脚本**

1. 双击 `skill_agent/安装依赖.bat`
2. 等待安装完成

### 步骤2：配置API Key

**方法A：通过Unity菜单配置**

1. 点击菜单：`Tools > skill_agent > 配置API Key`
2. 按照提示设置环境变量或编辑config.yaml

**方法B：手动配置（推荐）**

在Windows PowerShell中设置环境变量（永久）：

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "your-key", "User")
[System.Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "your-qwen-key", "User")
```

或编辑 `skill_agent/Python/config.yaml`，将API Key直接写入（仅测试用）：

```yaml
llm_providers:
  deepseek:
    api_key: "sk-your-actual-key-here"  # 直接写API Key
```

---

## 🚀 日常使用

### 启动服务器

1. 打开Unity编辑器
2. 点击菜单：`Tools > skill_agent > 启动服务器 (Start Server)`
3. 等待10-30秒（首次启动稍慢）
4. 浏览器自动打开 http://127.0.0.1:7860

**启动后会弹出对话框：**

```
skill_agent服务器
服务器启动成功！

Web UI: http://127.0.0.1:7860
RPC端口: 8766

浏览器将自动打开，如未打开请手动访问。
[确定]
```

### 停止服务器

点击菜单：`Tools > skill_agent > 停止服务器 (Stop Server)`

### 打开Web UI

如果浏览器意外关闭，点击：`Tools > skill_agent > 打开Web UI (Open Web UI)`

### 检查服务器状态

点击菜单：`Tools > skill_agent > 检查服务器状态 (Check Status)`

会显示：

```
skill_agent 服务器状态

Web UI (端口 7860): ✓ 运行中
RPC服务 (端口 8766): ✓ 运行中

访问地址: http://127.0.0.1:7860
```

---

## 🔧 完整Unity菜单说明

| 菜单项 | 快捷键 | 功能 |
|--------|--------|------|
| **启动服务器** | - | 启动Python服务器和Web UI |
| **停止服务器** | - | 停止服务器进程 |
| **打开Web UI** | - | 在浏览器中打开Web UI |
| **检查服务器状态** | - | 检测服务器运行状态 |
| --- | - | 分隔线 |
| **安装依赖** | - | 安装Python依赖包（仅首次） |
| **配置API Key** | - | 打开配置文件目录 |

---

## 📁 文件说明

### Unity侧文件

```
Assets/Scripts/RAGSystem/Editor/
└── skill_agentServerManager.cs    # Unity Editor菜单脚本
```

### Python侧文件

```
skill_agent/
├── 快速启动(Unity).bat          # Unity调用的启动脚本
├── 安装依赖.bat                  # 依赖安装脚本
├── 启动技能助手.bat              # 手动启动脚本（完整版）
└── Python/
    ├── config.yaml               # 配置文件
    ├── web_ui.py                 # Web UI主程序
    └── requirements_webui.txt    # 依赖清单
```

---

## ❓ 常见问题

### Q1: 点击"启动服务器"后无反应？

**检查清单：**

1. 是否已安装依赖？
   - 运行：`Tools > skill_agent > 安装依赖`

2. Python是否已安装？
   - 命令行运行：`python --version`
   - 应显示 Python 3.8+

3. 查看Unity Console是否有错误日志

### Q2: 服务器启动失败，显示"超时"？

**可能原因：**

1. **API Key未配置**
   - 检查环境变量是否设置
   - 或编辑 `config.yaml` 直接写API Key

2. **依赖包未安装完整**
   - 重新运行"安装依赖"

3. **端口被占用**
   - 检查7860和8766端口是否被其他程序占用
   - 使用：`netstat -ano | findstr 7860`

### Q3: 如何查看服务器日志？

**方法1：控制台窗口**

启动服务器时会弹出黑色控制台窗口，日志实时显示在其中。

**方法2：日志文件**

查看 `skill_agent/Python/logs/skillrag_server.log`

### Q4: Unity关闭后服务器是否自动关闭？

**当前设置：不自动关闭**

- 优点：Unity重启后可直接使用已启动的服务器
- 缺点：需要手动停止（通过菜单或关闭控制台窗口）

**如需自动关闭**，编辑 `skill_agentServerManager.cs:389`，取消注释：

```csharp
[InitializeOnLoadMethod]
private static void Initialize()
{
    // 取消注释以下代码
    EditorApplication.quitting += () =>
    {
        if (IsServerRunning())
        {
            StopServer();
        }
    };
}
```

### Q5: 如何在Unity中使用RPC调用？

1. **添加RPC客户端组件**
   - 场景中创建GameObject
   - 添加组件：`UnityRPCClient`
   - 添加组件：`UnityRPCBridge`

2. **运行场景**
   - 客户端会自动连接到RPC服务器（端口8766）

3. **调用示例（C#）**

```csharp
var rpcClient = FindObjectOfType<UnityRPCClient>();

// 调用技能搜索
var result = await rpcClient.CallAsync("search_skills", new {
    query = "火球术",
    top_k = 5
});

Debug.Log(result);
```

---

## 🔗 下一步

- **前端使用**：使用 Lobe Chat **桌面版 exe**，从 [lobehub.com](https://lobehub.com/) 下载后手动启动，照仓库 [`README.md § Lobe Chat 桌面版配置指南`](../README.md) 一次性填入 OpenAI 供应商设置
- **API参考**：查看 `Docs/API.md`
- **技能模式**：查看 `Docs/SkillPatterns.md`

---

**享受从Unity无缝启动AI助手的便捷体验！** 🎮✨
