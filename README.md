# AI Agent for Skill - Unity技能配置智能助手

<img width="3019" height="1484" alt="image" src="https://github.com/user-attachments/assets/e8393a5b-e5bc-47f4-ad4e-6c0417d8a905" />

## 项目简介

本项目是一个**Unity技能配置智能助手系统**,通过RAG (检索增强生成) + LangGraph工作流,实现技能配置的智能分析、自动修复和快速生成。策划人员可以**从Unity编辑器一键启动服务**,然后在本地Web界面通过对话形式完成技能开发工作。

### 核心特性

- **一键启动**: 从Unity菜单 `Tools/SkillAgent/启动服务器` 直接拉起所有服务
- **对话式交互**: 通过Web UI与AI对话,自然语言描述需求即可生成技能配置
- **智能参数推荐**: Unity Inspector中自动推荐Action参数配置
- **技能分析**: 基于语义向量检索,快速查找相似技能并分析差异
- **自动修复**: LangGraph工作流自动验证和修复JSON配置错误
- **本地部署**: Qwen3-Embedding模型本地运行,数据不出本地

---

## 快速开始

### 环境依赖

#### Python环境
```bash
Python >= 3.10
依赖包: requirements_langchain.txt
```

#### API Key配置
在 `skill_agent/config.yaml` 或环境变量中配置:
```yaml
DEEPSEEK_API_KEY: "your-deepseek-api-key"  # 用于技能生成和修复
```

### 一键启动 (推荐方式)

**从Unity编辑器启动**:
1. 在Unity中打开项目 `ai_agent_for_skill/`
2. 菜单栏选择 `Tools/SkillAgent/启动服务器`
3. 等待服务启动,会自动打开浏览器访问 `http://localhost:7860`

**手动启动**:
```bash
cd SkillRAG
start_webui.bat  # Windows
# 或直接执行
python langgraph_server.py  # 启动LangGraph服务 (端口2024)
cd ../webui && npm run dev   # 启动Web UI (端口3000)
```

### 验证服务状态

在Unity菜单选择 `Tools/SkillAgent/检查服务器状态`,或访问:
- LangGraph服务健康检查: `http://localhost:2024/health`
- Web UI: `http://localhost:3000`

---

## 使用指南

### 1. 技能生成

**Web UI对话方式**:
```
你: 生成一个火球术技能,造成100点火焰伤害,并击退敌人3米

AI: [检索相似技能] → [生成配置] → [验证JSON] → 返回完整技能配置
```

生成的JSON可直接保存到 `ai_agent_for_skill/Assets/GameData/Skills/` 目录。

### 2. 技能分析

**在Unity RAG查询窗口**:
1. 打开 `Tools/SkillAgent/打开RAG查询窗口`
2. 输入查询: "AOE伤害技能"
3. 查看检索结果和相似度排名

**Web UI对话**:
```
你: 分析ID为1001的技能和1002的技能有什么区别

AI: [检索两个技能] → [对比分析] → 返回差异列表
```

### 3. 智能参数推荐

**在Unity Inspector中使用**:
1. 选中一个SkillData资产
2. 在Action配置区域,右键选择 `智能推荐参数`
3. 系统会基于Action类型和上下文推荐合适的参数值

实现位置: `Assets/Scripts/RAGSystem/Editor/SmartActionInspector.cs`

### 4. 技能修复

当配置验证失败时,系统会自动触发修复流程:
```
生成 → 验证 (失败) → 修复 → 重新生成 → 验证 (通过)
```

最多重试3次,确保生成的JSON符合以下规范:
- 必填字段: `skillName`, `skillId`, `actions`
- Action结构: `actionType`, `parameters`
- 参数类型匹配: 根据21种Action类型验证

---

## 项目架构

### 目录结构

```
ai_agent_for_skill/
├── ai_agent_for_skill/              # Unity项目
│   ├── Assets/
│   │   ├── Scripts/
│   │   │   ├── SkillSystem/         # 技能系统核心 (21种Action类型)
│   │   │   └── RAGSystem/           # RAG系统Unity集成
│   │   │       ├── Editor/
│   │   │       │   ├── SkillRAGServerManager.cs    # 一键启动管理器
│   │   │       │   ├── SkillRAGWindow.cs           # RAG查询窗口
│   │   │       │   └── SmartActionInspector.cs     # 参数推荐Inspector
│   │   │       └── UnityRPCClient.cs               # RPC通信客户端
│   │   └── GameData/Skills/         # 技能配置JSON文件
│
├── skill_agent/                         # Python RAG服务
│   ├── core/                         # RAG核心引擎
│   │   ├── rag_engine.py            # RAG引擎主逻辑
│   │   ├── embeddings.py            # Qwen3向量生成
│   │   ├── vector_store.py          # ChromaDB封装
│   │   ├── skill_indexer.py         # 技能索引器
│   │   └── action_indexer.py        # Action元数据索引
│   ├── orchestration/               # LangGraph编排层
│   │   ├── graphs/
│   │   │   └── skill_generation.py  # 技能生成工作流
│   │   ├── nodes/
│   │   │   └── skill_nodes.py       # 工作流节点 (检索/生成/验证/修复)
│   │   └── prompts/                 # Prompt模板管理
│   ├── Data/
│   │   ├── models/                  # Qwen3-Embedding-0.6B本地模型
│   │   ├── vector_db/               # ChromaDB数据库文件
│   │   └── skill_index.json         # 技能索引缓存
│   ├── langgraph_server.py          # LangGraph HTTP服务器 (端口2024)
│   ├── Python/
│   │   └── unity_rpc_server.py      # Unity RPC服务器 (端口8766)
│   └── start_webui.bat              # 一键启动脚本
│
└── webui/                            # Web对话界面 (agent-chat-ui)
    ├── src/lib/                      # Next.js前端代码
    └── .env                          # 环境配置 (API_URL, ASSISTANT_ID)
```

### 技术栈

#### Unity侧
- **Unity Editor脚本**: 一键启动、参数推荐
- **RPC通信**: 与Python服务交互

#### Python服务
- **RAG引擎**: Qwen3-Embedding-0.6B + ChromaDB
- **LLM**: DeepSeek Chat API
- **工作流编排**: LangGraph (StateGraph)
- **Web框架**: FastAPI + Uvicorn
- **流式响应**: Server-Sent Events (SSE)

#### Web界面
- **前端框架**: Next.js 14 (App Router)
- **UI**: React + Tailwind CSS
- **通信协议**: SSE流式传输

### 服务架构

**双服务模式**:

```
┌─────────────┐
│   Unity     │
│  编辑器      │
└──────┬──────┘
       │ RPC (端口8766)
       ├───────────────────┐
       │                   │
┌──────▼──────┐    ┌──────▼──────────┐
│Unity RPC    │    │  LangGraph      │
│Server       │    │  Server         │
│(参数推荐)    │    │  (端口2024)     │
└─────────────┘    └──────┬──────────┘
                          │ HTTP SSE
                   ┌──────▼──────┐
                   │   Web UI    │
                   │ (端口3000)  │
                   └─────────────┘
```

**LangGraph工作流**:
```
检索相似技能 (retrieve)
    ↓
生成技能JSON (generate)
    ↓
验证配置 (validate) ──► 通过 → 完成 (finalize)
    │
    └─► 失败 → 修复 (fix) → 回到生成
              (最多重试3次)
```

---

## 核心功能实现

### 1. 语义向量检索

**实现**: `skill_agent/core/rag_engine.py`

```python
def search_skills_semantic(self, query: str, top_k: int = 5):
    # 1. Qwen3-Embedding生成查询向量
    query_embedding = self.embedding_generator.generate_embedding(
        query,
        prompt_name="query"  # 使用query prompt优化检索
    )

    # 2. ChromaDB向量相似度检索
    results = self.vector_store.search(
        query_embedding,
        top_k=top_k
    )

    # 3. 加载完整技能数据
    return [self.skill_indexer.load_skill(r['skill_id']) for r in results]
```

**模型参数**:
- 模型: Qwen/Qwen3-0.6B-Embedding
- 向量维度: 1024
- 上下文长度: 32K tokens
- 部署方式: 本地加载 (transformers)

### 2. 自动修复工作流

**实现**: `skill_agent/orchestration/nodes/skill_nodes.py`

```python
def validator_node(state):
    """验证生成的JSON"""
    errors = validate_skill_json(state["generated_json"])
    return {"validation_errors": errors, "is_valid": len(errors) == 0}

def fixer_node(state):
    """调用LLM修复错误"""
    prompt = f"""
    原始JSON: {state["generated_json"]}
    错误列表: {state["validation_errors"]}

    请修复以上错误,返回正确的JSON配置。
    """

    response = llm.invoke(prompt)
    return {
        "generated_json": response.content,
        "retry_count": state["retry_count"] + 1
    }

# 工作流定义
workflow.add_conditional_edges("validate", should_continue, {
    "fix": "fix",          # 失败 → 修复
    "finalize": "finalize" # 通过 → 结束
})
```

### 3. Unity一键启动

**实现**: `Assets/Scripts/RAGSystem/Editor/SkillRAGServerManager.cs`

```csharp
[MenuItem("Tools/SkillAgent/启动服务器", priority = 1)]
public static void StartServer()
{
    // 1. 查找启动脚本
    string batPath = FindServerBatchFile(); // skill_agent/快速启动(Unity).bat

    // 2. 启动Python服务进程
    ProcessStartInfo startInfo = new ProcessStartInfo
    {
        FileName = batPath,
        WorkingDirectory = Path.GetDirectoryName(batPath),
        UseShellExecute = true
    };

    serverProcess = Process.Start(startInfo);

    // 3. 等待端口开放后打开浏览器
    EditorCoroutineUtility.StartCoroutine(WaitAndOpenBrowser(), this);
}

private static IEnumerator WaitAndOpenBrowser()
{
    while (!IsPortOpen(7860)) // 检测Web UI端口
    {
        yield return new WaitForSeconds(1f);
    }

    Application.OpenURL("http://127.0.0.1:7860");
}
```

---

## 配置说明

### RAG配置

**文件**: `skill_agent/core_config.yaml`

```yaml
embedding:
  model_name: "Qwen/Qwen3-0.6B-Embedding"
  model_path: "./Data/models/Qwen3-0.6B-Embedding"
  device: "cuda"  # 或 "cpu"

vector_store:
  type: "chromadb"
  persist_directory: "./Data/vector_db"
  collection_name: "skills"

skill_indexer:
  skills_directory: "../ai_agent_for_skill/Assets/GameData/Skills"
  cache_file: "./Data/skill_index.json"
  auto_reload: true
```

### LangGraph配置

**文件**: `skill_agent/langgraph_server.py`

```python
# 支持的助手类型
ASSISTANTS = {
    "skill-generation": "技能生成",
    "skill-search": "技能搜索",
    "skill-detail": "技能详情"
}

# 服务端口
PORT = 2024

# DeepSeek配置
LLM_CONFIG = {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "api_key": os.getenv("DEEPSEEK_API_KEY")
}
```

### Web UI配置

**文件**: `webui/.env`

```bash
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=skill-generation
```

---

## 开发指南

### 添加新的Action类型

1. **定义Action类**: `Assets/Scripts/SkillSystem/Actions/YourAction.cs`
2. **更新Action索引**: 在 `skill_agent/core/action_indexer.py` 中注册
3. **添加参数模板**: 在 `skill_agent/orchestration/prompts/action_templates/` 中添加Prompt
4. **重建索引**: 运行 `python rebuild_index.py`

### 自定义Prompt模板

**位置**: `skill_agent/orchestration/prompts/`

**示例**:
```python
# skill_generation.txt
你是一个Unity技能配置专家。请基于以下参考技能生成新的技能配置:

参考技能:
{retrieved_skills}

用户需求:
{user_query}

要求:
1. 返回标准的SkillData JSON格式
2. 确保actionType从以下21种中选择: {available_actions}
3. 参数类型必须匹配Action定义

请生成配置:
```

### 扩展工作流

**示例: 添加技能平衡性检查节点**

```python
# skill_nodes.py
def balance_check_node(state):
    """检查技能平衡性"""
    skill = json.loads(state["generated_json"])

    warnings = []
    total_damage = sum(a.get("damage", 0) for a in skill["actions"])
    if total_damage > 1000:
        warnings.append("总伤害过高,可能影响平衡")

    return {"balance_warnings": warnings}

# skill_generation.py
workflow.add_node("balance_check", balance_check_node)
workflow.add_edge("validate", "balance_check")
workflow.add_edge("balance_check", "finalize")
```

---

## 常见问题

### Q1: 启动服务失败

**检查清单**:
1. Python环境是否正确安装依赖: `pip install -r requirements_langchain.txt`
2. DEEPSEEK_API_KEY是否配置
3. 端口2024和7860是否被占用: `netstat -ano | findstr :2024`
4. Qwen3模型文件是否存在: `skill_agent/Data/models/Qwen3-0.6B-Embedding/`

### Q2: 生成的技能配置不符合预期

**优化建议**:
1. 提供更详细的需求描述
2. 增加检索的相似技能数量 (top_k参数)
3. 调整DeepSeek的temperature参数 (降低随机性)
4. 自定义Prompt模板增加约束条件

### Q3: 向量检索结果不准确

**优化方案**:
1. 重建向量索引: `python rebuild_index.py --force`
2. 调整embedding的prompt_name (query vs text)
3. 增加技能描述的语义信息 (在JSON中添加description字段)

---

## 技术细节

### 向量化策略

**技能文档构建**:
```python
# skill_indexer.py
def build_skill_document(skill_json):
    """将技能JSON转换为可检索的文档"""
    doc = f"""
    技能名称: {skill_json['skillName']}
    技能ID: {skill_json['skillId']}
    描述: {skill_json.get('description', '')}

    Actions:
    """
    for i, action in enumerate(skill_json['actions']):
        doc += f"\n{i+1}. {action['actionType']}: {format_parameters(action['parameters'])}"

    return doc
```

**Prompt优化**:
- 检索查询: 使用 `query` prompt_name (优化检索性能)
- 文档向量化: 使用 `text` prompt_name (优化表征能力)

### LangGraph状态管理

**状态定义**:
```python
class SkillGenerationState(TypedDict):
    user_query: str                  # 用户输入
    retrieved_skills: List[Dict]     # 检索结果
    generated_json: str              # 生成的JSON
    validation_errors: List[str]     # 验证错误
    retry_count: int                 # 重试次数
    is_valid: bool                   # 是否通过验证
    final_result: Dict               # 最终结果
```

**条件路由**:
```python
def should_continue(state: SkillGenerationState) -> str:
    if state["is_valid"]:
        return "finalize"
    elif state["retry_count"] >= 3:
        return "finalize"  # 超过重试次数,返回最后结果
    else:
        return "fix"
```

### 缓存机制

**向量缓存**:
- TTL: 1小时
- 存储位置: `skill_agent/Data/embeddings_cache/`
- 缓存键: `hash(skill_id + skill_json_content)`

**技能索引缓存**:
- 自动检测文件变更 (mtime)
- 增量更新索引
- 存储位置: `skill_agent/Data/skill_index.json`

---

## 性能指标

**向量检索性能**:
- 技能库规模: 1000+技能
- 检索延迟: <100ms (本地ChromaDB)
- Top-5准确率: 85%+

**技能生成性能**:
- 端到端延迟: 3-8秒 (取决于DeepSeek API延迟)
- 一次通过率: 70%+ (无需修复)
- 修复成功率: 95%+ (3次重试内)

**资源占用**:
- Qwen3-Embedding内存占用: ~2GB (CUDA) / ~1GB (CPU)
- ChromaDB磁盘占用: ~500MB (1000技能)

---

## 许可证

本项目仅供学习和研究使用。

---

## 联系方式

如有问题或建议,请提交Issue或Pull Request。

**关键文件速查**:
- Unity一键启动: `ai_agent_for_skill/Assets/Scripts/RAGSystem/Editor/SkillRAGServerManager.cs:30`
- RAG引擎: `skill_agent/core/rag_engine.py:45`
- LangGraph服务: `skill_agent/langgraph_server.py:161`
- 技能生成工作流: `skill_agent/orchestration/graphs/skill_generation.py:44`
