# REQ-10 MCP Tool: validate_skill_config

**状态**: [P0-MVP必需] | **优先级**: 高 | **依赖**: REQ-19（核心算法）

## 背景
- 技能JSON需要在写回前做约束校验，避免时序/数值错误。

## 功能目标
- 输入skill_json与validation_level，输出valid/errors/warnings/suggestions。

## 实现步骤
1. 基于Action元数据构建静态约束（min/max/必填）。
2. 校验时间轴：frame、duration、totalDuration、轨道冲突。
3. 运行业务规则（如Damage前必须有Animation）并输出建议。

## 数据与依赖
- 依赖SchemaValidator核心库、技能JSON解析器。

## 验收标准
- 常见错误能被准确定位，错误文案指向Action+frame。
- 三个校验级别可调节严格度。

## 风险
- JSON格式异常 → 在解析阶段捕获，提示用户修复。

## 交付
- Tool实现、规则配置、单元测试、CI hook（PR自动校验）。
