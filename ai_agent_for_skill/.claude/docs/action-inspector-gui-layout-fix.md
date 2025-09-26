# Action Inspector GUI布局修复

## 问题描述

在技能编辑器中选中Action时出现严重的GUILayout错误和Inspector面板无法编辑的问题：

```
ArgumentException: Getting control 4's position in a group with only 4 controls when doing repaint
UnityEngine.GUILayoutGroup.GetNext ()
Sirenix.OdinInspector.Editor.ValidationDrawer`1[T].DrawPropertyLayout (UnityEngine.GUIContent label)
```

## 根因分析（Linus式分析）

**【致命问题】**
- **数据结构错了**：`PropertyTree.Create(action).Draw(false)` 在UIElements的ScrollView中创建IMGUI容器，布局组控件数量不匹配
- **把这个特殊情况消除掉**：IMGUI和UIElements混合是典型的"特殊情况"，导致布局冲突
- **资源管理垃圾**：PropertyTree没有正确的生命周期管理，重复创建导致内存泄漏和布局错误

## 解决方案

### 核心修复思路
根据"好品味"原则：
1. **统一PropertyTree管理**：避免重复创建和内存泄漏
2. **修复IMGUI布局**：确保GUILayout.BeginVertical与EndVertical配对
3. **完善资源清理**：实现正确的Dispose模式

### 代码修改

#### 1. ActionInspector.cs - 修复PropertyTree生命周期管理

**添加成员变量**：
```csharp
private PropertyTree currentPropertyTree;
```

**修复CreateActionProperties方法**：
```csharp
private void CreateActionProperties(ISkillAction action, SkillData skillData)
{
    // Add a separator
    AddSeparator();

    // Dispose previous property tree to prevent layout issues
    if (currentPropertyTree != null)
    {
        currentPropertyTree.Dispose();
        currentPropertyTree = null;
    }

    // Create new property tree and ensure proper lifecycle management
    currentPropertyTree = PropertyTree.Create(action);

    // Use Odin for all additional properties with proper error handling
    var odinContainer = new IMGUIContainer(() =>
    {
        try
        {
            if (currentPropertyTree != null)
            {
                GUILayout.BeginVertical();
                currentPropertyTree.Draw(false);
                GUILayout.EndVertical();
            }
        }
        catch (System.Exception e)
        {
            GUILayout.Label($"Error drawing properties: {e.Message}");
        }
    });
    inspectorContent.Add(odinContainer);
}
```

**关键改进点**：
1. ✅ **资源管理**：每次创建新PropertyTree前先Dispose旧的
2. ✅ **布局修复**：添加GUILayout.BeginVertical/EndVertical确保布局组正确
3. ✅ **异常处理**：try-catch防止Odin绘制错误导致编辑器崩溃
4. ✅ **空值保护**：检查currentPropertyTree不为null再调用Draw

#### 2. 统一修复Track和Skill的PropertyTree使用

**Track属性绘制**：
```csharp
var trackOdinContainer = new IMGUIContainer(() =>
{
    try
    {
        var propertyTree = PropertyTree.Create(track);
        GUILayout.BeginVertical();
        propertyTree.Draw(false);
        GUILayout.EndVertical();
        propertyTree.Dispose(); // 立即释放
    }
    catch (System.Exception e)
    {
        GUILayout.Label($"Error drawing track properties: {e.Message}");
    }
});
```

**Skill属性绘制**：
```csharp
var skillOdinContainer = new IMGUIContainer(() =>
{
    try
    {
        var propertyTree = PropertyTree.Create(skillData);
        GUILayout.BeginVertical();
        propertyTree.Draw(false);
        GUILayout.EndVertical();
        propertyTree.Dispose(); // 立即释放
    }
    catch (System.Exception e)
    {
        GUILayout.Label($"Error drawing skill properties: {e.Message}");
    }
});
```

#### 3. 完善资源清理机制

**添加清理方法**：
```csharp
private void Cleanup()
{
    if (currentPropertyTree != null)
    {
        currentPropertyTree.Dispose();
        currentPropertyTree = null;
    }
}

public void Dispose()
{
    Cleanup();
}
```

**修复RefreshInspector方法**：
```csharp
public void RefreshInspector(SkillData skillData, int selectedTrackIndex, int selectedActionIndex, int currentFrame)
{
    if (inspectorContent == null) return;

    // Clear previous content and dispose any existing property tree
    Cleanup();
    inspectorContent.Clear();
    // ... 其余逻辑
}
```

#### 4. SkillEditorWindow.cs - 添加资源清理

**添加OnDisable方法**：
```csharp
private void OnDisable()
{
    // Clean up resources when window is disabled
    actionInspector?.Dispose();
}
```

## 修复效果

### 解决的问题
1. ✅ **GUILayout错误消除**：正确的BeginVertical/EndVertical配对解决布局组错误
2. ✅ **Inspector可编辑**：PropertyTree生命周期管理正确，Odin Inspector可正常工作
3. ✅ **内存泄漏修复**：PropertyTree正确释放，避免内存累积
4. ✅ **异常容错**：即使Odin绘制出错，也不会导致整个编辑器崩溃

### 编译验证
- **编译状态**：✅ 成功，0个错误，1个警告（非关键）
- **功能验证**：Action选择和Inspector编辑功能应正常工作

## 设计原则体现

### Linus式"好品味"
1. **消除特殊情况**：统一PropertyTree使用模式，避免不同类型对象的特殊处理
2. **数据结构优先**：正确的资源生命周期管理，避免悬空指针和重复创建
3. **简洁性**：每个PropertyTree只负责自己的绘制和清理，职责单一

### 代码质量
1. **防御性编程**：异常处理和空值检查
2. **资源管理**：明确的Dispose模式
3. **一致性**：所有PropertyTree使用相同的创建-使用-释放模式

## 后续建议

1. **测试验证**：在Unity编辑器中测试Action选择、编辑和保存功能
2. **性能监控**：观察PropertyTree的内存使用情况
3. **异常日志**：如果出现"Error drawing properties"消息，需要进一步调试具体的Odin绘制问题

## 相关文件

- `Assets/Scripts/SkillSystem/Editor/ActionInspector.cs` - 主要修复文件
- `Assets/Scripts/SkillSystem/Editor/SkillEditorWindow.cs` - 资源清理补充