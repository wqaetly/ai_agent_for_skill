# REQ-21 任务3.3 统计分析工具

**状�?*: [P2-可选] | **优先�?*: �?| **备注**: REQ-03 已有基础能力

## 工作范围
- 实现query_action_statistics工具所需的统计计算、缓存与可视化�?

## 实施步骤
1. 从技能数据库抽取参数样本，构建DataFrame�?
2. 计算count/mean/median/std/min/max/percentiles并缓存�?
3. 生成ASCII分布图，支持多个bin配置�?
4. 与Tool12 API对接，处理过滤器逻辑�?

## 依赖
- pandas/numpy、技能索引、缓存层（可选redis）�?

## 验收标准
- 统计值通过离线脚本验证；缓存命中率�?0%�?

## 风险
- 数据更新后缓存失�?�?设计版本号与刷新策略�?

## 里程�?
- 预计1天�?

## 交付�?
- stats_service模块、缓存策略文档、测试�?
