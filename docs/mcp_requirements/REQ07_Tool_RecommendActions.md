# REQ-07 MCP Tool: recommend_actions_intelligent

## 背景
- 需要根据技能上下文推荐合适的Action类型及组合。

## 功能目标
- 输入技能描述、已有Action列表、期望效果与约束。
- 返回Action类型、置信度、理由、典型帧范围、可兼容Action。

## 实现步骤
1. 解析skill_context并调用REQ01中的语义/约束模块。
2. 结合项目优先级和Action使用统计生成排序结果。
3. 附加reason/compatible_actions，支撑Tool9的解释链。

## 接口示例
```json
{
  "skill_context": {"description": "火焰范围爆炸", "existing_actions": []},
  "constraints": {"max_actions": 5}
}
```

## 数据与依赖
- 依赖RAG检索、Action频率统计、组合规则表。

## 验收标准
- 推荐列表至少包含1个可行组合并附带理由。
- 命中不可用Action时能返回约束警告。

## 风险
- 上下文缺失 → 采用默认模板并提示用户补充。

## 交付
- Tool实现、打分策略文档、回测报告与Prompts样例。
