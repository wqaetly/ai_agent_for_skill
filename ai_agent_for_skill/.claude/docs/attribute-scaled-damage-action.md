# AttributeScaledDamageAction - 属性缩放伤害行为

## 概述

`AttributeScaledDamageAction` 是一个高度灵活的伤害Action，支持基于多种角色属性（攻击力、法强、生命值等）的复杂伤害计算。与简单的`DamageAction`不同，它能够区分"总攻击力"和"额外攻击力"，并支持同时应用多个属性缩放。

## 适用场景

- 需要多属性缩放的技能（如泰达米尔E：75 + 130%额外AD + 80%AP）
- 区分总攻击力和额外攻击力的技能
- 基于生命值（最大/当前/已损失）缩放的技能
- 需要灵活属性组合的复杂伤害计算

## 核心特性

### 1. 灵活的属性缩放系统

**支持的属性类型（ScalingAttributeType）：**

| 属性类型 | 说明 | 典型应用 |
|---------|------|---------|
| TotalAttackDamage | 总攻击力（基础+额外） | 普攻、大部分AD技能 |
| **BonusAttackDamage** | 额外攻击力（仅装备/符文提供） | 泰达米尔E、瑞文R等 |
| SpellPower | 法术强度 | AP技能 |
| MaxHealth | 最大生命值 | 坦克技能 |
| CurrentHealth | 当前生命值 | 赵信W |
| MissingHealth | 已损失生命值 | 处决技能 |
| Armor | 护甲 | 拉莫斯W |
| MagicResist | 魔法抗性 | 加里奥被动 |
| MovementSpeed | 移动速度 | 劫R |
| AttackSpeed | 攻击速度 | 剑圣R |

### 2. 伤害计算公式

```
最终伤害 = 基础伤害(随等级) + Σ(属性值 × 缩放系数)

基础伤害 = baseDamage + damagePerLevel × (技能等级 - 1)
属性加成 = Σ(GetAttributeValue(属性类型) × scalingRatio)
```

### 3. 暴击系统

- **可选暴击**：`canCritical`开关
- **暴击率来源**：
  - 使用施法者暴击率（`useCasterCritChance = true`）
  - 使用固定暴击率（`fixedCriticalChance`）
- **暴击倍数**：可配置`criticalMultiplier`

### 4. 参数说明

#### 伤害设置（Damage Settings）

| 参数 | 类型 | 说明 |
|------|------|------|
| baseDamage | float | 基础伤害值 |
| damageType | DamageType | 伤害类型（物理/魔法/纯净） |
| damageVariance | float | 伤害浮动范围（0-0.5） |

#### 缩放设置（Scaling Settings）

| 参数 | 类型 | 说明 |
|------|------|------|
| scaleWithLevel | bool | 是否随技能等级缩放 |
| damagePerLevel | float | 每级增加的基础伤害 |
| attributeScalings | AttributeScaling[] | 属性缩放数组 |

**AttributeScaling结构：**
```csharp
{
    attributeType: ScalingAttributeType,  // 属性类型
    scalingRatio: float                   // 缩放比例（1.3 = 130%）
}
```

#### 暴击设置（Critical Settings）

| 参数 | 类型 | 说明 |
|------|------|------|
| canCritical | bool | 是否可以暴击 |
| useCasterCritChance | bool | 使用施法者暴击率 |
| fixedCriticalChance | float | 固定暴击率（0-1） |
| criticalMultiplier | float | 暴击倍数 |

#### 目标设置（Target Settings）

| 参数 | 类型 | 说明 |
|------|------|------|
| targetFilter | TargetFilter | 目标筛选（敌人/友军/自己/所有） |
| maxTargets | int | 最大目标数量 |
| damageRadius | float | 伤害半径（0=单体） |

## 实现示例：泰达米尔E技能

### 技能数据（伤害部分）

```csharp
baseDamage = 75f;
damageType = DamageType.Physical;
scaleWithLevel = true;
damagePerLevel = 30f;  // 5级时：75 + 30×4 = 195

attributeScalings = new AttributeScaling[]
{
    new AttributeScaling
    {
        attributeType = ScalingAttributeType.BonusAttackDamage,
        scalingRatio = 1.3f  // 130%额外AD
    },
    new AttributeScaling
    {
        attributeType = ScalingAttributeType.SpellPower,
        scalingRatio = 0.8f  // 80%AP
    }
};

canCritical = true;
useCasterCritChance = true;
criticalMultiplier = 2f;

targetFilter = TargetFilter.Enemy;
maxTargets = 10;
damageRadius = 3f;  // 3米范围AOE
```

### 计算示例

**场景：5级技能，50额外AD，100AP，30%暴击率**

```
基础伤害 = 75 + 30 × (5 - 1) = 75 + 120 = 195
额外AD加成 = 50 × 1.3 = 65
AP加成 = 100 × 0.8 = 80
总伤害 = 195 + 65 + 80 = 340

如果暴击（30%概率）：
暴击伤害 = 340 × 2 = 680
```

### 各等级伤害对比

| 等级 | 基础伤害 | 50额外AD加成 | 100AP加成 | 总伤害（不暴击） |
|------|---------|-------------|----------|----------------|
| 1 | 75 | 65 | 80 | 220 |
| 2 | 105 | 65 | 80 | 250 |
| 3 | 135 | 65 | 80 | 280 |
| 4 | 165 | 65 | 80 | 310 |
| 5 | 195 | 65 | 80 | 340 |

## 代码位置

- **Action脚本**: `Assets/Scripts/SkillSystem/Actions/AttributeScaledDamageAction.cs:1`
- **枚举定义**:
  - `ScalingAttributeType`: 同文件内
  - `AttributeScaling`: 同文件内

## 执行流程

1. **OnEnter**:
   - 调用`ExecuteDamage()`执行伤害逻辑

2. **ExecuteDamage**:
   - 调用`CalculateDamage()`计算基础伤害
   - 调用`RollCritical()`判断是否暴击
   - 如果暴击，伤害乘以`criticalMultiplier`
   - 应用伤害浮动（`damageVariance`）
   - 调用`ApplyDamageToTargets()`应用伤害

3. **CalculateDamage**:
   - 计算等级缩放的基础伤害
   - 遍历`attributeScalings`数组
   - 对每个属性：获取属性值 × 缩放系数
   - 累加所有伤害

4. **OnTick**: 无操作（伤害在OnEnter执行）

5. **OnExit**: 清理和日志输出

## 设计优势

### 1. 消除特殊情况（Good Taste）

**传统做法（有特殊分支）：**
```csharp
if (useAD) damage += ad * adRatio;
if (useAP) damage += ap * apRatio;
if (useBonusAD) damage += bonusAD * bonusADRatio;
// 每种属性都需要一个if判断
```

**AttributeScaledDamageAction做法（无特殊情况）：**
```csharp
foreach (var scaling in attributeScalings)
{
    damage += GetAttributeValue(scaling.attributeType) * scaling.scalingRatio;
}
// 统一处理，无条件分支
```

### 2. 数据驱动

所有伤害行为通过配置决定，无需修改代码：
- 添加新属性类型？扩展`ScalingAttributeType`枚举即可
- 新技能需要不同缩放？修改`attributeScalings`数组即可

### 3. 高扩展性

未来可轻松添加：
- 新的属性类型（如护盾值、能量值等）
- 动态属性（如敌人生命值百分比）
- 复杂计算（如属性平方、对数缩放等）

## 与DamageAction的对比

| 特性 | DamageAction | AttributeScaledDamageAction |
|------|-------------|---------------------------|
| 基础伤害 | ✅ | ✅ |
| 伤害类型 | ✅ | ✅ |
| 简单缩放 | ❌ | ✅（多属性） |
| 区分总AD/额外AD | ❌ | ✅ |
| 等级缩放 | ❌ | ✅ |
| 灵活配置 | ❌ | ✅ |
| 复杂度 | 低 | 中 |
| 适用场景 | 简单技能 | 复杂技能 |

## 使用建议

### 何时使用AttributeScaledDamageAction

- 技能伤害公式包含多个属性缩放
- 需要区分总攻击力和额外攻击力
- 需要基于生命值等特殊属性缩放
- 技能伤害随等级显著变化

### 何时使用DamageAction

- 简单的固定伤害
- 不需要复杂缩放的技能
- 快速原型开发

## 扩展示例

### 示例1：坦克技能（基于最大生命值）

```csharp
baseDamage = 50f;
damageType = DamageType.Magical;
attributeScalings = new[]
{
    new AttributeScaling { attributeType = ScalingAttributeType.MaxHealth, scalingRatio = 0.03f }
};
// 伤害 = 50 + 3%最大生命值
```

### 示例2：处决技能（基于已损失生命值）

```csharp
baseDamage = 100f;
damageType = DamageType.Physical;
attributeScalings = new[]
{
    new AttributeScaling { attributeType = ScalingAttributeType.MissingHealth, scalingRatio = 0.1f }
};
// 伤害 = 100 + 10%已损失生命值（越残血伤害越高）
```

### 示例3：混合伤害技能

```csharp
baseDamage = 80f;
damageType = DamageType.Physical;  // 主要是物理伤害
attributeScalings = new[]
{
    new AttributeScaling { attributeType = ScalingAttributeType.TotalAttackDamage, scalingRatio = 1.0f },
    new AttributeScaling { attributeType = ScalingAttributeType.SpellPower, scalingRatio = 0.5f }
};
// 伤害 = 80 + 100%总AD + 50%AP（AD/AP双修）
```

## 相关文档

- [泰达米尔旋风斩技能配置](./tryndamere-spinning-slash-skill.md)
- [DamageAction](需要时参考DamageAction.cs) - 简单伤害Action
- [Timeline技能编辑器](./timeline-skill-editor.md)

## 技术细节

### 属性值获取（模拟实现）

当前`GetAttributeValue()`是模拟实现，返回硬编码的测试数据。在实际项目中，应该：

1. 从角色属性系统获取实时数值
2. 处理属性修正（Buff/装备/符文等）
3. 考虑属性上下限
4. 缓存频繁访问的属性值

### 暴击机制

暴击判断发生在伤害应用之前，影响整个技能伤害（包括所有缩放）。这符合大部分MOBA游戏的设计。

如果需要"只有基础伤害暴击"或"属性加成部分不暴击"，需要修改`ExecuteDamage()`逻辑。

## 性能考虑

- **属性缩放数组遍历**：O(n)复杂度，但n通常很小（1-4个元素）
- **属性值查询**：建议在角色系统中缓存计算结果
- **伤害计算频率**：每次技能释放仅计算一次，性能影响可忽略
