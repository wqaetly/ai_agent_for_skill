# 技能训练场系统 (Training Ground System)

## 概述

训练场系统是一个**零美术资源依赖**的技能效果可视化方案，用于在Unity中直观地演示技能系统的效果。类似"打木桩"的训练场景，可以实时查看伤害数字、技能范围、Buff状态、时间轴等全方位的技能表现。

### 核心特性

- ✅ **零美术资源** - 全部使用Unity基础几何体和纯色材质
- ✅ **数据可视化** - 伤害数字、血条、Buff图标、技能时间轴
- ✅ **完整技能效果** - 支持伤害、治疗、Buff、投射物、AOE、位移等24种Action
- ✅ **解耦设计** - 不修改原有SkillSystem代码，通过事件系统集成
- ✅ **热插拔** - 后续可无缝替换为真实模型和粒子特效

---

## 系统架构

```
TrainingGround/
├── Entity/              # 实体系统
│   ├── IEntity.cs                  # 实体接口
│   ├── TrainingDummy.cs            # 训练木桩
│   ├── PlayerCharacter.cs          # 玩家角色
│   └── EntityManager.cs            # 实体管理器（单例）
├── Visualizer/          # 可视化系统
│   ├── ISkillVisualizer.cs         # 可视化器接口
│   ├── SkillVisualizerManager.cs   # 可视化管理器
│   ├── DamageVisualizer.cs         # 伤害可视化
│   ├── HealVisualizer.cs           # 治疗可视化
│   ├── BuffVisualizer.cs           # Buff可视化
│   ├── ProjectileVisualizer.cs     # 投射物可视化
│   ├── AOEVisualizer.cs            # AOE可视化
│   └── MovementVisualizer.cs       # 移动可视化
├── UI/                  # UI系统
│   ├── DamageNumber.cs             # 伤害飘字组件
│   ├── DamageNumberPool.cs         # 飘字对象池
│   ├── EntityHealthBar.cs          # 实体血条
│   ├── BuffIconDisplay.cs          # Buff图标显示
│   └── SkillTimelinePanel.cs       # 技能时间轴面板
└── Runtime/             # 运行时管理
    └── TrainingGroundManager.cs    # 训练场核心管理器
```

---

## 快速开始

### 方式一：一键设置（推荐）

1. **创建空场景** - 新建Unity Scene
2. **添加管理器** - 创建空GameObject，命名为"TrainingGroundManager"
3. **挂载脚本** - 添加`TrainingGroundManager`组件
4. **运行游戏** - 点击Play，系统会自动创建：
   - 玩家角色（蓝色Capsule）
   - 3个训练木桩（灰色Cube）
   - 血条UI
   - 飘字系统
   - 技能时间轴面板

### 方式二：手动配置

#### 1. 创建实体

**玩家角色：**
```csharp
// 创建GameObject
GameObject playerObj = GameObject.CreatePrimitive(PrimitiveType.Capsule);
playerObj.name = "Player";

// 添加组件
var player = playerObj.AddComponent<PlayerCharacter>();
var skillPlayer = playerObj.AddComponent<SkillPlayer>();
var visualizerManager = playerObj.AddComponent<SkillVisualizerManager>();

// 添加血条
GameObject healthBarObj = new GameObject("HealthBar");
healthBarObj.transform.SetParent(playerObj.transform);
var healthBar = healthBarObj.AddComponent<EntityHealthBar>();
healthBar.SetTargetEntity(player);
```

**训练木桩：**
```csharp
// 创建GameObject
GameObject dummyObj = GameObject.CreatePrimitive(PrimitiveType.Cube);
dummyObj.transform.position = new Vector3(0, 0, 5);
dummyObj.transform.localScale = new Vector3(1, 2, 1);

// 添加组件
var dummy = dummyObj.AddComponent<TrainingDummy>();

// 添加血条
GameObject healthBarObj = new GameObject("HealthBar");
healthBarObj.transform.SetParent(dummyObj.transform);
var healthBar = healthBarObj.AddComponent<EntityHealthBar>();
healthBar.SetTargetEntity(dummy);
```

#### 2. 创建UI系统

**飘字系统：**
```csharp
GameObject poolObj = new GameObject("DamageNumberPool");
var pool = poolObj.AddComponent<DamageNumberPool>();
```

**技能时间轴：**
```csharp
// 在ScreenSpace Canvas中创建
GameObject panelObj = new GameObject("SkillTimelinePanel");
panelObj.transform.SetParent(canvas.transform, false);
var timeline = panelObj.AddComponent<SkillTimelinePanel>();
timeline.SetTargetSkillPlayer(skillPlayer);
```

---

## 使用示例

### 播放技能

```csharp
// 获取管理器
var manager = FindObjectOfType<TrainingGroundManager>();

// 从文件播放技能
manager.PlaySkill("Assets/Skills/FlameShockwave.json");

// 或从JSON字符串播放
string json = File.ReadAllText("skill.json");
manager.PlaySkillFromJson(json);
```

### 设置目标

```csharp
// 获取玩家
var player = manager.Player;

// 获取第一个木桩
var dummy = manager.Dummies[0];

// 设置为目标
player.SetTarget(dummy);
```

### 查看统计数据

```csharp
// 打印所有木桩的伤害统计
manager.PrintDummyStatistics();

// 输出示例：
// Dummy 1:
//   Total Damage: 3500
//   Hit Count: 5
//   Avg Damage/Hit: 700
//   DPS: 1166
```

### 重置场景

```csharp
// 重置所有木桩
manager.ResetAllDummies();

// 重置玩家
manager.ResetPlayer();
```

---

## 可视化效果说明

### 1. 伤害数字飘字

- **位置** - 目标头顶飘起
- **颜色编码**：
  - 橙色 - 物理伤害
  - 蓝色 - 魔法伤害
  - 黄色 - 纯粹伤害
  - 绿色 - 治疗
- **大小** - 暴击时字体更大
- **动画** - 向上飘动 + 淡出

### 2. 血条/护盾条

- **绿色条** - 生命值
- **青色条** - 护盾值（有护盾时显示）
- **数字** - 当前值/最大值
- **平滑动画** - 数值变化时平滑过渡

### 3. Buff图标

- **颜色编码**：
  - 绿色背景 - 增益Buff
  - 红色背景 - 减益Buff
  - 灰色背景 - 中性Buff
- **堆叠数** - 右下角显示层数
- **倒计时** - 中心显示剩余秒数

### 4. 技能时间轴

- **进度条** - 显示当前帧/总帧数
- **Action标记** - 彩色竖线标记各Action触发时间点
  - 红色 - Damage
  - 绿色 - Heal
  - 黄色 - Buff
  - 橙色 - Projectile
  - 紫色 - AOE
  - 青色 - Movement

### 5. 技能效果

**投射物：**
- 橙色Sphere + TrailRenderer
- 自动寻找目标
- 命中时闪光特效

**AOE范围：**
- 半透明红色圆环
- 扩散动画（放大 → 保持 → 淡出）
- 地面投影

**位移效果：**
- 青色虚线轨迹预测
- Dash时的残影效果
- 平滑过渡动画

---

## 扩展现有Action的可视化

系统已自动为以下Action类型提供可视化：
- ✅ DamageAction
- ✅ HealAction
- ✅ BuffAction
- ✅ ProjectileAction
- ✅ AreaOfEffectAction
- ✅ MovementAction

### 为新Action添加可视化

1. **创建Visualizer类**：

```csharp
using TrainingGround.Visualizer;
using SkillSystem.Actions;

public class MyCustomVisualizer : SkillVisualizerBase<MyCustomAction>
{
    protected override void OnVisualizeEnter(MyCustomAction action, GameObject caster)
    {
        // Action开始时的可视化
        Debug.Log("MyCustomAction started!");
    }

    protected override void OnVisualizeTick(MyCustomAction action, GameObject caster, int relativeFrame)
    {
        // 每帧更新的可视化
    }

    protected override void OnVisualizeExit(MyCustomAction action, GameObject caster)
    {
        // Action结束时的清理
    }
}
```

2. **注册Visualizer**：

在`SkillVisualizerManager.RegisterAllVisualizers()`中添加：
```csharp
RegisterVisualizer(new MyCustomVisualizer());
```

---

## 技术细节

### 事件驱动架构

```
SkillPlayer (播放技能)
    ↓ 事件: OnActionExecuted
SkillVisualizerManager (分发可视化)
    ↓ 调用
DamageVisualizer (执行伤害逻辑)
    ↓ 应用到
TrainingDummy (扣血、显示飘字)
```

### 数据流

```
SkillData.json → SkillPlayer → Action.Execute()
                      ↓
              SkillVisualizerManager
                      ↓
          找到对应的Visualizer
                      ↓
         获取目标实体 (EntityManager)
                      ↓
         应用效果 (TakeDamage/Heal/AddBuff)
                      ↓
         触发UI显示 (DamageNumberPool)
```

### 性能优化

- **对象池** - DamageNumber使用对象池复用
- **事件解耦** - 避免组件间直接引用
- **按需创建** - UI元素仅在需要时创建
- **自动清理** - Action结束时自动回收资源

---

## 后续升级路径

### 替换为真实美术资源

1. **角色模型** - 替换Capsule为角色Prefab
2. **特效粒子** - 在Visualizer中Instantiate粒子Prefab
3. **UI皮肤** - 替换默认UI为设计师UI

代码**无需修改**，只需在Inspector中指定Prefab即可。

### 集成战斗系统

```csharp
// 将TrainingDummy替换为真实Enemy
public class EnemyCharacter : MonoBehaviour, IEntity
{
    // 实现IEntity接口
    // 技能可视化自动生效
}
```

### 添加AI控制

```csharp
// 木桩可以反击
public class SmartDummy : TrainingDummy
{
    void Update()
    {
        if (IsBeingAttacked())
        {
            // 施放反击技能
            var skillPlayer = GetComponent<SkillPlayer>();
            skillPlayer.PlaySkill();
        }
    }
}
```

---

## 常见问题

### Q: 飘字不显示？
**A:** 检查是否创建了DamageNumberPool组件。可以在Manager的Inspector中查看DamageNumberPool引用。

### Q: 血条不跟随实体？
**A:** 确保EntityHealthBar的targetEntity已设置，且targetTransform不为空。

### Q: 技能无效果？
**A:** 检查：
1. PlayerCharacter是否设置了Target
2. SkillVisualizerManager是否已挂载到Player上
3. 技能JSON文件是否正确加载

### Q: 如何调试可视化？
**A:** 在Visualizer的OnVisualizeEnter中打断点，检查action参数和caster对象。

---

## Inspector快捷菜单

TrainingGroundManager提供右键菜单：
- **Setup Training Ground** - 一键设置训练场
- **Reset All Dummies** - 重置所有木桩
- **Reset Player** - 重置玩家

TrainingDummy提供右键菜单：
- **Reset Dummy** - 重置木桩状态

---

## 性能数据

- **对象池容量** - DamageNumber默认20初始/100最大
- **Buff图标** - 最多显示10个
- **实体查询** - EntityManager使用字典缓存，O(1)查询

---

## 许可和贡献

本系统是技能系统的可视化扩展，完全解耦于核心逻辑，可自由修改和扩展。

**核心设计原则：**
- 简单优于复杂
- 数据驱动优于硬编码
- 可替换优于写死
- 解耦优于耦合

---

## 联系方式

如有问题或建议，请查阅：
- 技能系统核心文档：`Assets/Scripts/SkillSystem/README.md`
- Unity官方文档：https://docs.unity3d.com/
