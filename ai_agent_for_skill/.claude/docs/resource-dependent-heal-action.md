# ResourceDependentHealAction - 基于资源消耗的治疗行为

## 概述

`ResourceDependentHealAction` 是一个通用的资源消耗型治疗Action，用于实现"消耗指定资源来回复生命/法力"的技能机制。该Action支持复杂的治疗量计算公式，包括技能等级缩放和法术强度加成。

## 适用场景

- 泰达米尔Q技能（消耗怒气回复生命）
- 吸血术（消耗法力按比例回血）
- 任何需要"资源交换"机制的治疗技能

## 核心特性

### 1. 资源消耗机制

**消耗模式（ConsumeMode）：**
- `All`: 消耗所有当前资源
- `Fixed`: 消耗固定数量资源

**支持的资源类型（ResourceType）：**
- Health（生命值）
- Mana（法力值）
- **Rage（怒气值）** - 新增
- Gold（金币）
- Experience（经验值）

### 2. 治疗量计算公式

```
总治疗量 = 基础治疗量 + 每资源治疗量 × 消耗的资源量

基础治疗量 = baseHeal + (baseHealPerLevel × (技能等级 - 1)) + (法术强度 × baseSpellPowerRatio)
每资源治疗量 = perResourceHeal + (perResourceHealPerLevel × (技能等级 - 1)) + (法术强度 × perResourceSpellPowerRatio)
```

### 3. 参数说明

#### 资源设置（Resource Settings）

| 参数 | 类型 | 说明 |
|------|------|------|
| resourceType | ResourceType | 要消耗的资源类型 |
| consumeMode | ConsumeMode | 消耗模式（全部/固定） |
| fixedConsumeAmount | float | 固定消耗量（仅在Fixed模式下有效） |

#### 治疗设置（Heal Settings）

| 参数 | 类型 | 说明 |
|------|------|------|
| healType | HealType | 治疗类型（生命值/法力值/两者） |
| baseHeal | float | 基础治疗量（不依赖资源消耗） |
| perResourceHeal | float | 每单位资源的治疗量 |

#### 等级缩放设置（Scaling Settings）

| 参数 | 类型 | 说明 |
|------|------|------|
| scaleWithLevel | bool | 是否随技能等级缩放 |
| baseHealPerLevel | float | 每级增加的基础治疗量 |
| perResourceHealPerLevel | float | 每级增加的每资源治疗量 |

#### 法术强度设置（Spell Power Settings）

| 参数 | 类型 | 说明 |
|------|------|------|
| baseSpellPowerRatio | float | 基础治疗的法强系数（如0.3表示30%法强加成） |
| perResourceSpellPowerRatio | float | 每资源治疗的法强系数（如0.012表示1.2%法强加成） |

## 实现示例：泰达米尔Q技能

### 技能数据（以1级为例）

```csharp
// 基础设置
resourceType = ResourceType.Rage;
consumeMode = ConsumeMode.All;
healType = HealType.Health;

// 治疗量设置
baseHeal = 30f;
perResourceHeal = 0.5f;

// 等级缩放
scaleWithLevel = true;
baseHealPerLevel = 10f;          // 每级+10基础治疗
perResourceHealPerLevel = 0.45f; // 每级+0.45每怒气治疗

// 法术强度加成
baseSpellPowerRatio = 0.3f;        // 基础治疗享受30%法强
perResourceSpellPowerRatio = 0.012f; // 每怒气治疗享受1.2%法强
```

### 计算示例

假设：
- 技能等级：1
- 当前怒气：100
- 法术强度：100

```
基础治疗 = 30 + (10 × 0) + (100 × 0.3) = 30 + 0 + 30 = 60
每怒气治疗 = 0.5 + (0.45 × 0) + (100 × 0.012) = 0.5 + 0 + 1.2 = 1.7
总治疗量 = 60 + (1.7 × 100) = 60 + 170 = 230
```

### 技能等级数据对比

| 等级 | 基础治疗 | 每怒气治疗 | 满怒气治疗（100法强） |
|------|----------|------------|----------------------|
| 1 | 30+30%AP | 0.5+1.2%AP | 230 |
| 2 | 40+30%AP | 0.95+1.2%AP | 265 |
| 3 | 50+30%AP | 1.4+1.2%AP | 300 |
| 4 | 60+30%AP | 1.85+1.2%AP | 335 |
| 5 | 70+30%AP | 2.3+1.2%AP | 370 |

## 代码位置

- **Action脚本**: `Assets/Scripts/SkillSystem/Actions/ResourceDependentHealAction.cs:1`
- **ResourceType枚举**: `Assets/Scripts/SkillSystem/Actions/ResourceAction.cs:530`

## 执行流程

1. **OnEnter**:
   - 计算并消耗资源
   - 基于消耗的资源量计算治疗量
   - 应用治疗效果
   - 播放特效和音效

2. **OnTick**: 无操作（瞬间效果）

3. **OnExit**: 清理和日志输出

## 扩展性

该Action设计为通用型，可以通过调整参数实现：

1. **不同资源消耗**: 修改`resourceType`
2. **不同消耗模式**: 切换`consumeMode`
3. **不同缩放曲线**: 调整`baseHealPerLevel`和`perResourceHealPerLevel`
4. **不同法强加成**: 修改两个`spellPowerRatio`参数

## 设计理念

遵循"Good Taste"原则：
- **单一职责**: 只处理"资源→治疗"的转换逻辑
- **无特殊情况**: 所有技能等级和资源量都使用相同的计算公式
- **数据驱动**: 所有行为通过参数配置，无需修改代码

## 相关文档

- [泰达米尔嗜血杀戮技能配置](./tryndamere-bloodlust-skill.md)
- [Timeline技能编辑器](./timeline-skill-editor.md)
- [ResourceAction资源操作](需要时参考ResourceAction.cs的实现)
