---
description: 从描述生成新的游戏技能配置
argument-hint: [技能描述]
allowed-tools: Read, Write, Grep, Glob, Bash
---

# 技能生成命令

你是一个专门生成 Unity 技能配置 JSON 文件的专家。根据用户的描述，生成完整、可用于生产环境的技能配置。

## 任务目标

生成一个符合以下结构的新技能配置文件：

### 需要收集的信息

如果用户没有提供完整信息，请询问以下问题：

1. **技能名称** - 技能叫什么名字？
2. **技能描述** - 技能的游戏机制是什么？
3. **所属英雄** - 哪个英雄使用这个技能？
4. **技能类型** - 伤害/治疗/护盾/增益/减益/控制/位移？
5. **核心机制** - 特殊机制（属性缩放、资源消耗、时机控制等）？
6. **持续时间** - 技能持续多少秒？
7. **帧率** - 目标帧率（默认：30fps）

### 技能配置结构

生成的 JSON 文件应遵循以下结构：

```json
{
    "$id": 0,
    "$type": "0|SkillSystem.Data.SkillData, Assembly-CSharp",
    "skillName": "技能名称",
    "skillDescription": "技能详细描述",
    "totalDuration": 180,  // 持续时间（帧数） = 秒数 * frameRate
    "frameRate": 30,
    "tracks": {
        "$id": 1,
        "$type": "1|System.Collections.Generic.List`1[[SkillSystem.Data.SkillTrack, Assembly-CSharp]], mscorlib",
        "$rlength": 3,
        "$rcontent": [
            // 轨道对象
        ]
    },
    "skillId": "英雄-技能名-001"
}
```

### 可用的 Action 类型

**伤害类 Action：**
- `AttributeScaledDamageAction` - 基于属性缩放的伤害
- `UnitTypeCappedDamageAction` - 对不同单位类型有伤害上限
- `DamageAction` - 简单伤害

**治疗类 Action：**
- `ResourceDependentHealAction` - 基于资源消耗的治疗
- `HealAction` - 简单治疗

**护盾类 Action：**
- `AttributeScaledShieldAction` - 基于属性缩放的护盾

**控制类 Action：**
- `InputDetectionAction` - 检测玩家输入以触发效果

**动画/音频：**
- `AnimationAction` - 播放动画
- `AudioAction` - 播放音效

**资源管理：**
- `ResourceAction` - 修改资源（法力、怒气、能量等）

### Action 时间设定

每个 Action 都有：
- `frame` - Action 开始的帧数（从0开始）
- `duration` - Action 持续的帧数
- `enabled` - Action 是否启用

### 最佳实践

1. **按轨道组织** - 将相关的 Action 分组（动画轨道、伤害轨道、音频轨道等）
2. **帧时机** - 合理安排 Action 的帧数（伤害在动画攻击时刻、音效配合视觉效果）
3. **使用有意义的名称** - 清晰的轨道和 Action 名称便于维护
4. **等级缩放** - 添加 `scaleWithLevel: true` 和每级缩放值以实现成长
5. **颜色编码** - 为视觉效果使用合适的颜色（伤害用红色，护盾用蓝色，治疗用绿色）
6. **3D 音频** - 对空间音频设置 `is3D: true` 并配置合适的最小/最大距离
7. **目标过滤** - 0 = 自己，1 = 敌人，2 = 友军，3 = 所有
8. **唯一 ID** - 使用格式：`英雄名-技能名-版本号`

## 示例

### 示例 1：简单伤害技能

**用户请求：**
```
为法师创建一个火球技能，造成魔法伤害
```

**生成的配置：**
```json
{
    "$id": 0,
    "$type": "0|SkillSystem.Data.SkillData, Assembly-CSharp",
    "skillName": "火球术",
    "skillDescription": "发射一个火球造成魔法伤害",
    "totalDuration": 60,
    "frameRate": 30,
    "tracks": {
        "$id": 1,
        "$type": "1|System.Collections.Generic.List`1[[SkillSystem.Data.SkillTrack, Assembly-CSharp]], mscorlib",
        "$rlength": 2,
        "$rcontent": [
            {
                "$id": 2,
                "$type": "2|SkillSystem.Data.SkillTrack, Assembly-CSharp",
                "trackName": "伤害轨道",
                "enabled": true,
                "actions": {
                    "$id": 3,
                    "$type": "3|System.Collections.Generic.List`1[[SkillSystem.Actions.ISkillAction, Assembly-CSharp]], mscorlib",
                    "$rlength": 1,
                    "$rcontent": [
                        {
                            "$id": 4,
                            "$type": "4|SkillSystem.Actions.AttributeScaledDamageAction, Assembly-CSharp",
                            "frame": 20,
                            "duration": 1,
                            "enabled": true,
                            "baseDamage": 80.0,
                            "damageType": 1,
                            "spellPowerRatio": 0.6,
                            "targetFilter": 1
                        }
                    ]
                }
            },
            {
                "$id": 5,
                "$type": "2|SkillSystem.Data.SkillTrack, Assembly-CSharp",
                "trackName": "动画轨道",
                "enabled": true,
                "actions": {
                    "$id": 6,
                    "$type": "3|System.Collections.Generic.List`1[[SkillSystem.Actions.ISkillAction, Assembly-CSharp]], mscorlib",
                    "$rlength": 1,
                    "$rcontent": [
                        {
                            "$id": 7,
                            "$type": "7|SkillSystem.Actions.AnimationAction, Assembly-CSharp",
                            "frame": 0,
                            "duration": 30,
                            "enabled": true,
                            "animationClipName": "FireBlast",
                            "crossFadeDuration": 0.1
                        }
                    ]
                }
            }
        ]
    },
    "skillId": "mage-fireball-001"
}
```

## 工作流程

1. **收集需求** - 如果需要，询问澄清性问题
2. **设计轨道** - 规划需要哪些轨道（伤害、动画、音频等）
3. **创建 Action** - 添加合适的 Action 并设置正确的时机
4. **验证** - 确保所有字段都存在且格式正确
5. **保存文件** - 保存到 `Assets/Skills/{技能名称}.json`
6. **说明** - 简要说明配置的关键特性和机制

## 平衡指南

### 伤害技能

| 类型 | 基础伤害 | 法强系数 | 每级成长 | 说明 |
|------|---------|---------|---------|------|
| 基础技能 | 60-100 | 0.4-0.6 | 10-15 | 可频繁释放 |
| 主要技能 | 100-200 | 0.6-0.9 | 15-25 | 中等冷却时间 |
| 终极技能 | 200-400 | 0.8-1.2 | 25-40 | 长冷却时间 |

### 治疗技能

| 类型 | 基础治疗 | 法强系数 | 每级成长 |
|------|---------|---------|---------|
| 基础治疗 | 40-80 | 0.3-0.5 | 8-12 |
| 主要治疗 | 80-150 | 0.5-0.8 | 12-20 |

### 护盾技能

| 类型 | 基础护盾值 | 法强系数 | 生命系数 | 持续时间 |
|------|-----------|---------|---------|----------|
| 基础护盾 | 50-100 | 0.3-0.5 | 0.05-0.10 | 2-4秒 |
| 主要护盾 | 100-200 | 0.5-0.8 | 0.08-0.15 | 3-6秒 |

### 时间指南

| 类型 | 持续时间 | 帧数 @ 30fps |
|------|----------|--------------|
| 瞬发 | 0.1-0.3秒 | 3-9 |
| 快速 | 0.25-0.5秒 | 8-15 |
| 标准 | 0.5-1.5秒 | 15-45 |
| 引导 | 2-4秒 | 60-120 |

## 输出要求

生成技能后：
1. 将 JSON 文件保存到合适的位置
2. 解释关键特性和机制
3. 提供测试建议
4. 说明任何特殊注意事项或边界情况

## 使用参数

如果用户提供了技能描述作为参数：
```
/skill-generate 创建一个火球技能造成100点魔法伤害
```

使用 `$ARGUMENTS` 作为技能描述的基础。
