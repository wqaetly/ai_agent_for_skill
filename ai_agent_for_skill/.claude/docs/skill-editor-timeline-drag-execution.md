# 技能编辑器拖动标尺执行功能

## 功能概述

实现了在技能编辑器中拖动时间轴标尺时实时执行技能逻辑的功能，让编辑时的预览更加直观。

## 实现原理

### 核心修改

在 `SkillEditorWindow.SetCurrentFrame` 方法中添加了拖动模式下的技能执行逻辑：

```csharp
public void SetCurrentFrame(int newFrame)
{
    currentFrame = Mathf.Clamp(newFrame, 0, currentSkillData.totalDuration);

    // Sync with skill executor if it's running
    if (skillExecutor != null && skillExecutor.IsExecuting)
    {
        skillExecutor.SetFrame(currentFrame);
    }
    else
    {
        // When not in playback mode, manually trigger frame processing for drag preview
        // This ensures OnEnter/OnTick/OnExit are called during timeline dragging
        skillExecutor?.SetFrame(currentFrame);
    }

    playbackController?.UpdateFrameControls(currentSkillData, currentFrame);
    timelineController?.UpdatePlayhead(currentFrame);
    timelineController?.UpdateCursorRuler(currentFrame);
}
```

### 执行流程

1. **拖动标尺触发** → `SetCurrentFrame` 被调用
2. **非播放模式检测** → 检查 `skillExecutor.IsExecuting` 状态
3. **手动执行触发** → 调用 `skillExecutor.SetFrame(currentFrame)`
4. **生命周期执行** → `EditorSkillExecutor.ProcessFrame()` 处理：
   - `OnEnter()` - 进入动作
   - `OnTick()` - 每帧更新
   - `OnExit()` - 退出动作

## 技术特点

### 数据驱动设计
- 完全基于当前的技能数据状态
- 自动处理 action 的增删改情况
- 无需额外的手动状态管理

### 生命周期完整性
- 确保所有生命周期方法正确调用
- 正确处理动作的进入和退出状态
- 保持与播放模式一致的执行逻辑

### 性能优化
- 只在帧变化时触发执行
- 避免不必要的重复计算
- 与现有的执行器共享逻辑

## 使用效果

### 编辑时预览
- 拖动标尺时实时看到技能效果
- 动作的视觉反馈（高亮、状态变化）
- 调试信息的实时输出

### 调试便利性
- 可以逐帧检查技能逻辑
- 快速定位动作执行问题
- 直观的动作生命周期观察

## 兼容性

### 向后兼容
- 不影响现有的播放功能
- 保持所有现有API不变
- 与所有Action类型兼容

### 向前扩展
- 为未来的实时预览功能奠定基础
- 支持更复杂的执行场景
- 易于集成新的Action类型

## 注意事项

1. **性能考虑**：频繁拖动可能产生较多计算，但Unity Editor环境通常可以承受
2. **状态一致性**：确保拖动过程中的状态与播放模式一致
3. **错误处理**：继承现有的错误处理机制，确保稳定性

## 测试验证

编译通过，无编译错误，功能已集成到现有系统中。

---

## 文档索引 (Documentation Index)

### 技能系统 (Skill System)
- [Timeline-Based Skill Editor](.claude/docs/timeline-skill-editor.md) - 基于时间轴的技能编辑器系统，支持JSON序列化和运行时播放
- [Skill Editor UI Elements Refactor](.claude/docs/skill-editor-ui-elements-refactor.md) - 技能编辑器UI Elements重构，解决拖动、美观度和功能缺失问题
- [Skill Editor UI Fixes](.claude/docs/skill-editor-ui-fixes.md) - 技能编辑器UI修复，解决Track高度对齐、滚动条、缩放和Action管理问题
- [Skill Editor Toolbar Improvements](.claude/docs/skill-editor-toolbar-improvements.md) - 技能编辑器Toolbar优化，改进Frame/Duration控件体验和Action创建指导
- [Skill Editor UI Layout Improvements](.claude/docs/skill-editor-ui-layout-improvements.md) - 技能编辑器UI布局改进，优化工具栏布局、统一控件样式、增强Track高度和右键菜单功能
- [Skill Editor Cursor Ruler and Layout Fixes](.claude/docs/skill-editor-cursor-ruler-and-layout-fixes.md) - 技能编辑器游标尺和布局修复，添加可拖拽游标尺、修复右键菜单、优化Add Track按钮位置
- [Skill Editor Timeline Ruler Improvements](.claude/docs/skill-editor-timeline-ruler-improvements.md) - 基于Unity Timeline源码分析的时间轴标尺和缩放系统专业化改进
- [Remove Track Color Feature](.claude/docs/remove-track-color-feature.md) - 移除Track颜色功能，Action颜色改为基于类型显示，简化UI和数据结构
- [Timeline Scroller Removal and Zoom Layout](.claude/docs/timeline-scroller-optimization.md) - 移除问题滚动条，将Zoom控件重新布局到toolbar，简化UI设计
- [Skill Editor Layout Improvements](.claude/docs/skill-editor-layout-improvements.md) - 技能编辑器布局重大改进：Inspector面板移至右侧，添加ScrollView支持和水平滚动条
- [Action Inspector Custom Fields Fix](.claude/docs/action-inspector-custom-fields-fix.md) - Action Inspector自定义字段显示修复，解决只显示基础字段而不显示Action子类自定义字段的问题
- [Skill Editor Execution System](.claude/docs/skill-editor-execution-system.md) - 技能编辑器执行系统，实现完整的生命周期管理（OnEnter/OnTick/OnExit）和实时技能执行功能
- [Skill Editor Timeline Drag Execution](.claude/docs/skill-editor-timeline-drag-execution.md) - 技能编辑器拖动标尺执行功能，支持在拖动时间轴时实时执行技能逻辑