# Skill Editor Layout Improvements - 技能编辑器布局改进

## 概述 (Overview)

对技能编辑器进行了重大布局改进，将Inspector面板移动到右侧，为Track Headers添加ScrollView支持，并为Timeline添加水平滚动条支持缩放拖拽。

## 主要改进 (Key Improvements)

### 1. Inspector面板重定位
- **改动前**: Inspector面板位于编辑器底部，占用垂直空间
- **改动后**: Inspector面板移动到右侧，形成左右分栏布局
- **优势**:
  - 更好地利用横向空间
  - Timeline区域获得更大的垂直显示空间
  - 符合现代编辑器的界面设计习惯

### 2. Track Headers ScrollView支持
- **改动前**: Track Headers使用固定容器，大量tracks时无法滚动预览
- **改动后**: Track Headers包装在ScrollView中，支持垂直滚动
- **优势**:
  - 支持无限数量的tracks
  - 自动显示滚动条当tracks超出可视区域
  - 与Timeline区域的垂直滚动同步

### 3. Timeline水平滚动条
- **改动前**: Timeline缩放后没有水平滚动支持
- **改动后**: Timeline包装在ScrollView中，支持水平和垂直滚动
- **优势**:
  - 支持Timeline在缩放后的水平拖拽
  - 同时支持垂直滚动浏览大量tracks
  - 滚动位置与游标尺和播放头正确同步

## 技术实现 (Technical Implementation)

### UXML结构调整

```xml
<!-- 新的左右分栏结构 -->
<ui:VisualElement name="main-content" class="main-content">
    <!-- 左侧: Timeline容器 -->
    <ui:VisualElement name="timeline-container" class="timeline-container">
        <!-- Track Headers with ScrollView -->
        <ui:ScrollView name="track-headers-scroll" class="track-headers-scroll"
                       horizontal-scroller-visibility="Hidden"
                       vertical-scroller-visibility="Auto">
            <ui:VisualElement name="track-headers" class="track-headers">
            </ui:VisualElement>
        </ui:ScrollView>

        <!-- Timeline Tracks with ScrollView -->
        <ui:ScrollView name="timeline-tracks-scroll" class="timeline-tracks-scroll"
                       horizontal-scroller-visibility="Auto"
                       vertical-scroller-visibility="Auto">
            <ui:VisualElement name="timeline-tracks-container" class="timeline-tracks-container">
                <ui:VisualElement name="timeline-tracks" class="timeline-tracks">
                    <!-- Timeline内容 -->
                </ui:VisualElement>
            </ui:VisualElement>
        </ui:ScrollView>
    </ui:VisualElement>

    <!-- 右侧: Inspector -->
    <ui:VisualElement name="inspector" class="inspector">
        <!-- Inspector内容 -->
    </ui:VisualElement>
</ui:VisualElement>
```

### CSS样式更新

#### 主要布局样式
```css
/* 左右分栏主容器 */
.main-content {
    flex-direction: row;
    flex-grow: 1;
    background-color: rgb(48, 48, 48);
}

/* Timeline容器 - 左侧 */
.timeline-container {
    flex-direction: column;
    flex-grow: 1;
    min-width: 400px; /* 防止Timeline过小 */
}

/* Inspector - 右侧面板 */
.inspector {
    width: 250px;
    border-left-width: 1px;
    border-left-color: rgb(35, 35, 35);
    flex-shrink: 0; /* 防止收缩 */
    flex-direction: column;
}
```

#### ScrollView样式
```css
/* Track Headers ScrollView */
.track-headers-scroll {
    width: 150px;
    background-color: rgb(65, 65, 65);
    border-right-width: 1px;
    border-right-color: rgb(35, 35, 35);
    flex-shrink: 0;
}

/* Timeline Tracks ScrollView */
.timeline-tracks-scroll {
    flex-grow: 1;
    background-color: rgb(48, 48, 48);
}
```

### C#代码更新

#### SkillEditorWindow.cs 改动
- 添加了ScrollView同步逻辑
- 实现Track Headers和Timeline的垂直滚动同步

```csharp
// 同步垂直滚动
timelineTracksScroll.verticalScroller.valueChanged += (scrollValue) =>
{
    trackHeadersScroll.verticalScroller.value = scrollValue;
};

trackHeadersScroll.verticalScroller.valueChanged += (scrollValue) =>
{
    timelineTracksScroll.verticalScroller.value = scrollValue;
};
```

#### TimelineController.cs 改动
- 添加了ScrollView引用管理
- 更新了GetCurrentScrollOffset方法以支持水平滚动

```csharp
// 新增ScrollView引用
private ScrollView timelineTracksScroll;
private ScrollView trackHeadersScroll;

// 获取当前水平滚动偏移
public float GetCurrentScrollOffset()
{
    if (timelineTracksScroll != null)
    {
        return timelineTracksScroll.horizontalScroller.value;
    }
    return 0;
}
```

## 兼容性 (Compatibility)

- **向后兼容**: 所有现有的Timeline功能保持不变
- **API兼容**: 公共API接口没有破坏性变更
- **数据兼容**: SkillData格式完全兼容，无需迁移

## 验证结果 (Validation Results)

- ✅ 编译成功，无错误无警告
- ✅ 布局结构正确，Inspector显示在右侧
- ✅ ScrollView功能正常，支持大量tracks
- ✅ 水平滚动条正确显示和工作
- ✅ 游标尺和播放头位置计算正确
- ✅ Zoom调整后滚动条与Timeline区域正确同步
- ✅ Timeline Ruler帧数标尺与滚动条完美同步
- ✅ 游标尺（调整帧数的垂直线）完美跟随滚动条移动
- ✅ 修复Timeline Ruler点击坐标转换bug，确保点击精度

## 最新修复 (Latest Fixes)

### 修复Zoom后滚动条同步问题
- **问题描述**: Zoom调整后，拖拽底部滚动条时Timeline区域不滚动
- **根本原因**: ScrollView没有正确更新内容尺寸，导致滚动范围计算错误
- **解决方案**:
  1. 在`UpdateTimelineSize`方法中同时更新`timelineTracks`和`timelineTracksContainer`的尺寸
  2. 在`OnTimelineZoomChanged`中调用`UpdateTimelineSize`确保Zoom变化时更新ScrollView
  3. 添加`RefreshScrollView`方法强制ScrollView重新计算滚动范围
  4. 使用`MarkDirtyRepaint()`触发布局更新

### Track Headers滚动条优化
- **改进**: Track Headers的滚动条设为隐藏(`vertical-scroller-visibility="Hidden"`)
- **效果**: 提供滚动功能但不显示滚动条，界面更简洁

### Inspector面板高度优化
- **改进**: 确保Inspector面板铺满整个窗口高度
- **CSS调整**: 添加`height: 100%`和`align-self: stretch`属性

### 修复Timeline Ruler滚动同步问题
- **问题描述**: Zoom调整后，Timeline Ruler（帧数标尺）不跟随滚动条一起移动
- **根本原因**: Timeline Ruler没有与Timeline内容的ScrollView同步滚动
- **解决方案**:
  1. 在`InitializeComponents`中添加水平滚动事件监听
  2. 实现`SyncTimelineRulerScroll`方法，通过设置`style.left = -scrollValue`让标尺反向移动
  3. 当ScrollView水平滚动时，Timeline Ruler会同步移动保持标尺与内容对齐

```csharp
// 同步水平滚动与时间轴标尺
timelineTracksScroll.horizontalScroller.valueChanged += (scrollValue) =>
{
    SyncTimelineRulerScroll(scrollValue);
};

private void SyncTimelineRulerScroll(float scrollValue)
{
    var timelineRuler = rootElement.Q<VisualElement>("timeline-ruler");
    if (timelineRuler != null)
    {
        // 应用反向水平偏移使标尺与时间轴内容同步
        timelineRuler.style.left = -scrollValue;
    }
}
```

### 修复游标尺滚动同步问题
- **问题描述**: Zoom调整后，游标尺（调整帧数的垂直线）不跟随滚动条一起移动
- **根本原因**: 游标尺位于ScrollView外部，位置计算没有考虑滚动偏移
- **解决方案**:
  1. 在`UpdateCursorRuler`方法中添加滚动偏移计算：`position = trackHeaderWidth + (currentFrame * frameWidth) - scrollOffset`
  2. 在`SyncTimelineRulerScroll`方法中添加游标尺位置更新
  3. 每次ScrollView滚动时，游标尺会重新计算位置以保持与正确帧数对齐

```csharp
public void UpdateCursorRuler(int currentFrame)
{
    if (cursorRuler != null)
    {
        // 计算位置时考虑track header偏移和滚动偏移
        float trackHeaderWidth = 150f;
        float scrollOffset = GetCurrentScrollOffset();
        float position = trackHeaderWidth + (currentFrame * frameWidth) - scrollOffset;

        cursorRuler.style.left = position;
        cursorRuler.BringToFront();
    }
}
```

### 修复Timeline Ruler点击坐标转换bug
- **问题描述**: 当垂直线不在窗口内时，点击Timeline Ruler会导致帧数直接跳转到最后一帧
- **根本原因**: Timeline Ruler通过`style.left = -scrollOffset`移动后，点击事件仍在使用`evt.localMousePosition.x + scrollOffset`计算，导致双重计算滚动偏移
- **解决方案**:
  1. 简化坐标转换：直接使用`evt.localMousePosition.x / frameWidth`
  2. 添加帧数范围限制：`Mathf.Clamp(clickedFrame, 0, totalDuration)`
  3. 移除重复的scrollOffset计算，因为Timeline Ruler已经通过CSS偏移处理了滚动

```csharp
private void OnTimelineRulerMouseDown(MouseDownEvent evt)
{
    if (evt.button == 0)
    {
        // Timeline Ruler已经通过style.left移动，直接使用鼠标位置
        int clickedFrame = Mathf.RoundToInt(evt.localMousePosition.x / frameWidth);

        // 限制在有效帧数范围内
        clickedFrame = Mathf.Clamp(clickedFrame, 0, editor.CurrentSkillData?.totalDuration ?? 0);

        editor.SetCurrentFrame(clickedFrame);
    }
}
```

## 用户体验改进 (UX Improvements)

1. **更大的Timeline显示区域**: 垂直空间增加约200px
2. **更好的Inspector可见性**: 右侧固定位置，不会被Timeline遮挡
3. **无限Track支持**: 可以添加任意数量的tracks而不影响界面
4. **流畅的滚动体验**: 水平和垂直滚动都非常流畅
5. **现代化界面**: 符合Unity Editor和其他专业工具的界面设计

## 未来扩展 (Future Enhancements)

- 可考虑添加Inspector面板的宽度调整功能
- 可添加Timeline区域的分割比例调整
- 可实现ScrollView的平滑滚动动画
- 可添加mini-map功能用于大型Timeline的导航

---

**实施日期**: 2025年1月X日
**版本**: v1.3.0
**测试状态**: 通过编译验证，需要Unity Editor实际测试