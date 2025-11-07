# REQ-09 MCP Tool: generate_action_json

## 背景
- 需要将推理结果转换为Odin序列化JSON片段，保证Unity可直接读取。

## 功能目标
- 输入action_type/parameters/frame/duration，输出Odin格式json_snippet与验证结果。

## 实现步骤
1. 建立Action→Odin元信息映射，包含$type、命名空间、Unity类型描述。
2. 根据参数生成字段，并为嵌套结构（Vector3等）生成子对象。
3. 自动分配$id并调用Tool6执行快速校验。

## 数据与依赖
- Action元数据、REQ02输出参数、SchemaValidator。

## 验收标准
- 生成结果可直接粘贴进技能JSON，并在Unity中通过反序列化。
- 校验失败时返回详细错误及定位信息。

## 风险
- Odin格式升级 → 通过配置映射隔离，并写入版本号。

## 交付
- JSON模板库、生成器实现、snapshot测试、使用示例。
