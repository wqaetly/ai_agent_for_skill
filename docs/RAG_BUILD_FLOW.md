# RAG 构建流程文档

本文档描述从 Unity 导出 JSON 到最终 RAG 存储的完整流程。

---

## 一、整体架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Unity 端                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. SkillData (技能数据)          2. Action 定义 (脚本元数据)                │
│     ↓ Odin Serializer                ↓ 反射导出                              │
│  Assets/Skills/*.json             Data/Actions/*.json                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Python RAG 服务端                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  3. Odin JSON 解析器              4. 索引器                                  │
│     odin_json_parser.py              skill_indexer.py / action_indexer.py   │
│                                       ↓                                      │
│  5. 嵌入生成器                    6. 向量数据库                              │
│     embeddings.py (Qwen3)            vector_store_lancedb.py (LanceDB)      │
│                                       ↓                                      │
│  7. RAG 引擎                                                                 │
│     rag_engine.py                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、数据流详解

### 2.1 Unity 端数据导出

#### 2.1.1 技能数据导出 (SkillData)

**文件位置**: `ai_agent_for_skill/Assets/Skills/*.json`

**导出方式**: 使用 Odin Serializer 序列化

```csharp
// SkillDataSerializer.cs
public static string SerializeToJson(SkillData skillData)
{
    byte[] bytes = SerializationUtility.SerializeValue(skillData, DataFormat.JSON);
    return System.Text.Encoding.UTF8.GetString(bytes);
}
```

**Odin JSON 特殊格式**:
- 类型引用: `"$type": "索引|完整类型名, 程序集"`
- 对象引用: `"$id"` / `"$iref:N"`
- 集合格式: `$rlength` + `$rcontent` (引用类型) / `$plength` + `$pcontent` (基元类型)
- Unity 类型裸值: `{"$type": "Vector3...", 1.5, 2.0, 3.5}` (无键名)

**技能 JSON 结构示例**:
```json
{
    "$id": 0,
    "$type": "0|SkillSystem.Data.SkillData, Assembly-CSharp",
    "skillName": "火球术",
    "skillDescription": "释放火球攻击敌人",
    "skillId": "fireball-001",
    "totalDuration": 120,
    "frameRate": 30,
    "tracks": {
        "$rlength": 2,
        "$rcontent": [
            {
                "trackName": "Animation",
                "enabled": true,
                "actions": { ... }
            }
        ]
    }
}
```

#### 2.1.2 Action 定义导出

**文件位置**: `skill_agent/Data/Actions/*.json`

**导出方式**: Unity Editor 脚本通过反射提取 Action 类的元数据

**Action 定义 JSON 结构**:
```json
{
    "version": "1.0",
    "exportTime": "2025-11-10T19:17:07",
    "action": {
        "typeName": "DamageAction",
        "fullTypeName": "SkillSystem.Actions.DamageAction",
        "displayName": "属性伤害",
        "category": "Damage",
        "description": "属性缩放伤害Action...",
        "searchText": "属性伤害\n属性缩放伤害Action...",
        "parameters": [
            {
                "name": "baseDamage",
                "type": "float",
                "defaultValue": "100",
                "label": "Base Damage",
                "group": "Damage Settings",
                "constraints": { "minValue": "0" }
            }
        ]
    }
}
```

---

### 2.2 Python 端数据处理

#### 2.2.1 Odin JSON 解析

**模块**: `core/odin_json_parser.py`

**核心类**: `OdinJsonParser`

**主要功能**:
1. 解析 Odin 非标准 JSON 格式（裸值数组、类型引用等）
2. 处理 Unity 特殊类型（Vector3, Color, Quaternion 等）
3. 解析对象引用 (`$iref:N`)
4. 展开集合结构 (`$rcontent` → Python List)

```python
# 使用示例
parser = OdinJsonParser()
skill_data = parser.parse_file("Assets/Skills/Fireball.json")
```

**解析流程**:
```
原始 Odin JSON
    ↓ parse_odin_json_raw()  # 预处理非标准格式
    ↓ _collect_types()        # 收集类型定义到缓存
    ↓ _resolve_odin_structure() # 递归解析特殊结构
标准 Python Dict
```

#### 2.2.2 技能索引器

**模块**: `core/skill_indexer.py`

**核心类**: `SkillIndexer`

**主要功能**:
1. 扫描技能目录 (`Assets/Skills/*.json`)
2. 解析技能文件（调用 OdinJsonParser）
3. 构建搜索文本（用于向量嵌入）
4. 缓存索引信息（避免重复解析）

```python
# 配置
skill_indexer:
  skills_directory: "../ai_agent_for_skill/Assets/Skills"
  index_cache: "Data/skill_index.json"
  index_action_details: true
```

**搜索文本构建**:
```python
def build_search_text(self, skill_data):
    text_parts = []
    text_parts.append(f"技能名称：{skill_data['skillName']}")
    text_parts.append(f"技能描述：{skill_data['skillDescription']}")
    # 提取 Action 类型和参数信息
    for track in skill_data['tracks']:
        for action in track['actions']:
            action_types.append(action['type'])
    text_parts.append(f"包含动作：{', '.join(action_types)}")
    return "\n".join(text_parts)
```

#### 2.2.3 Action 索引器

**模块**: `core/action_indexer.py`

**核心类**: `ActionIndexer`

**主要功能**:
1. 扫描 Action 定义目录 (`Data/Actions/*.json`)
2. 构建 Action 搜索文本
3. 提取 Action 元数据（类型、分类、参数等）

```python
# 配置
action_indexer:
  actions_directory: "Data/Actions"
  action_index_cache: "Data/action_index.json"
  collection_name: "action_collection"
```

---

### 2.3 向量化与存储

#### 2.3.1 嵌入生成器

**模块**: `core/embeddings.py`

**核心类**: `EmbeddingGenerator`

**模型**: Qwen3-Embedding-0.6B (本地部署)

**配置**:
```yaml
embedding:
  model_name: "Data/models/Qwen3-Embedding-0.6B"
  device: "cpu"  # 或 "cuda"
  batch_size: 32
  max_length: 8192
```

**编码流程**:
```python
# 文档编码（不需要 prompt）
doc_embeddings = generator.encode(documents)

# 查询编码（使用 prompt_name="query" 优化检索性能）
query_embedding = generator.encode(query, prompt_name="query")
```

**向量维度**: 768 维

#### 2.3.2 向量数据库

**模块**: `core/vector_store_lancedb.py`

**核心类**: `LanceDBVectorStore`

**数据库**: LanceDB (嵌入式，无需 Docker)

**配置**:
```yaml
vector_store:
  type: "lancedb"
  lancedb_path: "Data/lancedb"
  collection_name: "skill_collection"
  distance_metric: "cosine"
```

**存储结构**:
```
Data/lancedb/
├── skill_collection/     # 技能向量表
│   └── *.lance           # Lance 格式数据文件
└── action_collection/    # Action 向量表
    └── *.lance
```

**表结构**:
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 文档唯一ID |
| document | string | 搜索文本 |
| vector | float[768] | 嵌入向量 |
| metadata | string (JSON) | 元数据 |

---

### 2.4 RAG 引擎

**模块**: `core/rag_engine.py`

**核心类**: `RAGEngine`

**整合所有组件**:
```python
class RAGEngine:
    def __init__(self, config):
        self.embedding_generator = EmbeddingGenerator(config['embedding'])
        self.vector_store = create_vector_store(config['vector_store'])
        self.skill_indexer = SkillIndexer(config['skill_indexer'])
        self.action_indexer = ActionIndexer(config['action_indexer'])
        self.action_vector_store = create_vector_store(action_config)
```

---

## 三、索引构建流程

### 3.1 技能索引构建

```python
def index_skills(self, force_rebuild=False):
    # 1. 扫描并解析技能文件
    skills = self.skill_indexer.index_all_skills(force_rebuild)
    
    # 2. 准备数据
    documents = [skill['search_text'] for skill in skills]
    metadatas = [{
        'skill_id': skill['skillId'],
        'skill_name': skill['skillName'],
        'action_type_list': json.dumps(action_types),
        ...
    } for skill in skills]
    ids = [md5(skill['file_path']) for skill in skills]
    
    # 3. 生成嵌入向量
    embeddings = self.embedding_generator.encode_batch(documents)
    
    # 4. 存储到向量数据库
    self.vector_store.add_documents(documents, embeddings, metadatas, ids)
```

### 3.2 Action 索引构建

```python
def index_actions(self, force_rebuild=False):
    # 1. 准备 Action 数据
    prepared_actions = self.action_indexer.prepare_actions_for_indexing()
    
    # 2. 提取数据
    documents = [action['search_text'] for action in prepared_actions]
    metadatas = [action['metadata'] for action in prepared_actions]
    ids = [action['id'] for action in prepared_actions]
    
    # 3. 生成嵌入向量
    embeddings = self.embedding_generator.encode_batch(documents)
    
    # 4. 存储到 Action 向量数据库
    self.action_vector_store.add_documents(documents, embeddings, metadatas, ids)
```

### 3.3 手动重建索引

**方式一**: 使用脚本
```bash
cd skill_agent/Python
python rebuild_index.py
```

**方式二**: 通过 API
```python
# POST /api/rag/rebuild
result = rag_engine.index_skills(force_rebuild=True)
result = rag_engine.index_actions(force_rebuild=True)
```

**方式三**: 通过 WebUI
- 访问 `http://localhost:3000/rag`
- 点击 "重建索引" 按钮

---

## 四、数据目录结构

```
skill_agent/
├── Data/
│   ├── Actions/                    # Unity 导出的 Action 定义
│   │   ├── DamageAction.json
│   │   ├── HealAction.json
│   │   └── ...
│   ├── lancedb/                    # LanceDB 向量数据库
│   │   ├── skill_collection/
│   │   └── action_collection/
│   ├── models/                     # 本地嵌入模型
│   │   └── Qwen3-Embedding-0.6B/
│   ├── skill_index.json            # 技能索引缓存
│   └── fine_grained_index.json     # 细粒度索引缓存
│
ai_agent_for_skill/
└── Assets/
    └── Skills/                     # Unity 技能 JSON 文件
        ├── Fireball.json
        └── ...
```

---

## 五、配置文件

**主配置**: `skill_agent/core_config.yaml`

```yaml
# 嵌入模型
embedding:
  model_name: "Data/models/Qwen3-Embedding-0.6B"
  device: "cpu"
  batch_size: 32

# 向量数据库
vector_store:
  type: "lancedb"
  lancedb_path: "Data/lancedb"
  collection_name: "skill_collection"
  distance_metric: "cosine"

# 技能索引
skill_indexer:
  skills_directory: "../ai_agent_for_skill/Assets/Skills"
  index_cache: "Data/skill_index.json"

# Action 索引
action_indexer:
  actions_directory: "Data/Actions"
  collection_name: "action_collection"

# RAG 检索
rag:
  top_k: 5
  similarity_threshold: 0.1
  cache_enabled: true
  cache_ttl: 3600
```

---

## 六、流程图总结

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         完整 RAG 构建流程                                 │
└──────────────────────────────────────────────────────────────────────────┘

[Unity Editor]
     │
     ├─── SkillData ──→ Odin Serializer ──→ Assets/Skills/*.json
     │                                              │
     └─── Action 脚本 ──→ 反射导出 ──→ Data/Actions/*.json
                                                    │
                                                    ↓
[Python RAG 服务] ←─────────────────────────────────┘
     │
     ├─── OdinJsonParser ──→ 解析 Odin JSON 格式
     │         │
     │         ↓
     ├─── SkillIndexer ──→ 构建技能搜索文本 + 元数据
     │         │
     ├─── ActionIndexer ──→ 构建 Action 搜索文本 + 元数据
     │         │
     │         ↓
     ├─── EmbeddingGenerator (Qwen3) ──→ 生成 768 维向量
     │         │
     │         ↓
     └─── LanceDBVectorStore ──→ 存储向量 + 元数据
                  │
                  ↓
           [RAG 检索就绪]
                  │
                  ├─── search_skills(query) ──→ 语义搜索技能
                  ├─── search_actions(query) ──→ 语义搜索 Action
                  └─── recommend_actions(context) ──→ Action 推荐
```

---

## 七、常见问题

### Q1: 如何添加新的 Action 类型？

1. 在 Unity 中创建新的 Action 脚本
2. 使用 Action 导出工具导出到 `Data/Actions/`
3. 调用 `rag_engine.index_actions(force_rebuild=True)` 重建索引

### Q2: 技能文件修改后如何更新索引？

- **自动更新**: 配置 `watch_enabled: true` 后，文件变化会自动触发增量更新
- **手动更新**: 调用 `rag_engine.update_skill(file_path)` 或重建全部索引

### Q3: 如何调整检索精度？

修改 `core_config.yaml`:
```yaml
rag:
  top_k: 10              # 增加返回结果数
  similarity_threshold: 0.3  # 降低阈值提高召回率
```

### Q4: 向量数据库损坏如何恢复？

1. 删除 `Data/lancedb/` 目录
2. 重新运行索引构建: `python rebuild_index.py`

---

*文档版本: 1.0*
*最后更新: 2026-01-13*
