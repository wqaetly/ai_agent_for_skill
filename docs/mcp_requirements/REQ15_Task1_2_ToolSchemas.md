# REQ-15 任务1.2 工具定义与Schema设计

**状�?*: [P0-MVP必需] | **优先�?*: �?| **时间**: Day 3 | **依赖**: REQ-14

## 工作范围
- �?个Tool定义输入/输出Pydantic模型、MCP注册描述与资源URI�?
- 建立统一的错误码与验证器，便于客户端消费�?

## 实施步骤
1. 根据规划整理每个Tool的字段、类型、可选参数与默认值�?
2. 使用Pydantic v2定义模型，并添加字段级校验（range、enum等）�?
3. 在Tool registry中注册metadata（描述、示例、超时）�?
4. 为资源型输出（skill://）实现路由与权限控制�?

## 依赖
- 计划文档、Action/Skill schema、mcp-sdk接口�?

## 验收标准
- `mcp describe`能够列出全部Tool并展示示例�?
- 提供Schema单元测试与JSON schema导出�?

## 风险
- 字段变更频繁 �?引入版本号并集中管理�?

## 里程�?
- 预计1天完成，输出schema文档与示例payload�?

## 交付�?
- schema.py、工具注册表、验证测试、开发者文档�?
