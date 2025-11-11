# REQ-06 MCP Tool: get_skill_detail

**状态**: [P0-MVP必需] | **优先级**: 高 | **依赖**: REQ-03, REQ-14, REQ-15

## 背景
- LLM需要按需拉取完整技能JSON或聚焦某个轨道的摘要，避免一次性输出。

## 功能目标
- 输入skill_id，可选择summarize/focus_track。
- 输出完整JSON或摘要、文件指标和复杂度评分。

## 接口契约
```json
{
  "skill_id": "riven-broken-wings-001",
  "summarize": true,
  "focus_track": "Damage Track"
}
```

## 实现步骤
1. 借助扩展索引从存储中提取完整JSON或目标轨道片段。
2. 对summarize=true的情况生成结构化概览（轨道数、Action数、关键参数）。
3. 附加metadata：文件大小、行数、复杂度评分。

## 数据与依赖
- 关联REQ03的ChunkedJsonStore；metadata来源于索引统计。

## 验收标准
- 10K行文件拉取耗时 < 800ms（含摘要生成）。
- focus_track不存在时返回提示并给出可选列表。

## 风险
- 大文件读取阻塞 → 使用流式IO并限制传输大小。

## 交付
- Tool实现、摘要模板、异常用例测试、监控指标（成功率/耗时）。
