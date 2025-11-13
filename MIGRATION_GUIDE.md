# RAG功能迁移指南

## 📋 概述

本指南说明Unity RAG查询功能迁移到WebUI的详细情况，帮助用户快速适应新的工作流程。

**迁移日期**：2025-11-13
**影响范围**：Unity Editor RAG查询窗口、Inspector智能推荐
**迁移目标**：统一在WebUI中进行所有RAG查询和管理操作

---

## 🎯 为什么迁移？

### 原有架构的问题

1. **多端口混乱**：
   - Unity期望的`server.py`（端口8765）实际不存在
   - 导致Inspector智能推荐功能无法使用
   - 多个启动入口造成进程管理混乱

2. **职责不清**：
   - Unity窗口既要管理UI又要启动Python服务器
   - 描述管理器混杂了RAG索引重建功能
   - 代码耦合度高，难以维护

3. **用户体验差**：
   - 需要在Unity和浏览器间频繁切换
   - Inspector推荐功能实际不可用但用户不知情
   - 启动流程复杂，错误提示不友好

### 新架构的优势

- ✅ **统一后端服务**：所有功能通过`langgraph_server.py`（端口2024）提供
- ✅ **清晰的职责分离**：Unity专注于技能编辑，WebUI负责RAG查询
- ✅ **更好的可视化**：WebUI提供更丰富的查询和管理界面
- ✅ **易于扩展**：WebUI可以快速添加新的RAG功能
- ✅ **代码精简**：Unity Editor代码减少31.6%

---

## 📦 变更内容

### 已删除的功能

#### Unity Editor中移除：

**1. RAG查询窗口** (`SkillAgentWindow.cs`)
- ❌ 技能语义搜索界面
- ❌ Action推荐界面
- ❌ 索引管理界面
- ❌ 服务器启动/停止按钮

**2. Inspector智能推荐** (`SmartActionInspector.cs`)
- ❌ Action参数智能推荐UI
- ❌ 实时参数建议

**3. RAG客户端** (`EditorRAGClient.cs`)
- ❌ HTTP客户端封装
- ❌ 与端口8765的通信

**4. 描述管理器中的RAG功能** (`DescriptionManagerWindow.cs`)
- ❌ RAG服务器启动/停止按钮
- ❌ 服务器状态显示
- ❌ 重建索引按钮（步骤6）
- ❌ 服务器连接测试

#### Unity Editor中保留：

- ✅ 描述管理器的核心功能：
  - 扫描Actions
  - AI生成描述（DeepSeek）
  - 保存到数据库
  - 导出JSON
- ✅ 技能编辑器（`SkillEditorWindow`）- 完全保留
- ✅ `Tools → SkillAgent → 启动服务器` - 一键启动WebUI
- ✅ `Tools → SkillAgent → 打开Web UI` - 快速打开浏览器
- ✅ `Preferences → 技能系统 → RAG设置` - 配置WebUI地址
- ✅ `技能系统 → RAG功能 → 打开WebUI` - 菜单快捷方式

### 新增的功能

#### 后端API（`langgraph_server.py`）

新增7个RAG专用端点：

| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/rag/search` | POST | 技能语义搜索 | 替代Unity查询窗口的搜索功能 |
| `/rag/recommend-actions` | POST | Action类型推荐 | 替代Unity的Action推荐 |
| `/rag/recommend-parameters` | POST | 参数智能推荐 | 替代Inspector的参数推荐 |
| `/rag/index/rebuild` | POST | 重建RAG索引 | 替代Unity的重建索引按钮 |
| `/rag/index/stats` | GET | 索引统计信息 | 查看当前索引状态 |
| `/rag/cache` | DELETE | 清空查询缓存 | 清理缓存数据 |
| `/rag/health` | GET | RAG服务健康检查 | 对接WebUI的service-status.ts |

#### WebUI（计划开发）

**RAG查询页面** (`/rag`)：
- 🔄 技能语义搜索界面
- 🔄 Action智能推荐界面
- 🔄 参数推荐表单
- 🔄 索引管理面板
- 🔄 服务状态监控

> **注意**：WebUI前端页面需要在`agent-chat-ui`项目中开发。当前已完成后端API，WebUI开发待后续实施。

---

## 🚀 快速开始

### 1. 启动服务（Unity中）

在Unity Editor中：

```
菜单: Tools → SkillAgent → 启动服务器
```

这会执行`skill_agent/start_webui.bat`，启动：
- LangGraph Server（端口2024）- 提供所有RAG API
- WebUI前端（端口3000）- 可视化界面

### 2. 打开WebUI

**方式一**：Unity自动打开浏览器访问 `http://localhost:3000`

**方式二**：手动访问
```
Unity菜单: Tools → SkillAgent → 打开Web UI
```

**方式三**：在浏览器中直接访问
```
http://localhost:3000/rag
```

### 3. 配置WebUI地址（可选）

如果WebUI运行在其他端口：

```
Unity菜单: Edit → Preferences → 技能系统 → RAG设置
修改 "WebUI地址" 为实际地址（如 http://localhost:8080）
```

---

## 📖 新工作流程

### 场景1：搜索相似技能

**旧方式**（已废弃）：
```
Unity: 技能系统 → RAG查询窗口 → 搜索Tab → 输入查询
```

**新方式**：
```
1. Unity: Tools → SkillAgent → 启动服务器
2. 浏览器: http://localhost:3000/rag
3. 在搜索框输入查询（如"AOE伤害技能"）
4. 查看搜索结果（技能列表、相似度、详情）
```

**或使用对话界面**（临时方案）：
```
1. 浏览器: http://localhost:3000
2. 确保选择 skill-search 助手
3. 在对话框输入："查找所有AOE伤害类型的技能"
4. AI返回搜索结果
```

### 场景2：获取Action推荐

**旧方式**（已废弃）：
```
Unity: RAG查询窗口 → 推荐Tab → 输入上下文 → 获取推荐
```

**新方式（API调用）**：
```bash
curl -X POST http://localhost:2024/rag/recommend-actions \
  -H "Content-Type: application/json" \
  -d '{"context": "造成伤害并击退敌人", "top_k": 3}'
```

**新方式（WebUI - 待开发）**：
```
浏览器: http://localhost:3000/rag → Action推荐Tab
输入上下文 → 查看推荐列表
```

### 场景3：参数智能推荐（原Inspector功能）

**旧方式**（已失效）：
```
Unity Inspector: 编辑Action → 查看右侧智能推荐面板
```

**新方式（API调用）**：
```bash
curl -X POST http://localhost:2024/rag/recommend-parameters \
  -H "Content-Type: application/json" \
  -d '{"action_type": "DamageAction"}'
```

**新方式（WebUI - 待开发）**：
```
浏览器: http://localhost:3000/rag → 参数推荐Tab
选择技能 → 选择Action → 查看参数示例
```

### 场景4：重建RAG索引

**旧方式**（已废弃）：
```
方式1: Unity: 技能系统 → RAG功能 → 重建索引
方式2: Unity: 描述管理器 → 步骤6 → 重建索引
```

**新方式（API调用）**：
```bash
curl -X POST http://localhost:2024/rag/index/rebuild
```

**新方式（WebUI - 待开发）**：
```
浏览器: http://localhost:3000/rag → 索引管理Tab → 重建索引按钮
```

**Unity中的提示**：
当在描述管理器完成"一键完成全流程"后，会弹出提示：
```
✅ Action总数: 42
✅ 已生成描述: 42
✅ JSON已导出

💡 下一步：重建RAG索引
索引功能已迁移至WebUI。

1. 确保后端服务运行中（Tools → SkillAgent → 启动服务器）
2. 访问 http://localhost:3000/rag
3. 在索引管理页面点击"重建索引"按钮

[打开WebUI说明] [稍后处理] [关闭]
```

---

## 🔌 API 端点详细文档

### Base URL
```
http://localhost:2024
```

### 1. 技能语义搜索

**端点**: `POST /rag/search`

**请求体**:
```json
{
  "query": "AOE伤害技能",
  "top_k": 5,
  "filters": {
    "skillType": "Attack"
  }
}
```

**响应**:
```json
{
  "success": true,
  "query": "AOE伤害技能",
  "results": [
    {
      "skill_id": "skill_001",
      "skill_name": "火焰风暴",
      "similarity": 0.89,
      "skill_data": { ... }
    }
  ],
  "count": 5
}
```

### 2. Action类型推荐

**端点**: `POST /rag/recommend-actions`

**请求体**:
```json
{
  "context": "造成伤害并击退敌人",
  "top_k": 3
}
```

**响应**:
```json
{
  "success": true,
  "context": "造成伤害并击退敌人",
  "recommendations": [
    {
      "action_type": "DamageAction",
      "similarity": 0.92,
      "description": "造成伤害的基础Action"
    },
    {
      "action_type": "KnockbackAction",
      "similarity": 0.85,
      "description": "击退目标的Action"
    }
  ],
  "count": 2
}
```

### 3. 参数智能推荐

**端点**: `POST /rag/recommend-parameters`

**请求体**:
```json
{
  "action_type": "DamageAction",
  "skill_context": "火焰伤害技能"
}
```

**响应**:
```json
{
  "success": true,
  "action_type": "DamageAction",
  "parameter_examples": [
    {
      "action_type": "DamageAction",
      "parameters": {
        "damage": 100,
        "damageType": "Fire",
        "radius": 5.0
      },
      "source_skill": "火焰风暴",
      "similarity": 0.88
    }
  ],
  "count": 3
}
```

### 4. 重建索引

**端点**: `POST /rag/index/rebuild`

**响应**:
```json
{
  "success": true,
  "skill_index": {
    "status": "success",
    "count": 42,
    "elapsed_time": 2.34
  },
  "action_index": {
    "status": "success",
    "count": 120
  },
  "structured_index": {
    "status": "success"
  },
  "timestamp": "2025-11-13T10:30:00"
}
```

### 5. 索引统计

**端点**: `GET /rag/index/stats`

**响应**:
```json
{
  "success": true,
  "statistics": {
    "total_skills": 42,
    "total_actions": 120,
    "last_index_time": "2025-11-13T10:30:00",
    "cache_hits": 156
  },
  "timestamp": "2025-11-13T11:00:00"
}
```

### 6. 清空缓存

**端点**: `DELETE /rag/cache`

**响应**:
```json
{
  "success": true,
  "cleared_entries": 25,
  "timestamp": "2025-11-13T11:05:00"
}
```

### 7. 健康检查

**端点**: `GET /rag/health`

**响应**:
```json
{
  "status": "healthy",
  "indexed_skills": 42,
  "indexed_actions": 120,
  "cache_enabled": true,
  "last_index_time": "2025-11-13T10:30:00",
  "timestamp": "2025-11-13T11:10:00"
}
```

---

## ❓ 常见问题

### Q1: 为什么Unity中的RAG查询窗口消失了？

**A**: RAG查询功能已完全迁移到WebUI。原因：
- 原有的Unity查询窗口依赖的`server.py`（端口8765）实际不存在
- Inspector智能推荐功能因此无法工作
- 统一在WebUI中操作体验更好，功能更强大

### Q2: 我还能在Unity Inspector中看到参数推荐吗？

**A**: 不能。Inspector智能推荐功能已移除。请使用：
- **方式1**：在WebUI的参数推荐页面查看
- **方式2**：调用API获取参数示例后手动填写

### Q3: 如何验证后端服务是否正常运行？

**A**: 三种方式：
```bash
# 方式1: 检查根端点
curl http://localhost:2024/

# 方式2: 检查RAG健康状态
curl http://localhost:2024/rag/health

# 方式3: Unity菜单
Tools → SkillAgent → 检查服务器状态
```

### Q4: 描述管理器的"一键完成全流程"还能用吗？

**A**: 能用，但有变化：
- ✅ 步骤1-4正常（扫描、生成、保存、导出）
- ❌ 不再自动重建RAG索引
- ℹ️ 完成后会提示你在WebUI中手动重建索引

### Q5: WebUI在哪里？我看不到RAG查询页面！

**A**: WebUI前端页面**尚未开发**。当前状态：
- ✅ 后端API已完成（7个端点全部可用）
- ✅ 可通过curl或Postman调用API
- ❌ WebUI可视化界面待开发（在`agent-chat-ui`项目中）
- 🔄 临时方案：使用对话界面（切换到skill-search助手）

### Q6: 如果我还想要Unity中的查询窗口怎么办？

**A**: 可以从git历史恢复旧版本，但**不推荐**，因为：
- 原有架构依赖的后端服务不存在，无法正常工作
- 会与当前的后端API架构冲突
- 维护成本高

### Q7: 新的API性能如何？会比Unity窗口慢吗？

**A**: 性能**更好**：
- 统一后端避免多进程开销
- 查询缓存机制（TTL缓存）
- 批量操作支持（待WebUI实现）

### Q8: 如何测试新的API是否正常？

**A**: 使用curl测试：
```bash
# 测试搜索
curl -X POST http://localhost:2024/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "治疗技能", "top_k": 3}'

# 测试Action推荐
curl -X POST http://localhost:2024/rag/recommend-actions \
  -H "Content-Type: application/json" \
  -d '{"context": "造成伤害", "top_k": 3}'
```

### Q9: 启动后端服务失败怎么办？

**A**: 检查以下几点：
1. Python环境是否正确（Python 3.8+）
2. 依赖是否安装（`pip install -r requirements.txt`）
3. 端口2024是否被占用
4. 查看`skill_agent/logs/`目录的错误日志

### Q10: 可以同时使用多个Unity Editor访问同一个后端吗？

**A**: 可以！新架构支持多客户端：
- 多个Unity Editor可以同时调用API
- WebUI和Unity可以同时使用
- 所有客户端共享同一个RAG索引

---

## 🛠️ 开发者指南

### 如果需要开发WebUI前端

**项目位置**: `agent-chat-ui`（独立项目）

**推荐技术栈**:
- React + TypeScript
- Tailwind CSS + shadcn/ui
- API调用：使用`fetch`或`axios`

**示例代码**:

```typescript
// webui/src/app/rag/page.tsx
"use client";

import { useState } from "react";

export default function RAGQueryPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:2024/rag/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 5 })
      });
      const data = await response.json();
      setResults(data.results);
    } catch (error) {
      console.error("Search failed:", error);
    }
    setLoading(false);
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">RAG技能查询</h1>

      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入查询（如：AOE伤害技能）"
          className="flex-1 border rounded px-4 py-2"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-blue-500 text-white px-6 py-2 rounded"
        >
          {loading ? "搜索中..." : "搜索"}
        </button>
      </div>

      <div className="space-y-4">
        {results.map((skill, i) => (
          <div key={i} className="border p-4 rounded">
            <h3 className="font-bold">{skill.skill_name}</h3>
            <p>相似度: {(skill.similarity * 100).toFixed(1)}%</p>
            <p className="text-gray-600">{skill.skill_id}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 如果需要扩展API

**文件位置**: `skill_agent/langgraph_server.py`

**添加新端点示例**:
```python
@app.post("/rag/custom-feature")
async def custom_rag_feature(request: CustomRequest):
    """自定义RAG功能"""
    try:
        from orchestration.tools.rag_tools import get_rag_engine

        engine = get_rag_engine()
        # 实现你的逻辑
        result = engine.custom_method(request.params)

        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Custom feature error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📞 获取帮助

### 遇到问题？

1. **查看日志**:
   ```
   skill_agent/logs/langgraph_server.log
   ```

2. **检查API文档**:
   ```
   http://localhost:2024/docs（FastAPI自动生成）
   ```

3. **查看源码**:
   - 后端API: `skill_agent/langgraph_server.py`
   - RAG引擎: `skill_agent/core/rag_engine.py`
   - Unity集成: `Assets/Scripts/RAGSystem/Editor/`

### 反馈渠道

- 项目Issues: [GitHub Issues](your-repo-url)
- 技术文档: `skill_agent/Docs/`
- 联系开发者: [your-contact]

---

## 📅 更新日志

### v2.0.0 (2025-11-13)

**重大变更**:
- ✨ 新增7个RAG API端点（`/rag/*`）
- 🗑️ 移除Unity RAG查询窗口
- 🗑️ 移除Inspector智能推荐
- 🗑️ 移除Unity端RAG服务器启动功能
- 📝 简化描述管理器（减少467行代码）
- 🔄 统一后端服务架构（端口2024）

**兼容性**:
- Unity Editor: 2021.3+ (无变化)
- Python: 3.8+ (无变化)
- 新增依赖: FastAPI, Uvicorn (已在requirements.txt)

---

## ✅ 检查清单

迁移后请确认以下功能正常：

- [ ] Unity启动服务器：`Tools → SkillAgent → 启动服务器`
- [ ] Unity打开WebUI：`Tools → SkillAgent → 打开Web UI`
- [ ] 后端API健康检查：`curl http://localhost:2024/rag/health`
- [ ] 技能搜索API：`curl -X POST http://localhost:2024/rag/search -d '...'`
- [ ] 描述管理器：扫描、生成、保存、导出功能正常
- [ ] 一键完成全流程：显示迁移提示对话框
- [ ] Unity菜单：`技能系统 → RAG功能 → 打开WebUI` 可用
- [ ] Preferences：`技能系统 → RAG设置` 可配置WebUI地址

---

**文档版本**: v1.0
**最后更新**: 2025-11-13
**维护者**: [Your Name]
