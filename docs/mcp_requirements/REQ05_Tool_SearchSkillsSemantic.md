# REQ-05 MCP Tool: search_skills_semantic

**状�?*: [P0-MVP必需] | **优先�?*: �?| **依赖**: REQ-14, REQ-15

## 背景
- 需要基于自然语言快速定位技能，并附带统计信息为后续推理提供上下文�?

## 功能目标
- 支持query/top_k/filters过滤器，返回技能摘要、相似度与Action统计�?
- 提供资源URI以便客户端进一步调用Tool2拉取详情�?

## 接口契约
```json
{
  "query": "string",
  "top_k": 5,
  "filters": {
    "min_actions": 3,
    "action_types": ["DamageAction"]
  }
}
```
返回字段：skill_id、skill_name、file_path、similarity、summary、action_counts�?

## 实现步骤
1. 在RAG层支持filters映射（action_counts筛选等），并暴露分页能力�?
2. 对搜索结果补充summary（来自索引摘要或LLM概述）与统计信息�?
3. 输出MCP资源引用（skill://<id>），供其他工具链使用�?

## 数据与依�?
- 基于Chroma向量�?+ 技能索引统计表�?

## 验收标准
- 搜索延迟 < 300ms@top_k=5�?
- filters为空时默认返回多样化技能；filters非法时提供明确错误�?

## 风险
- 统计字段未及时更�?�?加索引重建任务并写入版本号�?

## 交付
- Tool定义、Pydantic schema、单元测试与监控埋点�?
