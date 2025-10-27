# 泰达米尔嗜血杀戮技能配置

## 技能信息

**英雄**: 泰达米尔（Tryndamere）
**技能名称**: 嗜血杀戮（Bloodlust）
**快捷键**: Q
**技能ID**: `tryndamere-bloodlust-001`

## 技能描述

### 被动效果（不在Timeline中实现）
泰达米尔嗜血成性，获得基础攻击力加成，并根据已损失生命值百分比获得额外攻击力：
- 基础攻击力：5/10/15/20/25
- 每1%已损失生命值额外攻击力：0.15/0.25/0.35/0.45/0.55

> **注**: 被动效果应由角色的永久属性系统管理，不在技能Timeline中配置。

### 主动效果（Timeline实现）
泰达米尔消耗他的怒气，回复生命值：
- **基础回复**: 30/40/50/60/70 + 30%法术强度
- **每怒气回复**: 0.5/0.95/1.4/1.85/2.3 + 1.2%法术强度

## Timeline配置

### 基本信息
- **总时长**: 60帧（2秒）
- **帧率**: 30 FPS
- **轨道数量**: 3条

### Track 1: Resource Heal Track（资源治疗轨道）

**Action**: ResourceDependentHealAction

| 参数 | 值 | 说明 |
|------|-----|------|
| frame | 0 | 技能开始时立即触发 |
| duration | 15帧 | 治疗效果持续0.5秒 |
| resourceType | Rage (2) | 消耗怒气 |
| consumeMode | All (0) | 消耗所有怒气 |
| healType | Health (0) | 回复生命值 |
| baseHeal | 30.0 | 基础回复30点生命 |
| perResourceHeal | 0.5 | 每点怒气回复0.5生命 |
| scaleWithLevel | true | 随技能等级缩放 |
| baseHealPerLevel | 10.0 | 每级基础回复+10 |
| perResourceHealPerLevel | 0.45 | 每级每怒气回复+0.45 |
| baseSpellPowerRatio | 0.3 | 基础回复享受30%法强 |
| perResourceSpellPowerRatio | 0.012 | 每怒气回复享受1.2%法强 |
| effectColor | (1, 0.3, 0.3, 1) | 红色特效（怒气主题） |

### Track 2: Animation Track（动画轨道）

**Action**: AnimationAction

| 参数 | 值 | 说明 |
|------|-----|------|
| frame | 0 | 技能开始时播放动画 |
| duration | 30帧 | 动画持续1秒 |
| animationClipName | "TryndamereBloodlust" | 动画片段名称 |
| crossFadeDuration | 0.1 | 0.1秒过渡时间 |

### Track 3: Audio Track（音频轨道）

**Action**: AudioAction

| 参数 | 值 | 说明 |
|------|-----|------|
| frame | 0 | 技能开始时播放音效 |
| duration | 30帧 | 音效持续1秒 |
| audioClipName | "tryndamere_bloodlust" | 音频片段名称 |
| volume | 0.9 | 音量90% |
| is3D | true | 3D音效 |
| fadeOutTime | 0.2 | 0.2秒淡出 |

## 技能效果计算示例

### 场景1: 1级技能，满怒气（100），100法强

```
基础回复 = 30 + 0 + (100 × 0.3) = 60
每怒气回复 = 0.5 + 0 + (100 × 0.012) = 1.7
总回复 = 60 + (1.7 × 100) = 230点生命值
```

### 场景2: 5级技能，满怒气（100），200法强

```
基础回复 = 70 + (10 × 4) + (200 × 0.3) = 70 + 40 + 60 = 170
每怒气回复 = 2.3 + (0.45 × 4) + (200 × 0.012) = 2.3 + 1.8 + 2.4 = 6.5
总回复 = 170 + (6.5 × 100) = 820点生命值
```

### 场景3: 3级技能，50怒气，150法强

```
基础回复 = 50 + (10 × 2) + (150 × 0.3) = 50 + 20 + 45 = 115
每怒气回复 = 1.4 + (0.45 × 2) + (150 × 0.012) = 1.4 + 0.9 + 1.8 = 4.1
总回复 = 115 + (4.1 × 50) = 320点生命值
```

## 技能数据表

### 各等级基础数值对比（无法强）

| 技能等级 | 基础回复 | 每怒气回复 | 满怒气总回复 |
|----------|----------|-----------|-------------|
| 1 | 30 | 0.50 | 80 |
| 2 | 40 | 0.95 | 135 |
| 3 | 50 | 1.40 | 190 |
| 4 | 60 | 1.85 | 245 |
| 5 | 70 | 2.30 | 300 |

### 法强加成对比（满怒气）

| 法强 | 1级回复 | 3级回复 | 5级回复 |
|------|---------|---------|---------|
| 0 | 80 | 190 | 300 |
| 100 | 230 | 400 | 570 |
| 200 | 380 | 610 | 840 |
| 300 | 530 | 820 | 1110 |

## 配置文件位置

**JSON配置**: `Assets/Skills/TryndamereBloodlust.json:1`

## 使用说明

### 在编辑器中加载技能

1. 打开技能编辑器
2. 点击 "Load Skill"
3. 选择 `TryndamereBloodlust.json`
4. 技能配置将自动加载并展示在Timeline中

### 修改技能参数

如需调整技能数值：
1. 在Timeline中选择 "Resource Heal Track"
2. 点击第一个Action（ResourceDependentHealAction）
3. 在右侧Inspector面板中修改参数
4. 保存技能配置

## 设计要点

### 1. 资源管理
- 怒气值范围：0-100
- 消耗所有当前怒气
- 怒气越高，治疗量越大

### 2. 缩放机制
- **技能等级缩放**: 线性增长，每级都有显著提升
- **法术强度缩放**: 基础部分享受30%法强，每怒气部分享受1.2%法强
- **双重缩放设计**: 确保技能在各个阶段都有价值

### 3. 平衡性考虑
- 低怒气时有基础回复保底（30-70点）
- 高怒气时回复量显著提升
- 法强加成使AP流泰达米尔成为可能

## 技术实现

### 关键Action
- **ResourceDependentHealAction**: 核心治疗逻辑
  - 位置: `Assets/Scripts/SkillSystem/Actions/ResourceDependentHealAction.cs:1`
  - 文档: [ResourceDependentHealAction文档](./resource-dependent-heal-action.md)

### 资源类型扩展
为支持怒气系统，在ResourceType枚举中新增了Rage类型：
- 位置: `Assets/Scripts/SkillSystem/Actions/ResourceAction.cs:535`

## 相关文档

- [ResourceDependentHealAction行为文档](./resource-dependent-heal-action.md)
- [Timeline技能编辑器](./timeline-skill-editor.md)
- [锐雯折断之翼技能](./riven-broken-wings-skill.md) - 复杂技能配置参考

## 后续扩展建议

### 1. 被动效果实现
建议在角色属性系统中实现被动效果，监听生命值变化并动态调整攻击力。

### 2. 怒气生成机制
需要实现怒气的生成逻辑：
- 普攻生成怒气
- 受到伤害生成怒气
- 暴击额外生成怒气

### 3. UI显示
- 怒气条显示
- 技能回复量预览
- 当前可回复生命值提示

### 4. 音效和特效
配置文件中引用的资源需要实际创建：
- `TryndamereBloodlust` 动画片段
- `tryndamere_bloodlust` 音频文件
- 怒气消耗和生命回复的粒子特效
