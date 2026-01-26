# RAG 系统数据导出流程指南

本文档介绍如何使用 Unity RAG 系统完成技能/Buff 数据的导出，为 Python 端 RAG 检索提供数据支持。

## 📋 概述

RAG 系统通过以下流程实现技能配置的智能生成：

```
Unity 项目 → 扫描 Action/Buff → AI 生成描述 → 导出 JSON → Python RAG 索引 → 技能生成
```

---

## 🚀 快速开始

### 1. 打开配置中心

**菜单：** `Tools → RAG System → RAG Config 设置`

### 2. 配置 DeepSeek API

在 **DeepSeek** Tab 中：
- 输入 API Key（获取地址：https://platform.deepseek.com）
- 点击 **测试连接** 验证配置

### 3. 执行架构分析（可选但推荐）

在 **架构分析** Tab 中：
1. 配置 **技能系统源码路径**（如 `Assets/Scripts/SkillSystem/Actions`）
2. 配置 **Buff 系统源码路径**（如 `Assets/Scripts/BuffSystem`）
3. 点击 **🤖 AI 分析系统架构**

> 架构分析会让 AI 理解你的技能系统设计，从而生成更准确的描述。

### 4. 导出数据

**菜单：** `Tools → RAG System → 数据导出中心`

在导出窗口中：
1. **Actions Tab**: 选择要导出的 Actions，点击 **导出选中**
2. **Buff Tab**: 选择要导出的 Buff Effects/Triggers，点击 **导出选中**
3. 或直接点击 **导出全部**

---

## 📁 导出目录结构

默认导出到 `skill_agent/Data/` 目录：

```
skill_agent/Data/
├── Actions/                    # 技能 Action JSON 文件
│   ├── DamageAction.json
│   ├── MoveAction.json
│   └── ...
├── Buffs/
│   ├── Effects/               # Buff 效果 JSON 文件
│   │   ├── DamageOverTimeEffect.json
│   │   └── ...
│   ├── Triggers/              # Buff 触发器 JSON 文件
│   │   └── ...
│   └── BuffEnums.json         # Buff 枚举定义
└── skill_system_config.json   # 项目配置（类型映射等）
```

---

## 🔧 详细配置说明

### 路径配置（路径 Tab）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| 数据库路径 | Action 描述数据库的 Asset 路径 | `Assets/Data/ActionDescriptionDatabase.asset` |
| 导出目录 | JSON 导出目录 | `../skill_agent/Data/Actions` |
| 自动通知重建 | 导出后自动通知服务器重建索引 | ✅ |

### 技能系统配置（技能系统 Tab）

| 配置项 | 说明 |
|--------|------|
| 程序集名称 | 包含 Action 类的程序集 |
| Action 基类 | Action 类的基类全名 |
| Action 接口 | Action 实现的接口全名 |

### Buff 系统配置（Buff系统 Tab）

| 配置项 | 说明 |
|--------|------|
| Buff Effect 基类 | Buff 效果基类全名 |
| Buff Trigger 基类 | Buff 触发器基类全名 |
| 导出目录 | Buff JSON 导出目录 |

---

## 📝 导出 JSON 格式示例

### Action JSON

```json
{
    "version": "1.0",
    "exportTime": "2024-01-15T10:30:00",
    "action": {
        "typeName": "DamageAction",
        "fullTypeName": "SkillSystem.Actions.DamageAction",
        "displayName": "造成伤害",
        "category": "伤害",
        "description": "对目标造成指定数值的伤害",
        "parameters": [
            {
                "name": "damage",
                "type": "float",
                "description": "伤害数值"
            }
        ]
    }
}
```

### Buff Effect JSON

```json
{
    "version": "1.0",
    "exportTime": "2024-01-15T10:30:00",
    "dataType": "BuffEffect",
    "effect": {
        "typeName": "DamageOverTimeEffect",
        "displayName": "持续伤害",
        "description": "每秒造成伤害",
        "parameters": [...]
    }
}
```

---

## ⚡ 常用操作

### 一键导出流程

1. 打开数据导出中心
2. 点击 **导出全部** 按钮
3. 等待完成（自动重建索引）

### AI 批量生成描述

1. 打开数据导出中心
2. 选择缺少描述的 Actions
3. 点击 **AI 生成描述**
4. 等待完成后点击 **保存到数据库**
5. 再次导出 JSON

### 导出配置到 Python 端

在技能系统/Buff系统 Tab 中点击 **导出配置到 Python 端**，会生成 `skill_system_config.json` 供 Python 端读取类型映射。

---

## 🖥️ Python 端使用

### 启动服务器

```bash
cd skill_agent
python langgraph_server.py
```

服务器默认端口 **2024**，提供以下功能：
- 技能检索 API
- 技能生成 API
- WebUI（http://127.0.0.1:2024）

### 数据加载

Python 端会自动从 `Data/` 目录加载：
- `Actions/*.json` → 构建 Action 向量索引
- `Buffs/Effects/*.json` → 构建 Buff Effect 向量索引
- `Buffs/Triggers/*.json` → 构建 Buff Trigger 向量索引
- `BuffEnums.json` → 枚举类型定义

### 重建索引

导出新数据后，需要重建索引：
- **自动**：开启"导出后自动通知重建索引"
- **手动**：调用 API `/api/rebuild_index`

---

## ❓ 常见问题

### Q: 扫描不到 Action 类？

检查技能系统配置：
1. 程序集名称是否正确
2. Action 基类/接口是否配置
3. 类是否为 `public` 且非 `abstract`

### Q: AI 描述生成失败？

1. 检查 DeepSeek API Key 是否有效
2. 点击 **测试连接** 验证
3. 检查网络连接

### Q: 导出的 JSON 文件不完整？

1. 确保先保存描述数据库
2. 检查导出目录权限
3. 查看 Console 日志获取详细错误

### Q: Python 端读取不到数据？

1. 确认 JSON 文件已导出
2. 检查路径配置是否指向 `skill_agent/Data/`
3. 重启 Python 服务器

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `RAGConfig.cs` | 配置 ScriptableObject |
| `RAGConfigEditorWindow.cs` | 配置编辑器窗口 |
| `ActionJSONExporter.cs` | Action JSON 导出器 |
| `BuffJSONExporter.cs` | Buff JSON 导出器 |
| `SystemArchitectureAnalyzer.cs` | AI 架构分析器 |
| `DescriptionManagerWindow.cs` | Action 描述管理窗口 |
| `UnifiedRAGExportWindow.cs` | 统一导出中心 |

---

## 🔗 完整工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                      Unity 编辑器                                │
├─────────────────────────────────────────────────────────────────┤
│  1. 配置 RAGConfig                                               │
│     ↓                                                           │
│  2. AI 分析系统架构 → 生成架构 Prompt                             │
│     ↓                                                           │
│  3. 扫描 Actions/Buffs → AI 生成描述 → 保存数据库                  │
│     ↓                                                           │
│  4. 导出 JSON 文件                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     skill_agent/Data/                           │
│  Actions/*.json  |  Buffs/*.json  |  skill_system_config.json   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Python RAG 服务                            │
├─────────────────────────────────────────────────────────────────┤
│  1. 加载 JSON → 构建向量索引                                     │
│     ↓                                                           │
│  2. 用户输入需求 → RAG 检索相似技能/Actions                       │
│     ↓                                                           │
│  3. LLM 生成技能配置 JSON                                        │
│     ↓                                                           │
│  4. 返回给 Unity 应用                                            │
└─────────────────────────────────────────────────────────────────┘
```
