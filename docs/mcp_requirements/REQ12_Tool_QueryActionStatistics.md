# REQ-12 MCP Tool: query_action_statistics

**状�?*: [P2-可选] | **优先�?*: �?| **备注**: REQ-03 已有基础能力，可延后

## 背景
- 需要快速获取Action参数分布，以支撑推理解释与对比分析�?

## 功能目标
- 输入action_type/parameter_name/filters，输出统计量、分位点、ASCII分布图�?

## 实现步骤
1. 构建预计算统计表（count/mean/median/std/min/max/percentiles）�?
2. 支持按skill_tags等过滤器筛选样本�?
3. 生成易读的ASCII直方图或箱型图摘要�?

## 数据与依�?
- 读取RAG索引与技能JSON参数；可结合pandas/Numpy处理�?

## 验收标准
- 统计结果与离线校验一致（误差<1e-6）�?
- 滤器未命中时返回提示而不是空指针�?

## 风险
- 样本过少 �?显示“样本不足”提示并附加建议�?

## 交付
- Tool实现、统计缓存、可视化格式示例、单元测试�?
