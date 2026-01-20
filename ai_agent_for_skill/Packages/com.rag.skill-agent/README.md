# RAG Builder System

一个可配置的 RAG（检索增强生成）构建系统 Unity 包。该包提供了为 AI 技能生成构建 Action/Skill 索引的工具。

## 📋 目录

- [功能特性](#功能特性)
- [包结构](#包结构)
- [安装方法](#安装方法)
- [快速开始](#快速开始)
- [核心接口](#核心接口)
- [配置说明](#配置说明)
- [菜单功能](#菜单功能)
- [迁移指南](#迁移指南)
- [示例代码](#示例代码)
- [依赖项](#依赖项)
- [许可证](#许可证)

## 功能特性

- **🔌 解耦架构**：使用接口适配任何技能/动作系统，与具体项目完全解耦
- **⚙️ 配置驱动**：所有路径和设置均可通过 ScriptableObject 配置
- **🖥️ 服务器管理**：直接从 Unity 启动/停止 Python RAG 服务器
- **📤 导出系统**：将 Action 和 Skill 导出为 JSON 用于 RAG 索引
- **🎛️ Unity 偏好设置集成**：通过 Unity Preferences 窗口配置一切

## 包结构

```
com.wqaetly.rag-builder/
├── package.json                    # 包配置文件
├── README.md                       # 使用文档
├── CHANGELOG.md                    # 变更日志
├── LICENSE.md                      # MIT 许可证
├── Runtime/                        # 运行时代码
│   ├── RAGBuilder.Runtime.asmdef   # 程序集定义
│   ├── Core/
│   │   ├── Interfaces.cs           # 核心接口定义 (IActionInfo, ISkillInfo 等)
│   │   ├── Providers.cs            # Provider 接口 (IActionProvider, ISkillProvider)
│   │   └── RAGBuilderConfig.cs     # 配置 ScriptableObject
│   ├── Client/
│   │   └── RAGClient.cs            # RAG 服务 HTTP 客户端
│   ├── Models/
│   │   ├── SemanticModels.cs       # 语义模型定义
│   │   └── ExportModels.cs         # 导出数据模型
│   └── Utils/
│       └── JsonStandardizer.cs     # JSON 标准化工具
├── Editor/                         # 编辑器代码
│   ├── RAGBuilder.Editor.asmdef    # 程序集定义
│   ├── Core/
│   │   ├── RAGBuilderService.cs    # 核心服务（管理配置和导出）
│   │   └── RAGServerManager.cs     # Python 服务器管理
│   └── UI/
│       ├── RAGBuilderMenus.cs      # Unity 菜单项
│       └── RAGBuilderSettingsProvider.cs  # Unity 偏好设置界面
└── Samples~/                       # 示例代码
    └── SkillSystemAdapter/
        ├── README.md
        ├── SampleImplementations.cs    # 接口实现示例
        └── SampleActionProvider.cs     # Provider 实现示例
```

## 安装方法

### 方式一：通过 Package Manager（Git URL）

1. 打开 Unity Package Manager（Window > Package Manager）
2. 点击 "+" 选择 "Add package from git URL..."
3. 输入：`https://github.com/wqaetly/rag-builder.git`

### 方式二：本地包安装

1. 将 `com.wqaetly.rag-builder` 文件夹复制到目标项目的 `Packages` 目录
2. Unity 会自动检测并导入该包

### 方式三：通过 manifest.json

在项目的 `Packages/manifest.json` 中添加：

```json
{
  "dependencies": {
    "com.wqaetly.rag-builder": "file:../path/to/com.wqaetly.rag-builder"
  }
}
```

## 快速开始

### 步骤 1：创建配置

1. 打开 **Edit > Preferences > RAG Builder**
2. 点击 "Create New Configuration" 创建配置文件
3. 配置服务器地址、导出路径等参数

或者通过菜单创建：**Tools > RAG Builder > Open Settings**

### 步骤 2：实现适配器接口

为你的技能系统创建适配器，实现 Provider 接口：

```csharp
using System.Collections.Generic;
using RAGBuilder;

/// <summary>
/// Action 提供者实现示例
/// </summary>
public class MyActionProvider : IActionProvider
{
    private Dictionary<string, IActionInfo> actionCache;

    public MyActionProvider()
    {
        // 扫描并缓存所有 Action 类型
        ScanActions();
    }

    public IEnumerable<IActionInfo> GetAllActions()
    {
        return actionCache.Values;
    }

    public IActionInfo GetAction(string typeName)
    {
        return actionCache.TryGetValue(typeName, out var info) ? info : null;
    }

    public bool HasAction(string typeName)
    {
        return actionCache.ContainsKey(typeName);
    }

    private void ScanActions()
    {
        // 实现你的 Action 扫描逻辑
    }
}
```

### 步骤 3：实现 IActionInfo 接口

```csharp
using System.Collections.Generic;
using RAGBuilder;

/// <summary>
/// Action 信息适配器
/// </summary>
public class MyActionInfo : IActionInfo
{
    public string TypeName { get; private set; }
    public string DisplayName { get; private set; }
    public string Category { get; private set; }
    public string Description { get; private set; }
    public string SearchText => $"{TypeName} {DisplayName} {Description} {Category}";
    public IReadOnlyList<IActionParameterInfo> Parameters { get; private set; }

    public MyActionInfo(System.Type actionType)
    {
        TypeName = actionType.Name;
        DisplayName = GetDisplayName(actionType);
        Category = GetCategory(actionType);
        Description = GetDescription(actionType);
        Parameters = ExtractParameters(actionType);
    }

    // 实现具体的提取逻辑...
}
```

### 步骤 4：注册适配器

在编辑器启动时注册你的 Provider：

```csharp
using RAGBuilder;
using RAGBuilder.Editor;
using UnityEditor;
using UnityEngine;

/// <summary>
/// RAG Builder 集成初始化
/// </summary>
[InitializeOnLoad]
public static class RAGBuilderSetup
{
    private const string CONFIG_PATH = "Assets/Data/RAGBuilderConfig.asset";

    static RAGBuilderSetup()
    {
        EditorApplication.delayCall += Initialize;
    }

    private static void Initialize()
    {
        // 加载配置
        var config = AssetDatabase.LoadAssetAtPath<RAGBuilderConfig>(CONFIG_PATH);
        if (config == null)
        {
            Debug.Log("[RAGBuilder] 未找到配置文件，请先创建配置");
            return;
        }

        // 创建 Provider
        var actionProvider = new MyActionProvider();
        var skillProvider = new MySkillProvider(); // 可选

        // 初始化服务
        RAGBuilderService.Instance.Initialize(
            config,
            actionProvider: actionProvider,
            skillProvider: skillProvider
        );

        Debug.Log("[RAGBuilder] 初始化完成");
    }
}
```

### 步骤 5：使用工具

通过菜单或设置界面使用各种功能：

- **Tools > RAG Builder > Start Server** - 启动 Python RAG 服务器
- **Tools > RAG Builder > Export Actions** - 导出 Action 定义为 JSON
- **Tools > RAG Builder > Export Skills** - 导出技能数据为 JSON
- **Tools > RAG Builder > Rebuild Index** - 重建 RAG 索引

## 核心接口

### IActionInfo

表示可被索引的 Action 类型：

```csharp
public interface IActionInfo
{
    string TypeName { get; }        // 类型名，如 "DamageAction"
    string DisplayName { get; }     // 显示名，如 "伤害"
    string Category { get; }        // 分类，如 "Damage"
    string Description { get; }     // 详细描述
    string SearchText { get; }      // 用于语义搜索的文本
    IReadOnlyList<IActionParameterInfo> Parameters { get; }  // 参数列表
}
```

### IActionParameterInfo

表示 Action 的参数信息：

```csharp
public interface IActionParameterInfo
{
    string Name { get; }            // 参数名
    string Type { get; }            // 类型名
    string DefaultValue { get; }    // 默认值
    string Label { get; }           // 显示标签
    string Description { get; }     // 参数描述
    bool IsArray { get; }           // 是否为数组
    bool IsEnum { get; }            // 是否为枚举
    IReadOnlyList<string> EnumValues { get; }  // 枚举值列表
    float? MinValue { get; }        // 最小值约束
    float? MaxValue { get; }        // 最大值约束
}
```

### ISkillInfo

表示可被索引的技能数据：

```csharp
public interface ISkillInfo
{
    string SkillId { get; }         // 技能 ID
    string SkillName { get; }       // 技能名称
    string Description { get; }     // 技能描述
    int TotalDuration { get; }      // 总时长（帧）
    int FrameRate { get; }          // 帧率
    IReadOnlyList<ISkillActionInstance> Actions { get; }  // Action 实例列表
    IReadOnlyList<string> Tags { get; }  // 标签列表
}
```

### IActionProvider / ISkillProvider

数据提供者接口：

```csharp
public interface IActionProvider
{
    IEnumerable<IActionInfo> GetAllActions();   // 获取所有 Action
    IActionInfo GetAction(string typeName);     // 按类型名获取
    bool HasAction(string typeName);            // 检查是否存在
}

public interface ISkillProvider
{
    IEnumerable<ISkillInfo> GetAllSkills();     // 获取所有技能
    ISkillInfo GetSkill(string skillId);        // 按 ID 获取
    ISkillInfo GetSkillByName(string name);     // 按名称获取
    IEnumerable<string> GetSkillFilePaths();    // 获取技能文件路径
    ISkillInfo LoadSkillFromFile(string path);  // 从文件加载技能
}
```

## 配置说明

`RAGBuilderConfig` ScriptableObject 包含以下可配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| Server Host | RAG 服务器地址 | `127.0.0.1` |
| Server Port | RAG 服务器端口 | `2024` |
| Request Timeout | HTTP 请求超时时间（秒） | `30` |
| Action Export Directory | Action JSON 导出目录 | `../skill_agent/Data/Actions` |
| Skill Export Directory | Skill JSON 导出目录 | `../skill_agent/Data/Skills` |
| Server Script Path | Python 服务器脚本路径 | `../skill_agent/langgraph_server.py` |
| WebUI URL | WebUI 访问地址 | `http://127.0.0.1:2024` |
| Auto Rebuild Index | 导出后自动重建索引 | `true` |
| Use Odin Inspector | 使用 Odin 增强 UI | `true` |

> **注意**：相对路径是相对于 Unity 项目根目录计算的。

## 菜单功能

包提供了以下 Unity 菜单项（位于 `Tools > RAG Builder`）：

| 菜单项 | 快捷键 | 说明 |
|--------|--------|------|
| Start Server | - | 启动 Python RAG 服务器 |
| Stop Server | - | 停止服务器 |
| Open WebUI | - | 在浏览器中打开 WebUI |
| Check Status | - | 检查当前状态 |
| Export Actions | - | 导出所有 Action 到 JSON |
| Export Skills | - | 导出所有 Skill 到 JSON |
| Rebuild Index | - | 触发服务器重建索引 |
| Open Settings | - | 打开偏好设置界面 |

## 迁移指南

将 RAG Builder 迁移到新项目的步骤：

### 1. 安装包

```bash
# 复制包到新项目
cp -r com.wqaetly.rag-builder /path/to/new-project/Packages/
```

### 2. 创建配置文件

在新项目中通过 `Edit > Preferences > RAG Builder` 创建配置，并根据项目结构调整路径：

```
Action Export Directory: ../your-agent/Data/Actions
Skill Export Directory: ../your-agent/Data/Skills
Server Script Path: ../your-agent/server.py
```

### 3. 实现适配器

根据你的 Action/Skill 系统实现相应的接口：

```csharp
// 1. 实现 IActionInfo 包装你的 Action 类型
public class YourActionInfo : IActionInfo { ... }

// 2. 实现 IActionProvider 提供 Action 数据
public class YourActionProvider : IActionProvider { ... }

// 3. （可选）实现 ISkillProvider 提供 Skill 数据
public class YourSkillProvider : ISkillProvider { ... }
```

### 4. 注册适配器

创建初始化脚本：

```csharp
[InitializeOnLoad]
public static class YourRAGSetup
{
    static YourRAGSetup()
    {
        EditorApplication.delayCall += () =>
        {
            var config = LoadYourConfig();
            RAGBuilderService.Instance.Initialize(
                config,
                actionProvider: new YourActionProvider(),
                skillProvider: new YourSkillProvider()
            );
        };
    }
}
```

### 5. 完成

现在可以通过菜单使用 RAG Builder 的所有功能了！

## 示例代码

完整的示例代码位于 `Samples~/SkillSystemAdapter` 目录：

- **SampleImplementations.cs** - `IActionInfo`、`ISkillInfo` 等接口的示例实现
- **SampleActionProvider.cs** - `IActionProvider` 的完整示例，演示如何扫描 Action 类型

通过 Package Manager 导入示例：
1. 打开 Package Manager
2. 选择 "RAG Builder System"
3. 在 "Samples" 下点击 "Import"

## 依赖项

### 必需依赖

- **UniTask** (`com.cysharp.unitask >= 2.0.0`)：用于异步操作

### 可选依赖

- **Odin Inspector**：提供增强的编辑器 UI（自动检测，如果存在则使用）

## API 参考

### RAGBuilderService

核心服务类，提供导出和管理功能：

```csharp
// 获取单例
var service = RAGBuilderService.Instance;

// 初始化
service.Initialize(config, actionProvider, skillProvider, descriptionStorage);

// 导出 Action
ExportResult result = service.ExportActions();

// 导出 Skill
ExportResult result = service.ExportSkills();

// 创建 RAG 客户端
RAGClient client = service.CreateClient();
```

### RAGServerManager

服务器管理静态类：

```csharp
// 启动服务器
bool success = RAGServerManager.StartServer(config);

// 停止服务器
RAGServerManager.StopServer();

// 检查服务器状态
bool running = RAGServerManager.IsServerRunning(config);

// 打开 WebUI
RAGServerManager.OpenWebUI(config);
```

### RAGClient

HTTP 客户端，用于与 RAG 服务器通信：

```csharp
var client = new RAGClient(config);

// 健康检查
StartCoroutine(client.CheckHealth((success, message) => { }));

// 搜索技能
StartCoroutine(client.SearchSkills("火球术", topK: 5, callback: (success, response, error) => { }));

// 推荐 Action
StartCoroutine(client.RecommendActions("造成范围伤害", topK: 3, callback: (success, response, error) => { }));

// 重建索引
StartCoroutine(client.RebuildIndex((success, response, error) => { }));
```

## 常见问题

### Q: 导出时提示 "Action provider not registered"

确保在编辑器启动时正确注册了 Provider：

```csharp
RAGBuilderService.Instance.Initialize(config, actionProvider: yourProvider);
```

### Q: 服务器启动失败

1. 检查 Python 环境是否正确配置
2. 检查 `serverScriptPath` 路径是否正确
3. 查看 Unity Console 中的错误日志

### Q: 如何自定义 Action 分类？

在你的 `IActionInfo` 实现中，根据 Action 类型名或自定义属性返回对应的分类：

```csharp
public string Category => GetCategoryFromType(actionType);

private string GetCategoryFromType(Type type)
{
    // 你的分类逻辑
    if (type.Name.Contains("Damage")) return "伤害";
    if (type.Name.Contains("Heal")) return "治疗";
    return "其他";
}
```

## 许可证

MIT License - 详见 [LICENSE.md](LICENSE.md)
