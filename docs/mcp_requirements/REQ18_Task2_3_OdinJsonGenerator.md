# REQ-18 任务2.3 OdinJsonGenerator

## 工作范围
- 负责把Action+参数转换为Odin兼容JSON片段，并处理Unity特殊类型。

## 实施步骤
1. 维护Action→Odin模板映射，含$type、程序集、嵌套结构。
2. 实现类型序列化器（Vector3/Color/AnimationCurve等）。
3. 自动生成$id并与SchemaValidator联动校验。
4. 提供Formatting选项（压缩/美化）和示例快照测试。

## 依赖
- Action元数据、ParameterInferencer输出、Unity示例JSON。

## 验收标准
- 生成JSON在Unity中可直接反序列化并通过Tool6校验。
- 模板新增可通过配置扩展而无需改代码。

## 风险
- 模板遗漏字段 → 使用Golden sample测试，CI对比输出。

## 里程碑
- 预计2天。

## 交付物
- json_generator.py、模板配置、测试、使用指南。
