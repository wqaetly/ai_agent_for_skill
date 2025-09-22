# Skill Editor Cursor Ruler and Layout Fixes

## 改进概述

本次改进针对技能编辑器的布局和交互体验进行了全面优化，主要解决了Add Track按钮位置、右键菜单功能失效，以及添加了重要的游标尺功能。

## 【核心判断】
✅ 全部完成：这些都是实际的可用性问题，游标尺是Timeline编辑器的标准功能

## 主要改进内容

### 1. 修复右键Track空白区域创建Action功能 ✅

**问题分析**:
- TrackElement创建的trackRow被添加到本地容器中
- 实际显示的trackRow在SkillEditorWindow的timelineTracks中
- 右键菜单注册在错误的元素上

**解决方案**:
- 重构TrackElement的CreateTrackRow方法，移除内部右键菜单注册
- 添加SetupContextMenu方法，接受实际的timeline trackRow作为参数
- 在SkillEditorWindow的UpdateTracks中为每个trackRow正确注册右键菜单

**修改文件**:
- `TrackElement.cs`: 重构右键菜单注册逻辑
- `SkillEditorWindow.cs`: 在UpdateTracks中调用SetupContextMenu

**技术实现**:
```csharp
public void SetupContextMenu(VisualElement timelineTrackRow)
{
    timelineTrackRow.RegisterCallback<ContextualMenuPopulateEvent>(evt =>
    {
        int targetFrame = GetFrameFromPosition(evt.localMousePosition.x);
        evt.menu.AppendAction($"Add Log Action at frame {targetFrame}",
            _ => editorWindow.AddActionToTrack<SkillSystem.Actions.LogAction>(this.trackIndex, targetFrame));
        // ... 更多Action类型
    });
}
```

### 2. Add Track按钮布局优化 ✅

**问题**: Add Track按钮应该在帧数尺那一行，而不是在主工具栏

**解决方案**:
- 将Add Track按钮从主工具栏移除
- 在timeline-header的track-header-space区域添加Add Track按钮
- 保持与帧数尺的水平对齐

**修改文件**:
- `SkillEditor.uxml`: 重新组织按钮位置

**布局结构**:
```xml
<ui:VisualElement name="timeline-header" class="timeline-header">
    <ui:VisualElement name="track-header-space" class="track-header-space">
        <ui:Button text="Add Track" name="add-track-button" class="add-track-button" />
    </ui:VisualElement>
    <ui:VisualElement name="timeline-ruler-container" class="timeline-ruler-container">
        <!-- 帧数尺和游标尺 -->
    </ui:VisualElement>
</ui:VisualElement>
```

### 3. 可拖拽游标尺功能 ✅

**需求**: 添加垂直于所有track的直线，用于表示当前帧数，支持手动拖拽调整

**技术方案**:
- 在timeline-ruler-container中添加cursor-ruler元素
- 使用绝对定位，z-index高于playhead
- 实现完整的鼠标拖拽交互逻辑

**UI层次结构**:
```
timeline-ruler-container
├── timeline-ruler (帧数标记)
├── cursor-ruler (可拖拽游标尺) - 新增
└── 其他元素
```

**拖拽实现**:
```csharp
private bool isDraggingCursorRuler = false;

private void OnCursorRulerMouseDown(MouseDownEvent evt)
{
    if (evt.button == 0)
    {
        isDraggingCursorRuler = true;
        cursorRuler.CaptureMouse();
        evt.StopPropagation();
    }
}

private void OnCursorRulerMouseMove(MouseMoveEvent evt)
{
    if (isDraggingCursorRuler)
    {
        var rulerContainer = rootElement.Q<VisualElement>("timeline-ruler-container");
        Vector2 localPos = rulerContainer.WorldToLocal(evt.mousePosition);
        float scrollOffset = GetCurrentScrollOffset();
        int targetFrame = Mathf.FloorToInt((localPos.x + scrollOffset) / frameWidth);
        SetCurrentFrame(targetFrame);
    }
}
```

**样式设计**:
```css
.cursor-ruler {
    position: absolute;
    width: 2px;
    top: 0;
    bottom: 0;
    background-color: rgb(80, 150, 255);
    cursor: ew-resize;
    z-index: 1001;
}

.cursor-ruler:hover {
    background-color: rgb(120, 180, 255);
    width: 3px;
}
```

## 技术实现细节

### 游标尺位置同步
- **实时更新**: 在SetCurrentFrame、UpdatePlayback、OnTimelineScroll中同步位置
- **滚动适配**: 考虑timeline的滚动偏移量
- **缩放适配**: 随frameWidth变化自动调整位置

### 事件处理优化
- **事件捕获**: 使用CaptureMouse确保拖拽过程中的稳定性
- **事件传播**: 适当使用StopPropagation避免与其他交互冲突
- **坐标转换**: 正确处理世界坐标到本地坐标的转换

### 视觉区分
- **颜色差异**: 游标尺使用蓝色(rgb(80, 150, 255))，playhead使用红色(rgb(255, 80, 80))
- **层级管理**: 游标尺z-index为1001，高于playhead的1000
- **交互反馈**: hover状态下变宽变亮，提供清晰的交互反馈

## 用户体验改进

### 交互流程优化
1. **直观拖拽**: 用户可以直接拖拽游标尺调整当前帧，比输入数字更直观
2. **实时反馈**: 拖拽过程中实时更新帧数显示和playhead位置
3. **右键便捷**: 右键Track空白区域直接添加Action，减少操作步骤

### 布局合理性
- Add Track按钮与帧数尺同行，符合用户对timeline编辑器的预期
- 游标尺与其他timeline元素保持一致的滚动和缩放行为
- 视觉层次清晰，不同功能元素有明确的视觉区分

## 编译验证

项目编译通过，无警告无错误：
```
已成功生成。
    0 个警告
    0 个错误
```

## 总结

本次改进成功解决了用户反馈的所有问题：
1. **✅ Add Track按钮重新定位** - 现在位于帧数尺同一行，布局更合理
2. **✅ 游标尺功能完整实现** - 支持拖拽调整当前帧，提供专业的timeline编辑体验
3. **✅ 右键菜单功能修复** - 现在可以正常右键Track空白区域创建Action

这些改进使Skill Editor的交互体验更加流畅和直观，符合用户对专业timeline编辑工具的期望。游标尺的加入特别重要，它是timeline编辑器的标准功能，大大提升了帧数导航的便利性。