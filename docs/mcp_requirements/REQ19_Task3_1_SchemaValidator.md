# REQ-19 任务3.1 SchemaValidator

## 工作范围
- 构建约束验证器，覆盖参数范围、时序一致性与Action冲突检测。

## 实施步骤
1. 解析技能JSON为中间结构，按Action/轨道分组。
2. 依据元数据执行参数校验（min/max/enum/必填）。
3. 进行时间轴验证：frame + duration ≤ totalDuration，轨道冲突提示。
4. 注入业务规则（必须有Animation、控制与位移互斥等），产出建议。

## 依赖
- Action元数据、技能JSON解析库、pydantic/jsonschema。

## 验收标准
- 可在三种validation_level下运行，错误指向具体Action。
- 测试覆盖至少20个正/负样例。

## 风险
- JSON格式异常导致解析失败 → 在入口做结构校验并返回易懂提示。

## 里程碑
- 预计2天完成。

## 交付物
- schema_validator.py、规则配置、测试、使用指南。
