# Action脚本RAG索引系统

## 概述

为SkillRAG系统添加了Action脚本的向量索引功能，使得AI可以基于自然语言查询推荐合适的Action类型及其参数。

## 系统架构

```
Unity编辑器
    ↓ (Reflection提取元数据)
ActionToJsonExporter.cs
    ↓ (为每个Action导出独立JSON)
Actions/
  ├── DamageAction.json
  ├── MovementAction.json
  └── ...
    ↓ (Python扫描目录)
action_indexer.py
    ↓ (生成向量嵌入)
Action Vector Store (ChromaDB)
    ↓ (RAG检索)
Unity编辑器 / API调用
```

## 功能特性

### 1. Unity端功能
- **Action元数据导出**：通过Reflection自动提取所有Action类的信息
- **完整参数信息**：包括类型、默认值、约束、分组等
- **Odin特性支持**：提取LabelText、BoxGroup、MinValue、Range等特性

### 2. Python端功能
- **向量索引**：将Action元数据转换为向量并存储到ChromaDB
- **语义搜索**：支持自然语言查询Action类型
- **分类过滤**：按Action分类（Damage、Movement等）筛选
- **详细信息查询**：获取Action的完整参数定义

### 3. API端点
- `POST /index_actions` - 构建Action索引
- `POST /search_actions` - 搜索Action类型
- `GET /search_actions?q=xxx` - 快速搜索
- `GET /action/{action_type}` - 获取Action详细信息
- `GET /actions/categories` - 获取所有分类
- `GET /actions/category/{category}` - 获取分类下的Action

## 使用流程

### 步骤1: Unity中导出Action元数据

1. 打开Unity编辑器
2. 菜单栏选择 `Tools -> Skill RAG -> Export Actions to JSON`
3. 点击"导出所有Actions"按钮
4. 确认导出成功，为每个Action生成独立JSON文件：
   ```
   SkillRAG/Data/Actions/
   ├── DamageAction.json
   ├── AttributeScaledDamageAction.json
   ├── MovementAction.json
   └── ...（21个文件）
   ```

### 步骤2: 构建Action向量索引

在SkillRAG/Python目录下执行：

```bash
# 基础索引构建
python build_action_index.py

# 强制重建索引
python build_action_index.py --force

# 仅查看统计信息
python build_action_index.py --stats-only
```

输出示例：
```
======================================================================
Action统计信息
======================================================================
总Action数: 21
平均参数数: 8.3

按分类统计:
  Animation: 1
  Audio: 1
  Camera: 1
  Control: 1
  Damage: 5
  Heal: 2
  ...
======================================================================

✅ 索引构建成功！
索引Action数: 21
耗时: 3.45 秒
```

### 步骤3: 测试Action搜索

运行测试脚本：

```bash
python test_action_search.py
```

测试内容：
- 自然语言搜索Action
- 按分类获取Action列表
- 获取Action详细参数

### 步骤4: 启动RAG Server并使用API

```bash
python server.py
```

访问API文档：http://127.0.0.1:8765/docs

## API使用示例

### 1. 搜索Action

**请求：**
```bash
curl -X POST "http://127.0.0.1:8765/search_actions" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "造成伤害",
    "top_k": 3,
    "return_details": false
  }'
```

**响应：**
```json
{
  "results": [
    {
      "type_name": "DamageAction",
      "display_name": "伤害",
      "category": "Damage",
      "similarity": 0.9234
    },
    {
      "type_name": "AttributeScaledDamageAction",
      "display_name": "属性缩放伤害",
      "category": "Damage",
      "similarity": 0.8876
    }
  ],
  "query": "造成伤害",
  "count": 2,
  "timestamp": "2025-10-30T10:30:00"
}
```

### 2. 获取Action详细信息

**请求：**
```bash
curl "http://127.0.0.1:8765/action/DamageAction"
```

**响应：**
```json
{
  "action": {
    "typeName": "DamageAction",
    "displayName": "伤害",
    "category": "Damage",
    "fullTypeName": "SkillSystem.Actions.DamageAction",
    "parameters": [
      {
        "name": "baseDamage",
        "type": "float",
        "label": "Base Damage",
        "defaultValue": "100",
        "group": "Damage Settings",
        "infoBox": "基础伤害值，技能造成的原始伤害数值",
        "constraints": {
          "minValue": "0"
        }
      }
    ]
  }
}
```

### 3. 按分类搜索

**请求：**
```bash
curl "http://127.0.0.1:8765/search_actions?q=伤害&category=Damage&top_k=5"
```

## 文件结构

```
SkillRAG/
├── Data/
│   ├── Actions/                     # Unity导出的Action元数据目录
│   │   ├── DamageAction.json
│   │   ├── MovementAction.json
│   │   └── ...（每个Action一个文件）
│   ├── action_index.json            # Action索引缓存
│   └── vector_db/
│       └── action_collection/       # Action向量数据库
│
├── Python/
│   ├── action_indexer.py            # Action索引模块（扫描Actions目录）
│   ├── rag_engine.py                # RAG引擎（已扩展）
│   ├── server.py                    # API服务器（已扩展）
│   ├── config.yaml                  # 配置文件（已更新）
│   ├── build_action_index.py        # 索引构建脚本
│   └── test_action_search.py        # 测试脚本
│
ai_agent_for_skill/Assets/Scripts/SkillSystem/Editor/
└── ActionToJsonExporter.cs          # Unity导出工具
```

## 配置说明

在 `config.yaml` 中的Action相关配置（使用相对路径）：

```yaml
action_indexer:
  # Unity导出的Action JSON文件目录（每个Action一个文件）
  # 相对于config.yaml的路径（SkillRAG/Python/config.yaml）
  actions_directory: "../Data/Actions"

  # Action索引缓存路径
  action_index_cache: "../Data/action_index.json"

  # Action向量数据库collection名称（独立于技能collection）
  collection_name: "action_collection"
```

**路径说明：**
- 所有路径都是**相对路径**，相对于`config.yaml`所在目录（`SkillRAG/Python/`）
- `../Data/Actions` → `SkillRAG/Data/Actions/`
- 详细说明请参考：[PATH_CONFIG.md](PATH_CONFIG.md)

**验证路径配置：**
```bash
cd SkillRAG/Python
python check_paths.py  # 检查所有路径是否配置正确
```

## 应用场景

### 1. Action智能推荐
用户输入："我需要一个造成伤害并基于攻击力缩放的Action"
系统返回：`AttributeScaledDamageAction` + 参数建议

### 2. 技能设计助手
在技能编辑器中集成搜索功能：
- 输入自然语言描述
- 系统推荐合适的Action类型
- 自动填充参数默认值

### 3. 文档生成
基于Action元数据自动生成技能系统文档

## 注意事项

1. **Action更新流程**：
   - 修改Action脚本后，需要重新在Unity中导出
   - 导出会生成/更新对应的JSON文件
   - 然后运行 `python build_action_index.py --force` 重建索引

2. **文件管理**：
   - 每个Action对应一个独立的JSON文件
   - 删除Action类后，记得手动删除对应的JSON文件
   - JSON文件名与Action类名一致

3. **性能优化**：
   - Action数量较少（约20-30个），索引速度很快
   - 向量存储在独立的collection中，不影响技能索引
   - 单文件结构便于版本控制和增量更新

4. **扩展性**：
   - 支持添加新的Action类型，自动识别
   - 支持嵌套结构和复杂参数类型
   - 单文件格式更易于手动编辑和维护

## 故障排除

### 问题1: 找不到Actions目录或目录为空
**解决**：确保在Unity中运行导出工具并检查`SkillRAG/Data/Actions/`目录

### 问题2: 索引构建失败
**解决**：检查Python环境和依赖，确保Qwen3模型已下载

### 问题3: 搜索结果不准确
**解决**：
- 调整 `config.yaml` 中的 `similarity_threshold`
- 确保Action的searchText构建合理
- 考虑添加更多描述信息

## 未来扩展

- [ ] 在Unity技能编辑器中集成Action搜索UI
- [ ] 基于技能模板自动生成Action配置
- [ ] 支持Action参数智能推荐
- [ ] 添加Action使用示例提取

## 相关文档

- [SkillRAG系统文档](README.md)
- [Action脚本规范](../ai_agent_for_skill/.claude/docs/ACTION_CHECKLIST.md)
