# 赛恩W技能 - 灵魂熔炉 (Sion Soul Furnace)

## 技能概述

赛恩的W技能"灵魂熔炉"是一个双阶段主动技能：
- **第一阶段**：获得基于属性缩放的护盾，持续6秒
- **第二阶段**：3秒后若护盾仍存在，可引爆护盾造成范围魔法伤害（对非英雄单位有伤害上限）

**注意**：本实现仅包含主动部分。被动效果（击杀单位获得永久生命值）属于事件驱动机制，不在Timeline范畴内。

---

## 技能数值

### 护盾值计算公式

**护盾值** = 基础护盾(随等级) + 40%法术强度 + (8%/10%/12%/14%/16%)当前生命值

| 等级 | 基础护盾 | 生命值缩放 |
|------|---------|-----------|
| 1    | 60      | 8%        |
| 2    | 75      | 10%       |
| 3    | 90      | 12%       |
| 4    | 105     | 14%       |
| 5    | 120     | 16%       |

- **持续时间**：6秒
- **护盾类型**：吸收型，可抵挡物理和魔法伤害

### 引爆伤害计算公式

**伤害值** = 基础伤害(随等级) + 40%法术强度 + 14%施法者最大生命值

| 等级 | 基础伤害 |
|------|---------|
| 1    | 40      |
| 2    | 65      |
| 3    | 90      |
| 4    | 115     |
| 5    | 140     |

- **伤害类型**：魔法伤害
- **作用范围**：半径5米的AOE
- **对小兵/野怪伤害上限**：400点（基础伤害+属性缩放后，超过400的部分被截断）

---

## Timeline配置详解

### 基本信息
- **技能ID**：`sion-soul-furnace-001`
- **总时长**：180帧（6秒 @ 30fps）
- **帧率**：30fps

### Track 1: Shield Track（护盾轨道）

**Action类型**：AttributeScaledShieldAction

**时间配置**：
- 起始帧：0
- 持续帧数：180（整个技能持续期间）

**关键参数**：
```json
{
  "baseShieldAmount": 60.0,
  "shieldPerLevel": 15.0,
  "spellPowerRatio": 0.4,
  "healthRatio": 0.08,
  "healthRatioPerLevel": 0.02,
  "useCurrentHealth": true,
  "shieldDuration": 6.0,
  "shieldType": "Absorption"
}
```

**功能**：
- 在技能开始时立即施加护盾
- 护盾值动态计算，基于当前属性
- 护盾会在6秒后自动消失（如果未被破坏）

### Track 2: Explosion Damage Track（引爆伤害轨道）

**Action类型**：UnitTypeCappedDamageAction

**时间配置**：
- 起始帧：90（技能释放后3秒）
- 持续帧数：1（瞬发伤害）

**关键参数**：
```json
{
  "baseDamage": 40.0,
  "damagePerLevel": 25.0,
  "spellPowerRatio": 0.4,
  "maxHealthRatio": 0.14,
  "useTargetMaxHealth": false,
  "damageType": "Magical",
  "damageRadius": 5.0,
  "damageCaps": [
    {"unitType": "Minion", "damageCap": 400.0},
    {"unitType": "Monster", "damageCap": 400.0}
  ]
}
```

**功能**：
- 在第3秒时触发引爆伤害
- 对英雄造成完整伤害（无上限）
- 对小兵和野怪最多造成400点伤害
- 5米范围AOE伤害

### Track 3: Animation Track（动画轨道）

**Action类型**：AnimationAction

**配置**：
- 播放护盾施加动画
- 动画持续1秒

### Track 4: Audio Track（音频轨道）

**包含2个AudioAction**：

1. **护盾施加音效**（帧0）
   - 音频文件：`sion_soul_furnace_cast`
   - 3D音效，传播范围3-15米

2. **护盾引爆音效**（帧90）
   - 音频文件：`sion_soul_furnace_explosion`
   - 3D音效，传播范围5-20米
   - 更高优先级（200 vs 180）

---

## 新创建的Action脚本

为实现此技能，创建了两个通用Action：

### 1. AttributeScaledShieldAction

**文件位置**：`Assets/Scripts/SkillSystem/Actions/AttributeScaledShieldAction.cs`

**功能概述**：
- 提供基于多种属性动态缩放的护盾系统
- 支持法术强度、当前/最大生命值等属性缩放
- 护盾值随技能等级增长
- 可配置护盾类型（吸收/减伤/格挡）

**适用技能**：
- 赛恩W - 灵魂熔炉
- 塞拉斯W - 弑君突刺（吸血+护盾）
- 诺提勒斯W - 泰坦之怒
- 其他需要属性缩放护盾的技能

**核心参数**：
- `baseShieldAmount`：基础护盾值
- `shieldPerLevel`：每级增加的护盾值
- `spellPowerRatio`：法强缩放比例
- `healthRatio`：生命值缩放基础比例
- `healthRatioPerLevel`：每级增加的生命值缩放
- `useCurrentHealth`：使用当前还是最大生命值

### 2. UnitTypeCappedDamageAction

**文件位置**：`Assets/Scripts/SkillSystem/Actions/UnitTypeCappedDamageAction.cs`

**功能概述**：
- 造成基于属性缩放的伤害
- 对不同单位类型应用独立的伤害上限
- 支持法强、生命值等多属性缩放
- 可配置AOE范围

**适用技能**：
- 赛恩W - 灵魂熔炉（引爆）
- 塞拉斯被动 - 节能飞弹（对非英雄有上限）
- 薇恩W - 圣银弩箭（真实伤害，对野怪有上限）
- 其他对非英雄单位有伤害限制的技能

**核心参数**：
- `baseDamage`：基础伤害
- `damagePerLevel`：每级增加的伤害
- `spellPowerRatio`：法强缩放比例
- `maxHealthRatio`：最大生命值缩放比例
- `damageCaps`：单位类型伤害上限数组
- `damageRadius`：AOE范围

**单位类型枚举**：
- `Hero`：英雄
- `Minion`：小兵
- `Monster`：野怪
- `Building`：建筑
- `Ward`：守卫/眼

---

## 技能执行流程

### 时间轴（30fps）

```
Frame 0-29    (0-1秒)：护盾施加，播放施加音效和动画
Frame 30-89   (1-3秒)：护盾持续存在
Frame 90      (3秒)  ：护盾引爆，造成AOE伤害，播放引爆音效
Frame 91-179  (3-6秒)：护盾继续存在（如果未被破坏）
Frame 180     (6秒)  ：护盾消失，技能结束
```

### 实际游戏逻辑

在实际游戏中，引爆伤害应该由玩家手动触发（再次按W键）。Timeline配置展示的是"标准流程"：

1. **施放技能**（玩家按下W）
   - 立即获得护盾
   - 护盾会在6秒后自动消失

2. **引爆护盾**（玩家在3秒后再次按下W）
   - 如果护盾仍存在，引爆造成AOE伤害
   - 游戏逻辑判断护盾状态，决定是否执行引爆Action

3. **护盾被破坏**
   - 如果护盾在6秒内被伤害完全消耗，播放破盾特效
   - 无法再引爆

---

## 编译验证

✅ 所有脚本编译通过，0错误

**编译命令**：
```bash
dotnet build ai_agent_for_skill.sln
```

**结果**：
- `AttributeScaledShieldAction.cs` - 编译成功
- `UnitTypeCappedDamageAction.cs` - 编译成功
- `SionSoulFurnace.json` - 配置生成成功

---

## 使用说明

### 在Unity编辑器中加载技能

1. 打开技能编辑器窗口（菜单：Tools > Skill Editor）
2. 点击"Load Skill"按钮
3. 选择文件：`Assets/Skills/SionSoulFurnace.json`
4. 技能配置将加载到编辑器中

### 查看技能配置

- **Shield Track**：查看护盾的数值配置和持续时间
- **Explosion Damage Track**：查看引爆伤害的配置和单位类型上限
- **Animation/Audio Track**：查看视觉和音效配置

### 测试技能

1. 在编辑器中点击"Play"按钮
2. 观察Timeline播放：
   - 帧0：护盾施加日志输出
   - 帧90：引爆伤害日志输出
   - 查看Console窗口的详细计算日志

---

## 扩展建议

### 被动效果实现

赛恩W的被动（击杀单位获得永久生命值）应该在以下系统中实现：

1. **事件监听系统**
   - 监听单位死亡事件
   - 判断击杀者是否为赛恩
   - 判断被击杀单位类型

2. **属性增长系统**
   - 永久增加最大生命值
   - 更新角色属性面板
   - 保存数值（跨局游戏）

**不要在Timeline中实现被动**，Timeline只负责主动释放的技能效果。

### 引爆触发优化

在实际游戏中，可以考虑以下优化：

1. **手动触发**
   - 监听玩家输入（再次按W）
   - 检查护盾是否存在
   - 如果存在，跳转到Frame 90执行引爆

2. **自动引爆**
   - 如果希望实现"6秒后自动引爆"，保持当前配置不变
   - 如果希望"提前引爆"，需要在游戏逻辑中手动触发Action

3. **条件引爆**
   - 添加条件判断：护盾是否被破坏
   - 如果护盾已破坏，跳过引爆Action

---

## 总结

赛恩W技能"灵魂熔炉"成功实现，完整展示了：

✅ **属性缩放护盾系统** - 护盾值动态计算，基于法强和当前生命值
✅ **单位类型伤害上限** - 对英雄无限制，对小兵/野怪有400上限
✅ **双阶段技能流程** - 护盾施加（3秒） → 引爆伤害
✅ **完整的Timeline配置** - 4条轨道，协同工作
✅ **通用Action脚本** - 可复用于其他类似技能

**文件清单**：
- `Assets/Scripts/SkillSystem/Actions/AttributeScaledShieldAction.cs`
- `Assets/Scripts/SkillSystem/Actions/UnitTypeCappedDamageAction.cs`
- `Assets/Skills/SionSoulFurnace.json`
- `.claude/docs/sion-soul-furnace-skill.md`
