# Action参数详细参考

本文档详细说明所有Action类型的参数及其含义，供RAG系统索引和开发者参考。

## 目录

- [基础Action](#基础action)
- [伤害类Action](#伤害类action)
- [治疗类Action](#治疗类action)
- [移动类Action](#移动类action)
- [弹道类Action](#弹道类action)
- [控制类Action](#控制类action)
- [状态类Action](#状态类action)
- [视听类Action](#视听类action)

---

## 基础Action

所有Action都继承自`ISkillAction`，包含以下基础参数：

### 共通参数
- **frame** (int): 开始执行的帧数
- **duration** (int): 持续时间（帧数）
- **enabled** (bool): 是否启用此Action

---

## 伤害类Action

### DamageAction - 基础伤害
造成伤害，支持暴击、吸血等效果。

**参数:**
- **baseDamage** (float): 基础伤害值
- **damageType** (enum): 伤害类型
  - `Physical`: 物理伤害
  - `Magical`: 魔法伤害
  - `Pure`: 纯粹伤害（无视护甲）
- **damageVariance** (float): 伤害浮动范围（0-1）
- **criticalChance** (float): 暴击几率（0-1）
- **criticalMultiplier** (float): 暴击倍率（通常2.0）
- **lifeStealPercentage** (float): 物理吸血百分比（0-1）
- **spellVampPercentage** (float): 法术吸血百分比（0-1）
- **targetFilter** (enum): 目标过滤
  - `Enemy`: 敌人
  - `Ally`: 友军
  - `Self`: 自己
  - `All`: 所有单位
- **maxTargets** (int): 最大目标数量
- **damageRadius** (float): 伤害半径（用于范围伤害）

**使用场景:** 所有造成伤害的技能效果

---

### AttributeScaledDamageAction - 属性加成伤害
伤害随角色属性缩放。

**参数:**
- 继承 `DamageAction` 所有参数
- **attributeType** (enum): 属性类型
  - `Strength`: 力量
  - `Agility`: 敏捷
  - `Intelligence`: 智力
  - `AttackDamage`: 攻击力
  - `AbilityPower`: 法术强度
- **attributeScaling** (float): 属性缩放系数
- **baseValue** (float): 基础值（不受属性影响部分）

**使用场景:** 英雄属性加成技能（如"造成100+力量150%的伤害"）

---

### UnitTypeCappedDamageAction - 单位类型伤害上限
对不同单位类型有伤害上限。

**参数:**
- 继承 `DamageAction` 所有参数
- **damageCapVsHeroes** (float): 对英雄的伤害上限
- **damageCapVsCreeps** (float): 对小兵的伤害上限
- **damageCapVsSummons** (float): 对召唤物的伤害上限

**使用场景:** AOE技能需要对不同单位类型限制伤害

---

### AreaOfEffectAction - 范围效果
在区域内造成伤害或应用效果。

**参数:**
- **effectRadius** (float): 效果半径
- **centerPosition** (Vector3): 中心位置
- **damagePerSecond** (float): 每秒伤害
- **tickInterval** (float): 伤害间隔（秒）
- **affectAllies** (bool): 是否影响友军
- **affectEnemies** (bool): 是否影响敌人
- **visualEffect** (GameObject): 视觉效果预制体

**使用场景:** 火焰风暴、冰霜新星等AOE技能

---

## 治疗类Action

### HealAction - 基础治疗
恢复生命值。

**参数:**
- **healAmount** (float): 治疗量
- **healType** (enum): 治疗类型
  - `Instant`: 瞬间治疗
  - `OverTime`: 持续治疗
- **tickInterval** (float): 治疗间隔（仅OverTime）
- **targetFilter** (enum): 目标过滤（同DamageAction）
- **maxTargets** (int): 最大目标数
- **healRadius** (float): 治疗半径
- **canOverheal** (bool): 是否可以超量治疗

**使用场景:** 治疗术、再生技能

---

### ResourceDependentHealAction - 资源依赖治疗
治疗量依赖于资源值。

**参数:**
- 继承 `HealAction` 所有参数
- **resourceType** (enum): 资源类型
  - `Health`, `Mana`, `Rage`, `Energy`
- **resourceScaling** (float): 资源缩放系数
- **consumeResource** (bool): 是否消耗资源

**使用场景:** "消耗30%最大生命值治疗队友"类技能

---

### AttributeScaledShieldAction - 属性缩放护盾
创建吸收伤害的护盾。

**参数:**
- **baseShieldAmount** (float): 基础护盾值
- **attributeType** (enum): 属性类型
- **attributeScaling** (float): 属性缩放系数
- **shieldDuration** (float): 护盾持续时间
- **shieldType** (enum): 护盾类型
  - `Physical`: 物理护盾
  - `Magical`: 魔法护盾
  - `All`: 全伤害护盾

**使用场景:** 护盾技能，伤害吸收

---

## 移动类Action

### MovementAction - 角色移动
移动角色到指定位置。

**参数:**
- **movementType** (enum): 移动类型
  - `Linear`: 直线移动
  - `Arc`: 弧线移动
  - `Curve`: 自定义曲线
  - `Instant`: 瞬移
- **targetPosition** (Vector3): 目标位置
- **movementSpeed** (float): 移动速度
- **arcHeight** (float): 弧线高度（仅Arc）
- **movementCurve** (AnimationCurve): 移动曲线（仅Curve）
- **faceMovementDirection** (bool): 是否面向移动方向
- **canBeInterrupted** (bool): 是否可被打断

**使用场景:** 冲锋、闪烁、跳跃技能

---

### TeleportAction - 瞬移
瞬间传送到目标位置。

**参数:**
- **teleportPosition** (Vector3): 传送目标位置
- **teleportType** (enum): 传送类型
  - `ToPosition`: 到指定位置
  - `ToUnit`: 到单位位置
  - `Behind`: 到单位背后
- **teleportEffect** (GameObject): 传送特效
- **requiresVision** (bool): 是否需要视野
- **maxDistance** (float): 最大传送距离

**使用场景:** 闪烁、传送技能

---

## 弹道类Action

### ProjectileAction - 弹道发射
发射弹道飞行物。

**参数:**
- **projectileType** (enum): 弹道类型
  - `Linear`: 直线弹道
  - `Arc`: 抛物线弹道
  - `Homing`: 追踪弹道
- **projectilePrefab** (GameObject): 弹道预制体
- **projectileSpeed** (float): 弹道速度
- **maxDistance** (float): 最大飞行距离
- **pierceCount** (int): 穿透次数（0=不穿透）
- **homingStrength** (float): 追踪强度（仅Homing）
- **onHitAction** (ISkillAction): 命中时触发的Action
- **destroyOnHit** (bool): 命中后是否销毁

**使用场景:** 火球术、飞箭、追踪导弹

---

### CollisionAction - 碰撞检测
检测碰撞并触发效果。

**参数:**
- **collisionType** (enum): 碰撞类型
  - `Sphere`: 球形
  - `Box`: 盒形
  - `Capsule`: 胶囊形
- **collisionRadius** (float): 碰撞半径
- **collisionLayer** (LayerMask): 碰撞层
- **triggerOnce** (bool): 是否只触发一次
- **onCollisionAction** (ISkillAction): 碰撞时触发的Action

**使用场景:** 弹道碰撞、近战攻击检测

---

## 控制类Action

### ControlAction - 输入控制
限制或禁用角色输入。

**参数:**
- **controlType** (enum): 控制类型
  - `Stun`: 眩晕（禁用所有操作）
  - `Silence`: 沉默（禁用技能）
  - `Root`: 定身（禁用移动）
  - `Disarm`: 缴械（禁用普攻）
  - `Slow`: 减速
- **slowPercentage** (float): 减速百分比（仅Slow）
- **canBeDispelled** (bool): 是否可被驱散
- **immunityType** (enum): 免疫类型

**使用场景:** 控制技能，眩晕、沉默、定身

---

### BuffAction - 增益/减益
应用状态效果。

**参数:**
- **buffType** (enum): Buff类型
  - `AttackSpeed`: 攻速
  - `MovementSpeed`: 移速
  - `Damage`: 伤害
  - `Armor`: 护甲
  - `Custom`: 自定义
- **buffValue** (float): Buff数值
- **isPercentage** (bool): 是否为百分比加成
- **stackable** (bool): 是否可叠加
- **maxStacks** (int): 最大叠加层数
- **refreshOnReapply** (bool): 重复施加是否刷新时间
- **buffIcon** (Sprite): Buff图标

**使用场景:** 增益技能、Debuff技能

---

## 视听类Action

### AnimationAction - 动画播放
播放角色动画。

**参数:**
- **animationName** (string): 动画名称
- **animationLayer** (int): 动画层
- **blendTime** (float): 混合时间
- **playbackSpeed** (float): 播放速度
- **loop** (bool): 是否循环

**使用场景:** 技能动画、特效动画

---

### AudioAction - 音效播放
播放音效。

**参数:**
- **audioClip** (AudioClip): 音频剪辑
- **volume** (float): 音量（0-1）
- **pitch** (float): 音调（0.5-2.0）
- **spatialBlend** (float): 空间混合（0=2D, 1=3D）
- **minDistance** (float): 最小距离
- **maxDistance** (float): 最大距离
- **loop** (bool): 是否循环

**使用场景:** 技能音效、环境音

---

### CameraAction - 相机效果
控制相机行为。

**参数:**
- **cameraEffectType** (enum): 效果类型
  - `Shake`: 震动
  - `Zoom`: 缩放
  - `Follow`: 跟随
- **shakeIntensity** (float): 震动强度
- **shakeDuration** (float): 震动时长
- **zoomLevel** (float): 缩放级别
- **transitionTime** (float): 过渡时间

**使用场景:** 技能释放震屏、特写镜头

---

## 其他Action

### SummonAction - 召唤单位
召唤单位。

**参数:**
- **summonPrefab** (GameObject): 召唤物预制体
- **summonCount** (int): 召唤数量
- **summonDuration** (float): 存在时长（0=永久）
- **summonPosition** (Vector3): 召唤位置
- **summonRadius** (float): 召唤半径（多单位时）
- **inheritStats** (bool): 是否继承施法者属性
- **statInheritPercentage** (float): 属性继承百分比

**使用场景:** 召唤物技能

---

### ResourceAction - 资源操作
消耗或生成资源。

**参数:**
- **resourceType** (enum): 资源类型
  - `Health`, `Mana`, `Rage`, `Energy`
- **resourceAmount** (float): 资源数量
- **isPercentage** (bool): 是否为百分比
- **operationType** (enum): 操作类型
  - `Consume`: 消耗
  - `Restore`: 恢复
  - `Set`: 设置

**使用场景:** 技能消耗、资源回复

---

### InputDetectionAction - 输入检测
检测玩家输入组合。

**参数:**
- **requiredInput** (string): 所需输入
- **detectionWindow** (float): 检测时间窗口
- **onDetectAction** (ISkillAction): 检测成功时触发的Action

**使用场景:** 连招系统、输入combo

---

### LogAction - 调试日志
输出调试信息（开发用）。

**参数:**
- **message** (string): 日志消息
- **logType** (enum): 日志类型
  - `Log`, `Warning`, `Error`

**使用场景:** 调试技能流程

---

## 参数命名规范

### 通用后缀含义
- **Percentage**: 百分比值（0-1）
- **Radius**: 半径（Unity单位）
- **Duration**: 持续时间（秒）
- **Interval**: 间隔时间（秒）
- **Multiplier**: 倍率
- **Scaling**: 缩放系数
- **Amount**: 数量/数值
- **Count**: 计数

### 常见前缀含义
- **base**: 基础值
- **max**: 最大值
- **min**: 最小值
- **can**: 布尔判断（是否可以）
- **is**: 布尔状态（是否为）

---

## 枚举类型参考

### DamageType
```csharp
enum DamageType {
    Physical,  // 物理伤害
    Magical,   // 魔法伤害
    Pure       // 纯粹伤害
}
```

### TargetFilter
```csharp
enum TargetFilter {
    Enemy,  // 敌人
    Ally,   // 友军
    Self,   // 自己
    All     // 所有单位
}
```

### ResourceType
```csharp
enum ResourceType {
    Health,  // 生命值
    Mana,    // 魔法值
    Rage,    // 怒气
    Energy   // 能量
}
```

---

## 最佳实践

### 参数设置建议
1. **伤害值**: 基础伤害通常在50-500范围
2. **持续时间**: 一般3-10秒（90-300帧@30fps）
3. **冷却时间**: 普通技能5-15秒，大招60-120秒
4. **范围**: 近战3-5单位，远程8-15单位
5. **移动速度**: 行走5单位/秒，冲刺15单位/秒

### 性能考虑
- 避免过多同时active的Action
- 碰撞检测优先使用简单形状
- 粒子特效控制在合理范围
- 音效使用对象池管理

---

## 版本历史
- v1.0 (2025-01-29): 初始版本，包含21种Action类型
