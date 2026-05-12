# RAG Skill Agent - Unity 技能配置智能助手

基于 RAG（检索增强生成）技术的 Unity 技能配置智能助手系统。通过 AI 分析游戏技能系统源码，自动生成高质量的技能配置 JSON。

## 🎯 系统概述

本系统解决的核心问题：**让 AI 理解你的技能系统，自动生成符合项目规范的技能配置**。

```
┌─────────────────────────────────────────────────────────────────────┐
│                         整体架构                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Unity Editor                        Python RAG Server             │
│   ┌─────────────────┐                ┌─────────────────┐            │
│   │ 1. 源码分析      │                │ 4. 向量索引      │            │
│   │ 2. 类型扫描      │ ──── JSON ──→ │ 5. 语义检索      │            │
│   │ 3. AI描述生成    │                │ 6. LLM 生成      │            │
│   └─────────────────┘                └─────────────────┘            │
│          ↑                                    │                     │
│          └──────────── 技能配置 JSON ←────────┘                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔄 工作原理

### 阶段一：数据准备（Unity 端）

```
源码 → AI 架构分析 → 类型扫描 → AI 描述生成 → JSON 导出
```

1. **架构分析**：使用 DeepSeek API 分析技能系统源码，理解基类、生命周期、参数语义
2. **类型扫描**：通过反射扫描所有 Action/Buff 类型，提取参数信息
3. **描述生成**：AI 基于架构理解，为每个 Action 生成语义描述
4. **JSON 导出**：将所有元数据导出为结构化 JSON 文件

### 阶段二：索引构建（Python 端）

```
JSON 文件 → 文本嵌入 → 向量索引 → LanceDB 存储
```

1. **加载 JSON**：读取 Unity 导出的 Action/Buff/Skill JSON 文件
2. **文本嵌入**：使用 Qwen3-Embedding 模型将描述转为向量
3. **索引存储**：将向量存入 LanceDB，支持高效语义检索

### 阶段三：技能生成（运行时）

```
用户需求 → 语义检索 → RAG 增强 → LLM 生成 → 技能 JSON
```

1. **需求理解**：解析用户自然语言描述的技能需求
2. **RAG 检索**：从向量库检索相似技能和相关 Action
3. **上下文增强**：将检索结果作为 LLM 参考上下文
4. **配置生成**：LLM 生成符合项目规范的技能配置 JSON

## 📋 目录

- [功能特性](#功能特性)
- [工作原理详解](#工作原理详解)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [核心接口](#核心接口)
- [菜单功能](#菜单功能)
- [依赖项](#依赖项)

## 功能特性

- **🤖 AI 架构分析**：自动分析技能系统源码，理解项目特定的设计模式
- **📊 智能描述生成**：基于源码上下文，为 Action 参数生成准确的语义描述
- **🔍 语义检索**：基于向量相似度检索相关技能和 Action，非关键词匹配
- **⚡ 一键导出**：扫描、生成描述、导出 JSON、通知重建索引一气呵成
- **🎛️ 可视化配置**：通过 Editor Window 配置所有参数，无需修改代码
- **🔌 解耦架构**：使用接口适配任何技能/动作系统

## 🔬 工作原理详解

### 1. AI 架构分析

系统首先使用 DeepSeek API 分析你的技能系统源码：

```csharp
// SystemArchitectureAnalyzer.cs 核心逻辑
1. 收集源码文件 → config.skillSystemSourcePaths
2. 构建分析 Prompt → 包含源码 + 分析指令
3. 调用 DeepSeek API → 获取架构理解文档
4. 保存到 RAGConfig → skillSystemArchitecturePrompt
```

**分析输出示例**：
```markdown
## 核心基类
- ActionBase: 所有技能行为的基类，通过帧判断控制执行时机

## 生命周期方法
- OnEnter(): Action 开始时调用
- OnUpdate(): 每帧调用，activeFrame 内有效
- OnExit(): Action 结束时调用

## 参数命名规范
- xxxDuration: 持续时间（帧）
- xxxRadius: 作用半径
- xxxPrefab: 特效/投射物预制体
```

### 2. 类型扫描与反射

扫描程序集中所有符合条件的类型：

```csharp
// ActionScanner.cs 扫描逻辑
var actionTypes = AppDomain.CurrentDomain.GetAssemblies()
    .SelectMany(a => a.GetTypes())
    .Where(t => !t.IsAbstract && typeof(ISkillAction).IsAssignableFrom(t));

foreach (var type in actionTypes)
{
    var entry = new ActionEntry
    {
        typeName = type.Name,
        parameters = ExtractSerializedFields(type),  // 提取 [SerializeField] 字段
        // ...
    };
}
```

### 3. AI 描述生成

结合架构理解，为每个 Action 生成语义描述：

```
输入：
- Action 类型名：DamageAreaAction
- 参数列表：damage(float), radius(float), effectPrefab(GameObject)
- 架构 Prompt：（包含生命周期、参数规范等）

输出：
- displayName: "范围伤害"
- category: "伤害"
- description: "在指定范围内对所有敌人造成伤害并播放特效"
- parameterDescriptions: {
    damage: "造成的伤害数值",
    radius: "伤害作用半径（米）",
    effectPrefab: "伤害特效预制体"
  }
```

### 4. JSON 导出格式

```json
// DamageAreaAction.json
{
  "version": "1.0",
  "exportTime": "2024-01-15T10:30:00",
  "action": {
    "typeName": "DamageAreaAction",
    "fullTypeName": "SkillSystem.Actions.DamageAreaAction",
    "displayName": "范围伤害",
    "category": "伤害",
    "description": "在指定范围内对所有敌人造成伤害",
    "searchText": "DamageAreaAction 范围伤害 伤害 AOE 群伤",
    "parameters": [
      {
        "name": "damage",
        "type": "Single",
        "description": "造成的伤害数值",
        "defaultValue": "100"
      },
      {
        "name": "radius",
        "type": "Single",
        "description": "伤害作用半径（米）",
        "defaultValue": "5"
      }
    ]
  }
}
```

### 5. 向量检索流程

```python
# Python 端检索逻辑
def search_actions(query: str, top_k: int = 5):
    # 1. 将查询文本向量化
    query_embedding = embedding_model.encode(query)

    # 2. 从 LanceDB 检索相似向量
    results = action_table.search(query_embedding).limit(top_k).to_list()

    # 3. 返回最相关的 Actions
    return [ActionSchema.parse(r) for r in results]
```

### 6. 技能生成流程

```python
# Langflow 工作流（在项目仓库 langflow/components/ 下以 Custom Component 实现）
def generate_skill(requirement: str):
    # 1. 需求理解
    parsed = understand_requirement(requirement)

    # 2. RAG 检索
    similar_skills = search_skills(parsed.keywords)
    relevant_actions = search_actions(parsed.action_needs)

    # 3. 构建 Prompt
    prompt = build_generation_prompt(
        requirement=requirement,
        reference_skills=similar_skills,
        available_actions=relevant_actions,
        architecture_prompt=get_architecture_prompt()
    )

    # 4. LLM 生成
    skill_json = llm.generate(prompt)

    # 5. 验证 & 修复
    validated = validate_and_fix(skill_json)

    return validated
```

## 📁 包结构

```
com.rag.skill-agent/
├── Editor/
│   ├── SkillSystem/              # 技能系统核心
│   │   ├── RAGConfig.cs          # 配置 ScriptableObject
│   │   ├── RAGConfigEditorWindow.cs  # 配置编辑器窗口
│   │   ├── SystemArchitectureAnalyzer.cs  # AI 架构分析
│   │   ├── ActionScanner.cs      # Action 类型扫描
│   │   ├── ActionJSONExporter.cs # JSON 导出器
│   │   ├── AIDescriptionGenerator.cs  # AI 描述生成
│   │   └── DeepSeekClient.cs     # DeepSeek API 客户端
│   ├── BuffSystem/               # Buff 系统支持
│   │   ├── BuffScanner.cs        # Buff 类型扫描
│   │   └── BuffJSONExporter.cs   # Buff JSON 导出
│   ├── UnifiedExport/            # 统一导出中心
│   │   └── UnifiedRAGExportWindow.cs
│   └── Docs/                     # 文档
│       └── RAG导出流程指南.md
└── Runtime/                      # 运行时（接口定义）
```

## 🚀 快速开始

### 步骤 1：配置 DeepSeek API

1. 打开菜单 **Tools → RAG System → RAG Config 设置**
2. 切换到 **DeepSeek** Tab
3. 输入 API Key（获取：https://platform.deepseek.com）
4. 点击 **测试连接** 验证

### 步骤 2：配置类型扫描

在 **技能系统** Tab 中配置：
- 程序集名称（如 `Assembly-CSharp`）
- Action 基类全名（如 `SkillSystem.ActionBase`）
- Action 接口全名（如 `SkillSystem.ISkillAction`）

### 步骤 3：执行架构分析（推荐）

在 **架构分析** Tab 中：
1. 配置技能系统源码路径
2. 点击 **🤖 AI 分析系统架构**
3. 等待分析完成

### 步骤 4：导出数据

1. 打开 **Tools → RAG System → 数据导出中心**
2. 检查扫描到的 Actions
3. 点击 **AI 生成描述**（为缺少描述的项生成）
4. 点击 **导出全部**

### 步骤 5：启动后端服务

在仓库根目录运行 `launch.bat`（菜单 `[1] Full System` 会拉起 Langflow @7860 + OpenAI 兼容适配层 @2024 + Lobe Chat @3210）。

- 策划使用：访问 http://127.0.0.1:3210 （Lobe Chat）
- 调试/Flow 可视化：访问 http://127.0.0.1:7860 （Langflow Playground）

## ⚙️ 配置说明

通过 **RAG Config 设置** 窗口配置所有参数：

| Tab | 主要配置项 |
|-----|-----------|
| **架构分析** | 源码路径、Prompt模板、AI分析参数 |
| **技能系统** | 程序集名称、Action基类/接口、导出配置 |
| **Buff系统** | Effect/Trigger基类、导出目录 |
| **DeepSeek** | API Key、模型选择、温度参数 |
| **服务器** | OpenAI 兼容适配层地址、端口、Lobe Chat URL |
| **路径** | 数据库路径、导出目录、自动通知设置 |

## 🍔 菜单功能

**Tools → RAG System** 菜单：

| 菜单项 | 说明 |
|--------|------|
| RAG Config 设置 | 打开配置窗口 |
| 数据导出中心 | 打开统一导出窗口 |
| Action 描述管理 | 管理 Action 描述数据库 |
| 启动服务器 | 启动 Python RAG 服务器【已废弃，请使用仓库根的 launch.bat】 |
| 打开 Lobe Chat | 在浏览器中打开 Lobe Chat（默认 http://127.0.0.1:3210） |

## ❓ 常见问题

### Q: 扫描不到 Action 类？

1. 检查程序集名称是否正确（技能系统 Tab）
2. 确认 Action 基类/接口配置正确
3. 确保类是 `public` 且非 `abstract`

### Q: AI 描述生成失败？

1. 检查 DeepSeek API Key 是否有效
2. 点击 **测试连接** 验证
3. 检查网络连接

### Q: 架构分析结果不理想？

1. 确保源码路径配置正确
2. 可以编辑 Prompt 模板优化分析指令
3. 或使用自定义 Prompt 文件覆盖

### Q: Python 端读取不到数据？

1. 确认 JSON 文件已导出到 `skill_agent/Data/`
2. 检查路径配置
3. 重启 Python 服务器

## 📚 相关文档

- [RAG导出流程指南](Editor/Docs/RAG导出流程指南.md) - 详细的导出流程说明

## 🔗 技术栈

| 组件 | 技术 |
|------|------|
| AI 分析 | DeepSeek API |
| 文本向量化 | Qwen3-Embedding-0.6B |
| 向量数据库 | LanceDB |
| 工作流编排 | Langflow（fork: wqaetly/langflow @ dev）|
| 后端服务 | FastAPI（OpenAI 兼容适配层 @2024） |
| 聊天前端 | Lobe Chat（官方镜像 @3210） |

## 📄 许可证

MIT License
