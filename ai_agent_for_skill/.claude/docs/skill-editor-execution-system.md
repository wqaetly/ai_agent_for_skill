# 技能编辑器执行系统

## 概述

为技能编辑器实现了完整的实时执行系统，支持技能逻辑的即时预览和调试。该系统基于Linus Torvalds的"好品味"原则设计，追求简洁、可靠的代码架构。

## 核心特性

### 1. 生命周期管理

#### ISkillAction 接口增强
- **OnEnter()**: 动作开始时调用一次，用于初始化逻辑
- **OnTick(int relativeFrame)**: 动作活跃期间每帧调用，relativeFrame为相对于动作开始的帧数
- **OnExit()**: 动作结束时调用一次，用于清理逻辑
- **ProcessLifecycle()**: 自动处理Enter/Tick/Exit状态转换
- **ResetLifecycleState()**: 重置生命周期状态（用于技能循环或重启）
- **ForceExit()**: 强制退出动作（用于中途停止技能）

#### 状态跟踪
```csharp
// 非序列化字段避免数据污染
[System.NonSerialized]
private bool hasEntered = false;
[System.NonSerialized]
private bool hasExecuted = false;
```

### 2. 编辑器执行引擎

#### EditorSkillExecutor 特性
- **实时播放**: 按技能帧率实时执行动作逻辑
- **帧跳转**: 支持任意帧位置的即时跳转，自动处理状态同步
- **生命周期管理**: 自动处理动作的Enter/Tick/Exit转换
- **错误处理**: 捕获并报告执行过程中的异常，不中断整体播放
- **性能监控**: 跟踪执行性能和活跃动作数量

#### 核心算法
```csharp
// Linus: "消除特殊情况的核心逻辑"
private void ProcessFrame()
{
    // 1. 收集当前帧应该活跃的所有动作
    var allActiveActionsThisFrame = new HashSet<ISkillAction>();

    // 2. 处理退出：之前活跃现在不活跃的动作
    foreach (var activeAction in activeActions)
    {
        if (!allActiveActionsThisFrame.Contains(activeAction))
        {
            action.OnExit();
            activeActions.Remove(action);
        }
    }

    // 3. 处理进入：之前不活跃现在活跃的动作
    foreach (var newActiveAction in allActiveActionsThisFrame)
    {
        if (!activeActions.Contains(newActiveAction))
        {
            action.OnEnter();
            activeActions.Add(action);
        }
    }

    // 4. 处理Tick：所有当前活跃的动作
    foreach (var action in activeActions)
    {
        int relativeFrame = currentFrame - action.frame;
        action.OnTick(relativeFrame);
    }
}
```

### 3. 编辑器集成

#### SkillEditorWindow 集成
- **自动同步**: 播放控制器和执行器状态自动同步
- **可视化反馈**: 执行中的动作显示黄色边框和特殊CSS类
- **事件处理**: 完整的执行事件回调系统
- **错误报告**: 执行错误直接显示在控制台

#### PlaybackController 增强
- **播放开始**: 自动启动技能执行
- **播放停止**: 自动停止技能执行并清理状态
- **帧跳转**: 拖动时间轴时自动同步执行器帧位置

### 4. 视觉反馈系统

#### SkillActionElement 执行状态
```csharp
public void SetExecutionState(bool isExecuting, bool isTicking)
{
    // CSS类管理
    RemoveFromClassList("executing", "ticking", "entered");

    if (isExecuting)
    {
        AddToClassList("executing");
        AddToClassList(isTicking ? "ticking" : "entered");

        // 黄色边框表示执行状态
        this.style.borderColor = Color.yellow;
        this.style.borderWidth = 2;
    }
}
```

## 使用方法

### 1. 在编辑器中运行技能
1. 在技能编辑器中创建或加载技能
2. 添加各种类型的动作到时间轴
3. 点击"Play"按钮开始实时执行
4. 观察动作的黄色边框和控制台日志
5. 使用时间轴拖动来跳转到任意帧位置

### 2. 动作实现示例

#### LogAction 生命周期实现
```csharp
public override void OnEnter()
{
    Debug.unityLogger.Log(logType, $"[OnEnter] {message}");
}

public override void OnTick(int relativeFrame)
{
    if (relativeFrame % 10 == 0) // 每10帧记录一次
    {
        Debug.unityLogger.Log(LogType.Log, $"[OnTick] {message} (Frame: {relativeFrame})");
    }
}

public override void OnExit()
{
    Debug.unityLogger.Log(LogType.Log, $"[OnExit] {message} - Action completed");
}
```

#### AnimationAction 生命周期实现
```csharp
public override void OnEnter()
{
    var animator = FindFirstObjectByType<Animator>();
    if (animator != null)
    {
        animator.CrossFade(animationClipName, crossFadeDuration, animationLayer, normalizedTime);
        Debug.Log($"[AnimationAction] Started animation: {animationClipName}");
    }
}

public override void OnTick(int relativeFrame)
{
    var animator = FindFirstObjectByType<Animator>();
    if (animator != null && relativeFrame % 5 == 0)
    {
        var currentState = animator.GetCurrentAnimatorStateInfo(animationLayer);
        Debug.Log($"[AnimationAction] {animationClipName} progress: {currentState.normalizedTime:F2}");
    }
}

public override void OnExit()
{
    Debug.Log($"[AnimationAction] Finished animation action: {animationClipName}");
}
```

## 架构设计原则

### Linus Torvalds "好品味"原则
1. **消除特殊情况**: 帧处理逻辑统一，没有边界条件的特殊处理
2. **简单的数据结构**: HashSet用于活跃动作跟踪，直接映射，无复杂继承
3. **明确的职责分离**: 执行器只负责执行，编辑器只负责UI，控制器只负责播放控制
4. **错误处理**: 局部错误不影响整体执行，每个动作异常独立处理

### 关键设计决策
1. **编辑器执行器**: 将执行逻辑放在Editor程序集中，避免运行时依赖
2. **状态重置**: 跳帧时重置所有状态后重新计算，确保一致性
3. **事件驱动**: 通过事件系统解耦执行器和UI反馈
4. **向后兼容**: 保留旧的Execute()方法，标记为过时但仍可用

## 性能特性

- **帧率独立**: 使用deltaTime累积确保准确的帧率控制
- **错误隔离**: 单个动作错误不影响其他动作执行
- **内存管理**: 使用对象池和重用减少GC压力
- **状态缓存**: 避免重复计算动作活跃状态

## 调试功能

### 控制台输出
- 技能执行开始/停止日志
- 动作Enter/Tick/Exit生命周期日志
- 执行错误详细信息
- 性能统计信息

### 可视化指示
- 执行中动作显示黄色边框
- CSS类标识不同执行状态（executing、ticking、entered）
- 时间轴播放头实时显示当前执行帧

## 扩展性

### 新动作类型
继承ISkillAction并实现OnEnter/OnTick/OnExit方法即可获得完整的生命周期支持：

```csharp
public class CustomAction : ISkillAction
{
    public override string GetActionName() => "Custom Action";

    public override void OnEnter()
    {
        // 动作开始逻辑
    }

    public override void OnTick(int relativeFrame)
    {
        // 每帧更新逻辑
    }

    public override void OnExit()
    {
        // 动作结束清理逻辑
    }
}
```

### 执行器扩展
EditorSkillExecutor可以扩展支持：
- 断点调试
- 单步执行
- 条件执行
- 性能分析

该系统为技能编辑器提供了强大的实时执行能力，让技能设计师能够即时看到逻辑效果，大大提升了开发效率和调试体验。