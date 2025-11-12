# skill_agent API文档

skill_agent Python服务提供的RESTful API接口文档。

## 基础信息

- **Base URL**: `http://127.0.0.1:8765`
- **Content-Type**: `application/json`
- **字符编码**: UTF-8

---

## API端点列表

### 1. 健康检查

**端点**: `GET /health`

**描述**: 检查服务器是否正常运行。

**请求**: 无参数

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-29T10:30:00.123456"
}
```

**状态码**:
- `200`: 服务正常
- `503`: 服务不可用

---

### 2. 搜索技能

**端点**: `POST /search` 或`GET /search`

**描述**: 根据查询文本搜索相似的技能。

#### POST方法

**请求体**:
```json
{
  "query": "火焰伤害技能",
  "top_k": 5,
  "filters": {
    "skill_type": "damage"
  },
  "return_details": true
}
```

**参数说明**:
- `query` (string, 必需): 搜索查询文本
- `top_k` (int, 可选): 返回结果数量，默认5
- `filters` (object, 可选): 元数据过滤条件
- `return_details` (bool, 可选): 是否返回详细信息，默认false

#### GET方法

**查询参数**:
- `q` (string, 必需): 搜索查询文本
- `top_k` (int, 可选): 返回结果数量
- `details` (bool, 可选): 是否返回详细信息

**示例**:
```
GET /search?q=火焰伤害&top_k=3&details=true
```

**响应示例**:
```json
{
  "results": [
    {
      "skill_id": "flame-shockwave-001",
      "skill_name": "Flame Shockwave",
      "file_name": "FlameShockwave.json",
      "similarity": 0.8523,
      "distance": 0.1477,
      "file_path": "E:/Study/.../FlameShockwave.json",
      "total_duration": 150,
      "frame_rate": 30,
      "num_tracks": 6,
      "num_actions": 12,
      "last_modified": "2025-01-28T15:30:00",
      "search_text_preview": "技能名称：Flame Shockwave..."
    }
  ],
  "query": "火焰伤害技能",
  "count": 1,
  "timestamp": "2025-01-29T10:35:00.123456"
}
```

**状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器错误

---

### 3. 获取技能详情

**端点**: `GET /skill/{skill_id}`

**描述**: 根据skill_id获取技能的完整数据。

**路径参数**:
- `skill_id` (string): 技能ID

**响应示例**:
```json
{
  "skill": {
    "skillName": "Flame Shockwave",
    "skillDescription": "释放一道火焰冲击波...",
    "skillId": "flame-shockwave-001",
    "totalDuration": 150,
    "frameRate": 30,
    "tracks": [
      {
        "trackName": "伤害轨道",
        "enabled": true,
        "actions": [
          {
            "type": "DamageAction",
            "frame": 10,
            "duration": 30,
            "enabled": true,
            "parameters": {
              "baseDamage": 100,
              "damageType": "Magical"
            }
          }
        ]
      }
    ],
    "file_path": "E:/Study/.../FlameShockwave.json",
    "file_name": "FlameShockwave.json"
  },
  "timestamp": "2025-01-29T10:40:00.123456"
}
```

**状态码**:
- `200`: 成功
- `404`: 技能未找到
- `500`: 服务器错误

---

### 4. 推荐Action

**端点**: `POST /recommend`

**描述**: 根据上下文描述推荐合适的Action类型及参数示例。

**请求体**:
```json
{
  "context": "造成伤害并击退敌人",
  "top_k": 3
}
```

**参数说明**:
- `context` (string, 必需): 上下文描述
- `top_k` (int, 可选): 推荐数量，默认3

**响应示例**:
```json
{
  "recommendations": [
    {
      "action_type": "DamageAction",
      "frequency": 15,
      "examples": [
        {
          "skill_name": "Flame Shockwave",
          "parameters": {
            "baseDamage": 100,
            "damageType": "Magical",
            "damageRadius": 5.0
          }
        },
        {
          "skill_name": "Sion Soul Furnace",
          "parameters": {
            "baseDamage": 80,
            "damageType": "Physical"
          }
        }
      ]
    },
    {
      "action_type": "MovementAction",
      "frequency": 8,
      "examples": [
        {
          "skill_name": "Riven Broken Wings",
          "parameters": {
            "movementType": "Linear",
            "movementSpeed": 10.0
          }
        }
      ]
    }
  ],
  "context": "造成伤害并击退敌人",
  "count": 2
}
```

**状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器错误

---

### 5. 触发索引

**端点**: `POST /index`

**描述**: 手动触发技能索引，扫描技能文件并更新向量数据库。

**请求体**:
```json
{
  "force_rebuild": false
}
```

**参数说明**:
- `force_rebuild` (bool, 可选): 是否强制重建索引，默认false

**响应示例**:
```json
{
  "status": "success",
  "count": 8,
  "elapsed_time": 12.345,
  "message": null
}
```

**字段说明**:
- `status` (string): 索引状态（success/error/no_skills）
- `count` (int): 索引的技能数量
- `elapsed_time` (float): 耗时（秒）
- `message` (string): 额外信息（仅在出错时）

**状态码**:
- `200`: 成功
- `500`: 服务器错误

---

### 6. 获取统计信息

**端点**: `GET /stats`

**描述**: 获取RAG引擎的运行统计信息。

**请求**: 无参数

**响应示例**:
```json
{
  "statistics": {
    "engine_stats": {
      "total_queries": 156,
      "cache_hits": 42,
      "total_indexed": 8,
      "last_index_time": "2025-01-29T09:00:00.123456"
    },
    "vector_store": {
      "collection_name": "skill_collection",
      "total_documents": 8,
      "distance_metric": "cosine",
      "embedding_dimension": 768,
      "persist_directory": "../Data/vector_db"
    },
    "embedding_cache": {
      "size": 234,
      "max_size": 1000,
      "hit_rate": 0.65
    },
    "query_cache_size": 12
  },
  "timestamp": "2025-01-29T10:50:00.123456"
}
```

**状态码**:
- `200`: 成功
- `503`: 服务未初始化

---

### 7. 清空缓存

**端点**: `POST /clear-cache`

**描述**: 清空所有缓存（嵌入缓存和查询缓存）。

**请求**: 无参数

**响应示例**:
```json
{
  "status": "success",
  "message": "All caches cleared",
  "timestamp": "2025-01-29T10:55:00.123456"
}
```

**状态码**:
- `200`: 成功
- `500`: 服务器错误

---

### 8. 服务信息

**端点**: `GET /`

**描述**: 获取服务基本信息。

**请求**: 无参数

**响应示例**:
```json
{
  "service": "skill_agent API",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2025-01-29T11:00:00.123456"
}
```

---

## 错误响应格式

所有错误响应遵循FastAPI标准格式：

```json
{
  "detail": "错误详细信息"
}
```

### 常见错误码
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源未找到
- `500 Internal Server Error`: 服务器内部错误
- `503 Service Unavailable`: 服务不可用

---

## 使用示例

### Python示例

```python
import requests

# 基础URL
BASE_URL = "http://127.0.0.1:8765"

# 1. 搜索技能
response = requests.get(
    f"{BASE_URL}/search",
    params={
        "q": "火焰伤害",
        "top_k": 3,
        "details": True
    }
)
results = response.json()
print(f"找到 {results['count']} 个技能")

# 2. 推荐Action
response = requests.post(
    f"{BASE_URL}/recommend",
    json={
        "context": "造成伤害并击退敌人",
        "top_k": 3
    }
)
recommendations = response.json()
for rec in recommendations['recommendations']:
    print(f"推荐: {rec['action_type']}")

# 3. 触发索引
response = requests.post(
    f"{BASE_URL}/index",
    json={"force_rebuild": False}
)
print(f"索引完成: {response.json()['count']} 个技能")
```

### C# Unity示例

参见Unity客户端代码：`RAGClient.cs`

### cURL示例

```bash
# 健康检查
curl http://127.0.0.1:8765/health

# 搜索技能
curl "http://127.0.0.1:8765/search?q=火焰&top_k=3"

# 推荐Action
curl -X POST http://127.0.0.1:8765/recommend \
  -H "Content-Type: application/json" \
  -d '{"context":"造成伤害","top_k":3}'

# 触发索引
curl -X POST http://127.0.0.1:8765/index \
  -H "Content-Type: application/json" \
  -d '{"force_rebuild":false}'
```

---

## 在线API文档

启动服务器后，访问以下URL查看交互式API文档：

- **Swagger UI**: `http://127.0.0.1:8765/docs`
- **ReDoc**: `http://127.0.0.1:8765/redoc`

---

## 性能建议

### 查询优化
1. **使用缓存**: 相同查询会自动缓存1小时
2. **限制top_k**: 只请求需要的结果数量
3. **避免频繁重建索引**: 使用文件监听自动更新

### 并发处理
- 服务器默认使用uvicorn，支持异步处理
- 建议在Unity中使用单例模式管理RAGClient
- 避免同时发起大量请求

### 索引策略
- **首次启动**: 会自动索引所有技能
- **文件变化**: 自动增量更新（如启用文件监听）
- **定期重建**: 建议每周重建一次索引

---

## 版本历史

- **v1.0.0** (2025-01-29): 初始版本
  - 技能搜索API
  - Action推荐API
  - 索引管理API
  - 统计与缓存管理
