# Action Inspector 自定义字段显示修复

## 问题描述

Action Inspector只显示基础字段（frame、duration、enabled），没有显示Action子类的自定义字段，如LogAction的message和logType、CollisionAction的shape、position、size等字段。

## 根源分析

### 原有代码问题

```csharp
private bool HasCustomProperties(ISkillAction action)
{
    // 检查是否有ShowInInspectorAttribute标记的属性
    return properties.Any(p =>
        !basicProperties.Contains(p.Name.ToLower()) &&
        p.CanWrite &&
        p.GetCustomAttributes(typeof(ShowInInspectorAttribute), true).Length > 0);
}
```

**问题1：错误的属性检测**
- 只检查有`ShowInInspectorAttribute`的属性
- 但实际Action类使用的是Odin的`LabelText`、`MinValue`等属性
- 导致所有自定义字段都被忽略

**问题2：过于复杂的反射逻辑**
- 试图精确判断哪些属性是"自定义"的
- 容易遗漏各种Odin特性标记的字段

## 解决方案

### 最终方案：直接显示Odin Inspector

```csharp
// 移除HasCustomProperties方法，直接显示Odin Inspector
var odinContainer = new IMGUIContainer(() =>
{
    var propertyTree = PropertyTree.Create(action);
    propertyTree.Draw(false);
});
inspectorContent.Add(odinContainer);
```

**核心思路：**
- 既然所有Action都需要显示自定义字段，何必判断？
- Odin Inspector智能处理：已有UI的字段会被跳过，只显示新字段
- 代码更简洁，逻辑更清晰
- 无需维护复杂的反射判断代码

## 修复效果

### 修复前
- LogAction：只显示frame、duration、enabled
- CollisionAction：只显示frame、duration、enabled
- AnimationAction：只显示frame、duration、enabled

### 修复后
- LogAction：显示基础字段 + message（文本框）+ logType（枚举下拉）
- CollisionAction：显示基础字段 + shape（枚举）+ position（Vector3）+ size（Vector3）+ layerMask（LayerMask）+ damage（数值）
- AnimationAction：显示基础字段 + 所有动画相关的自定义字段

## 技术优势

1. **简化逻辑** - 从复杂的反射检查变为简单的类型判断
2. **兼容性强** - 支持所有Odin特性（LabelText、MinValue、MultiLineProperty等）
3. **易维护** - 新增Action类型无需修改Inspector代码
4. **性能优化** - 减少不必要的反射操作

## 相关文件

- `Assets/Scripts/SkillSystem/Editor/ActionInspector.cs` - 修复HasCustomProperties方法
- `Assets/Scripts/SkillSystem/Actions/LogAction.cs` - 使用LabelText、MultiLineProperty特性
- `Assets/Scripts/SkillSystem/Actions/CollisionAction.cs` - 使用LabelText、MinValue特性