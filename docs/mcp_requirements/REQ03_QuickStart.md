# REQ-03 快速开始指�?
## 5分钟快速体�?
### 步骤1：安装依�?
```bash
cd skill_agent/Python
pip install ijson
```

### 步骤2：构建细粒度索引

```python
# 运行索引构建
python -c "from fine_grained_indexer import build_fine_grained_index; print(build_fine_grained_index(force_rebuild=True))"
```

**预期输出**�?```
{
  'total_files': 9,
  'indexed_files': 9,
  'total_actions': 120,
  'skipped_files': 0,
  'errors': []
}
```

### 步骤3：执行结构化查询

```python
from structured_query_engine import query_skills

# 查询baseDamage > 200的DamageAction
result = query_skills("DamageAction where baseDamage > 200")

print(f"找到 {result['total_matches']} 个匹配Action")
print(f"查询耗时 {result['query_time_ms']}ms")

# 显示结果
for action in result['results'][:3]:
    print(f"- {action['skill_name']}: {action['summary']}")
```

### 步骤4：运行完整测�?
```bash
python test_structured_query.py
```

---

## 常用查询示例

### 1. 按Action类型查询

```python
# 查询所有DamageAction
query_skills("DamageAction")

# 查询所有MovementAction
query_skills("MovementAction")
```

### 2. 数值比较查�?
```python
# 伤害 > 200
query_skills("DamageAction where baseDamage > 200")

# 移动速度 < 10
query_skills("MovementAction where moveSpeed < 10")

# 伤害�?00-300之间
query_skills("baseDamage between 100 and 300")
```

### 3. 字符串查�?
```python
# 动画名包�?Attack"
query_skills("animationClipName contains 'Attack'")

# 伤害类型为魔�?query_skills("DamageAction where damageType = 'Magical'")
```

### 4. 组合条件查询

```python
# 魔法伤害且伤�?150
query_skills("DamageAction where damageType = 'Magical' and baseDamage > 150")

# 范围伤害且范�?3�?query_skills("DamageAction where damageRadius > 3 and baseDamage > 100")
```

---

## 统计分析示例

### 1. 全局统计

```python
from structured_query_engine import StructuredQueryEngine

engine = StructuredQueryEngine()

# 按Action类型统计
stats = engine.get_statistics(group_by="action_type")

print(f"总Action�? {stats['total_actions']}")

for action_type, data in stats['groups'].items():
    print(f"\n{action_type}:")
    print(f"  数量: {data['count']}")

    # 显示参数统计
    if 'avg_baseDamage' in data:
        print(f"  baseDamage: min={data['min_baseDamage']}, avg={data['avg_baseDamage']}, max={data['max_baseDamage']}")
```

### 2. 过滤统计

```python
# 只统计DamageAction的参数分�?stats = engine.get_statistics(
    query_str="DamageAction",
    group_by="action_type"
)
```

---

## 获取Action详细信息

```python
from structured_query_engine import StructuredQueryEngine

engine = StructuredQueryEngine()

# 先查询找到感兴趣的Action
result = engine.query("DamageAction where baseDamage > 200", limit=1)

if result['results']:
    action = result['results'][0]

    # 获取完整详细信息
    detail = engine.get_action_detail(
        skill_file=action['skill_file'],
        json_path=action['json_path']
    )

    print("完整Action数据:")
    print(detail['data'])

    print("\n上下文信�?")
    print(detail['context'])

    print(f"\n所在行�? {action['line_number']}")
```

---

## 缓存管理

```python
from structured_query_engine import StructuredQueryEngine

engine = StructuredQueryEngine()

# 查看缓存统计
stats = engine.get_cache_stats()
print(f"缓存命中�? {stats['query_cache']['hit_rate']:.2%}")

# 清空缓存
engine.clear_cache()

# 重建索引
rebuild_stats = engine.rebuild_index(force=True)
print(f"重建索引: {rebuild_stats['total_actions']} 个Action")
```

---

## MCP集成（可选）

### 1. 安装MCP�?
```bash
pip install mcp
```

### 2. 启动MCP Server

```bash
python mcp_server_structured_query.py
```

### 3. 在Claude Desktop中配�?
编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "skill-structured-query": {
      "command": "python",
      "args": [
        "E:/Study/wqaetly/ai_agent_for_skill/skill_agent/Python/mcp_server_structured_query.py"
      ]
    }
  }
}
```

### 4. 使用MCP Tools

在Claude Desktop中：

```
使用 query_skills_structured 工具查询所有伤害大�?00的DamageAction
```

Claude会自动调用MCP工具并返回结果�?
---

## Python API完整示例

```python
from structured_query_engine import StructuredQueryEngine

# 创建引擎实例
engine = StructuredQueryEngine(
    skills_dir="../../ai_agent_for_skill/Assets/Skills",
    cache_size=100
)

# 1. 执行查询
result = engine.query(
    query_str="DamageAction where baseDamage > 200 and damageType = 'Magical'",
    limit=50,
    include_context=True,
    use_cache=True
)

print(f"查询结果: {result['total_matches']} 个匹�?)
print(f"查询耗时: {result['query_time_ms']}ms")
print(f"缓存命中: {result['cache_hit']}")

# 2. 遍历结果
for action in result['results']:
    print(f"\n技�? {action['skill_name']}")
    print(f"轨道: {action['track_name']}")
    print(f"类型: {action['action_type']}")
    print(f"帧位�? {action['frame']}")
    print(f"参数: {action['parameters']}")
    print(f"摘要: {action['summary']}")
    print(f"行号: {action['line_number']}")

# 3. 统计分析
stats = engine.get_statistics(
    query_str="DamageAction",
    group_by="action_type"
)

print(f"\nDamageAction统计:")
damage_stats = stats['groups'].get('DamageAction', {})
print(f"数量: {damage_stats.get('count', 0)}")
print(f"平均伤害: {damage_stats.get('avg_baseDamage', 0)}")

# 4. 获取详细信息
if result['results']:
    first_action = result['results'][0]
    detail = engine.get_action_detail(
        skill_file=first_action['skill_file'],
        json_path=first_action['json_path']
    )
    print(f"\n详细数据大小: {detail['size_bytes']} bytes")

# 5. 缓存管理
cache_stats = engine.get_cache_stats()
print(f"\n缓存命中�? {cache_stats['query_cache']['hit_rate']:.2%}")
```

---

## 性能测试

```python
import time
from structured_query_engine import StructuredQueryEngine

engine = StructuredQueryEngine()

# 测试查询性能
queries = [
    "DamageAction",
    "DamageAction where baseDamage > 100",
    "baseDamage between 50 and 500",
]

for query in queries:
    start = time.time()
    result = engine.query(query, use_cache=False)
    elapsed = (time.time() - start) * 1000

    print(f"{query}")
    print(f"  匹配: {result['total_matches']}")
    print(f"  耗时: {elapsed:.2f}ms")
    print()
```

---

## 故障排查

### 问题1：索引文件不存在

**错误**：`FileNotFoundError: fine_grained_index.json not found`

**解决**�?```python
from fine_grained_indexer import build_fine_grained_index
build_fine_grained_index(force_rebuild=True)
```

### 问题2：技能目录路径错�?
**错误**：`FileNotFoundError: 技能目录不存在`

**解决**�?```python
# 使用绝对路径
engine = StructuredQueryEngine(
    skills_dir="E:/Study/wqaetly/ai_agent_for_skill/ai_agent_for_skill/Assets/Skills"
)
```

### 问题3：查询语法错�?
**错误**：查询返�?结果

**解决**：检查查询语�?```python
# 正确
"DamageAction where baseDamage > 200"

# 错误（运算符前后需要空格）
"DamageAction where baseDamage>200"

# 错误（字符串需要引号）
"DamageAction where damageType = Magical"  # �?"DamageAction where damageType = 'Magical'"  # �?```

### 问题4：查询性能�?
**解决**�?1. 启用缓存（默认已启用�?2. 减少返回结果数量（设置limit�?3. 清理过期缓存

```python
# 限制结果数量
result = engine.query("DamageAction", limit=10)

# 清理缓存
engine.clear_cache()
```

---

## 支持的参数类�?
| 类型 | 示例 | 查询语法 |
|------|------|---------|
| 数�?| `baseDamage: 150` | `baseDamage > 100` |
| 字符�?| `damageType: "Magical"` | `damageType = 'Magical'` |
| 布尔 | `enabled: true` | `enabled = true` |
| 区间 | `baseDamage: 100-300` | `baseDamage between 100 and 300` |
| 包含 | `animationClipName: "Attack_01"` | `animationClipName contains 'Attack'` |

---

## 最佳实�?
### 1. 索引管理
- 技能文件修改后自动检测更新（基于MD5�?- 定期重建索引（`force=True`）以确保一致�?- 监控索引大小和构建时�?
### 2. 查询优化
- 优先使用具体的Action类型过滤
- 合理设置limit避免返回大量结果
- 启用缓存（默认）以提升性能

### 3. 性能监控
- 定期检查缓存命中率�? 70%为佳�?- 监控查询延迟�? 500ms�?- 大型查询使用异步执行

---

## 下一步学�?
1. [REQ-03实现文档](REQ03_Implementation.md) - 深入了解架构设计
2. [MCP开发计划](../MCP_Development_Plan.md) - 完整MCP集成方案
3. [测试脚本](../../skill_agent/Python/test_structured_query.py) - 查看更多示例

---

## 常见问题

**Q: 如何查询所有技能的统计信息�?*
```python
stats = engine.get_statistics(group_by="action_type")
```

**Q: 如何查找特定技能文件中的所有Action�?*
```python
# 使用文件名过滤（需在结果中过滤�?result = engine.query("DamageAction", limit=1000)
flame_actions = [a for a in result['results'] if a['skill_file'] == 'FlameShockwave.json']
```

**Q: 支持OR逻辑吗？**
```
当前只支持AND逻辑。OR查询可以通过多次查询合并结果实现�?```

**Q: 如何导出查询结果为JSON�?*
```python
import json

result = engine.query("DamageAction where baseDamage > 200")

with open("query_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```

---

**完成�?* 你现在已经掌握了REQ-03的基本使用方法�?