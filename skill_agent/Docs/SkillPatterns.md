# 技能设计模式参�?

本文档总结常见的技能设计模式，帮助开发者快速构建技能�?

## 目录

- [基础模式](#基础模式)
- [伤害模式](#伤害模式)
- [移动模式](#移动模式)
- [控制模式](#控制模式)
- [组合模式](#组合模式)
- [高级模式](#高级模式)

---

## 基础模式

### 1. 单次即时效果
**描述**: 技能释放后立即产生效果，无持续时间�?

**典型Actions**:
- DamageAction (duration=0)
- HealAction (duration=0)
- TeleportAction

**时间轴示�?*:
```
Frame 0: AnimationAction (播放施法动画)
Frame 15: DamageAction (造成伤害)
Frame 15: AudioAction (播放音效)
```

**应用场景**: 火球术、治疗术、闪�?

---

### 2. 持续效果
**描述**: 技能效果持续一段时间�?

**典型Actions**:
- BuffAction (持续增益/减益)
- AreaOfEffectAction (持续伤害)
- HealAction (持续治疗)

**时间轴示�?*:
```
Frame 0-300: BuffAction (持续10秒的加速Buff)
Frame 0-300: AnimationAction (循环播放Buff动画)
```

**应用场景**: 增益技能、毒药、持续治�?

---

### 3. 通道技�?
**描述**: 需要持续引导，中断则失效�?

**典型Actions**:
- ControlAction (限制自身移动)
- AreaOfEffectAction (持续伤害)
- 配合InputDetectionAction检测打�?

**时间轴示�?*:
```
Frame 0-150: ControlAction (自身无法移动/释放技�?
Frame 0-150: AreaOfEffectAction (�?.5秒造成伤害)
Frame 0-150: AnimationAction (引导动画)
```

**应用场景**: 暴风雪、传送读条、治疗通道

---

## 伤害模式

### 4. 单体爆发伤害
**描述**: 对单个目标造成高额瞬间伤害�?

**Action组合**:
```
AnimationAction (施法动画)
�?ProjectileAction (可选，发射弹道)
�?DamageAction (baseDamage�? maxTargets=1)
�?AudioAction + VisualEffect
```

**参数建议**:
- baseDamage: 200-500
- criticalChance: 0.1-0.3
- damageType: Physical或Magical

**应用场景**: 刺杀技能、单体大�?

---

### 5. AOE范围伤害
**描述**: 对区域内所有敌人造成伤害�?

**Action组合**:
```
AnimationAction
�?AreaOfEffectAction (effectRadius较大)
�?
�?DamageAction (damageRadius > 0, maxTargets > 1)
```

**参数建议**:
- effectRadius: 5-15单位
- maxTargets: 5-10
- damagePerSecond: 30-100（持续伤害）

**应用场景**: 火焰风暴、冰霜新星、地�?

---

### 6. 弹道伤害
**描述**: 发射弹道，命中目标造成伤害�?

**Action组合**:
```
AnimationAction (投掷动画)
�?ProjectileAction (projectileSpeed适中)
   └─ onHitAction: DamageAction
�?CollisionAction (检测命�?
```

**参数建议**:
- projectileSpeed: 10-30单位/�?
- pierceCount: 0（不穿透）�?-3（穿透）
- maxDistance: 15-30单位

**应用场景**: 飞箭、火球、飞�?

---

### 7. 持续伤害（DOT�?
**描述**: 在一段时间内持续造成伤害�?

**Action组合**:
```
AnimationAction
�?BuffAction (debuff图标)
�?AreaOfEffectAction (tickInterval=0.5-1.0�?
```

**参数建议**:
- duration: 90-300帧（3-10秒）
- damagePerSecond: 20-50
- tickInterval: 0.5-1.0�?

**应用场景**: 毒药、燃烧、流血

---

## 移动模式

### 8. 冲锋/突进
**描述**: 快速移动到目标位置，可能造成伤害�?

**Action组合**:
```
MovementAction (movementType=Linear, 高速度)
�?DamageAction (在终点或路径�?
�?ControlAction (移动期间无法操作)
```

**参数建议**:
- movementSpeed: 15-30单位/�?
- maxDistance: 10-20单位
- canBeInterrupted: true/false

**应用场景**: 冲锋、突进、跳�?

---

### 9. 位移闪避
**描述**: 短距离快速移动，通常用于躲避�?

**Action组合**:
```
MovementAction (movementType=Linear或Arc)
�?BuffAction (短暂无敌/加�?
�?AnimationAction (翻滚/闪避动画)
```

**参数建议**:
- movementSpeed: 20-40单位/�?
- duration: 15-30帧（0.5-1秒）
- arcHeight: 1-3单位（跳跃类�?

**应用场景**: 翻滚、侧闪、后�?

---

### 10. 传�?闪现
**描述**: 瞬间移动到目标位置�?

**Action组合**:
```
AnimationAction (施法动画)
�?TeleportAction (instant)
�?VisualEffect (传送特�?
```

**参数建议**:
- teleportType: ToPosition
- maxDistance: 10-15单位
- requiresVision: true（竞技向）

**应用场景**: 闪现、传送、空间跳�?

---

## 控制模式

### 11. 硬控（眩�?定身�?
**描述**: 完全限制目标行动�?

**Action组合**:
```
ProjectileAction �?DamageAction
�?ControlAction (controlType=Stun/Root)
�?BuffAction (控制debuff图标)
```

**参数建议**:
- duration: 30-120帧（1-4秒）
- canBeDispelled: true
- controlType: Stun或Root

**应用场景**: 眩晕技能、束缚、石�?

---

### 12. 软控（减�?缴械�?
**描述**: 部分限制目标能力�?

**Action组合**:
```
AreaOfEffectAction
�?ControlAction (controlType=Slow/Disarm)
�?BuffAction (减�?缴械图标)
```

**参数建议**:
- slowPercentage: 0.3-0.7�?0%-70%减速）
- duration: 60-180帧（2-6秒）

**应用场景**: 减速领域、缴械、沉�?

---

## 组合模式

### 13. 位移+伤害组合
**描述**: 移动的同时造成伤害�?

**Action组合**:
```
Track 1: MovementAction (整个过程)
Track 2: DamageAction (起点/终点/路径)
Track 3: AnimationAction + AudioAction
```

**实例**:
- Riven Broken Wings: 三段突进，每段都有伤�?
- 旋风�? 旋转移动造成范围伤害

---

### 14. 伤害+治疗组合
**描述**: 造成伤害的同时治疗自己或队友�?

**Action组合**:
```
Track 1: DamageAction (targetFilter=Enemy)
Track 2: HealAction (targetFilter=Ally或Self)
   └─ 或使用lifeStealPercentage参数
```

**实例**:
- 吸血技�?
- 伤害转治�?

---

### 15. 召唤+增益组合
**描述**: 召唤单位并给予增益�?

**Action组合**:
```
SummonAction (召唤单位)
�?BuffAction (给召唤物加Buff)
�?AnimationAction (召唤特效)
```

**实例**:
- 召唤强化幽灵
- 召唤图腾并增�?

---

## 高级模式

### 16. 连招系统
**描述**: 多个技能按特定顺序释放产生额外效果�?

**Action组合**:
```
InputDetectionAction (检测输入序�?
�?触发特殊Action�?
�?BuffAction (连招标记)
```

**实现要点**:
- 使用InputDetectionAction检测组合键
- BuffAction记录连招状�?
- 通过state machine管理连招流程

**应用场景**: 格斗游戏combo、ARPG连招

---

### 17. 充能/蓄力技�?
**描述**: 持续按住技能键增加效果强度�?

**Action组合**:
```
Phase 1 (充能): ControlAction (限制移动)
              + AnimationAction (充能动画)
Phase 2 (释放): DamageAction (根据充能时长调整伤害)
```

**实现要点**:
- 监听按键时长
- 伤害/范围随时间增�?
- 设置最大充能时�?

**应用场景**: 蓄力火球、弓箭瞄准、重�?

---

### 18. 条件触发技�?
**描述**: 满足特定条件后自动触发效果�?

**Action组合**:
```
CollisionAction (检测碰�?
�?条件判断
�?触发DamageAction/BuffAction�?
```

**条件类型**:
- 生命值阈值（血�?30%触发�?
- 连击次数（第三次攻击触发�?
- 技能命中（命中后触发追加效果）

**应用场景**: 被动技能、触发效�?

---

### 19. 变身/形态切�?
**描述**: 切换角色形态，改变技能集�?

**Action组合**:
```
BuffAction (形态标�? duration�?
�?AnimationAction (变身动画)
�?AttributeScaling (属性变�?
�?解锁新技能集
```

**实现要点**:
- 使用Buff标记当前形�?
- 技能CD独立或共�?
- 属性临时改�?

**应用场景**: 狼人变身、龙形态、战斗姿�?

---

### 20. 反击/格挡技�?
**描述**: 在受到攻击时触发反击效果�?

**Action组合**:
```
BuffAction (格挡状�? 短duration)
�?CollisionDetection (检测受�?
�?条件触发:
   └─ DamageAction (反伤)
   └─ ControlAction (反控)
```

**实现要点**:
- 短时间格挡窗口（0.5-2秒）
- 检测受击事�?
- 触发反制效果

**应用场景**: 格挡反击、荆棘光环、反弹护�?

---

## 技能平衡建�?

### 伤害类技�?
| 类型 | 伤害范围 | 冷却时间 | 施法距离 |
|------|----------|----------|----------|
| 单体爆发 | 200-500 | 8-15�?| 10-15单位 |
| AOE范围 | 150-300 | 10-20�?| 8-12单位 |
| 持续伤害 | 100-300总计 | 12-18�?| 10-15单位 |
| 终极技�?| 500-1000 | 60-120�?| 15-20单位 |

### 控制类技�?
| 类型 | 控制时长 | 冷却时间 | 施法距离 |
|------|----------|----------|----------|
| 眩晕 | 1-3�?| 10-15�?| 8-12单位 |
| 定身 | 2-4�?| 12-18�?| 10-15单位 |
| 减�?| 3-6�?| 8-12�?| 10-15单位 |
| 沉默 | 2-5�?| 15-25�?| 8-12单位 |

### 移动类技�?
| 类型 | 距离 | 冷却时间 | 特点 |
|------|------|----------|------|
| 闪现 | 10-15单位 | 180-300�?| 瞬间 |
| 冲锋 | 8-15单位 | 12-20�?| 可被打断 |
| 位移 | 5-10单位 | 6-12�?| 快�?|

---

## 设计原则

### 1. 清晰的反�?
- 每个技能都应有明确的视�?音效反馈
- 关键帧配合特效和音效
- 伤害数字、Buff图标等UI提示

### 2. 平衡性考虑
- 高伤�?长CD或复杂操�?
- 强控�?较长CD或施法条�?
- 高机动�?低伤害或脆弱

### 3. 技能分�?
- **基础技�?*: CD短，伤害中等
- **进阶技�?*: CD中等，效果显�?
- **终极技�?*: CD长，效果强大

### 4. 互动性设�?
- 技能之间有连携（combo�?
- 可被反制或规�?
- 鼓励技巧性操�?

---

## 常见MOBA技能模�?

### 突进+伤害+减�?
```
典型代表: 诺克萨斯之手 E技�?
Frame 0: MovementAction (冲向目标)
Frame 15: DamageAction (造成伤害)
Frame 15: ControlAction (减�?
```

### 弹道+范围伤害+控制
```
典型代表: 光辉女郎 Q技�?
Frame 0: ProjectileAction (发射光球)
OnHit: DamageAction + ControlAction (定身)
```

### 位移+护盾+强化
```
典型代表: 瑞文 E技�?
Frame 0: MovementAction (短距离冲�?
Frame 0: ShieldAction (获得护盾)
Frame 0: BuffAction (下次攻击强化)
```

---

## 版本历史
- v1.0 (2025-01-29): 初始版本，包�?0种设计模�?
