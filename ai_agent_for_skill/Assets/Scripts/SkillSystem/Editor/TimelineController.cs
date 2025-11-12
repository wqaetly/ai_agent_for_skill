using UnityEngine;
using UnityEngine.UIElements;
using UnityEditor;
using System.Collections.Generic;
using System.Linq;
using SkillSystem.Data;
using SkillSystem.Actions;

namespace SkillSystem.Editor
{
    /// <summary>
    /// 时间轴控制器 - 负责时间轴UI的渲染和交互
    /// 职责：标尺显示、缩放控制、滚动管理、游标操�?
    /// </summary>
    public class TimelineController
    {
        private readonly SkillEditorWindow editor;

        // Timeline settings
        private float baseFrameWidth = 20f;
        private float frameWidth = 20f;
        private float trackHeight = 30f;
        private float zoomLevel = 1.0f;

        // UI Elements
        private Slider zoomSlider;
        private Button fitButton;
        private VisualElement timelineRuler;
        private VisualElement timelineTracks;
        private VisualElement timelineTracksContainer;
        private VisualElement playhead;
        private VisualElement frameLines;
        private VisualElement cursorRuler;
        private ScrollView timelineTracksScroll;
        private ScrollView trackHeadersScroll;

        // State
        private bool isUpdatingZoom = false;
        private bool isDraggingCursorRuler = false;
        private bool isDraggingFromRuler = false;

        public float FrameWidth => frameWidth;
        public float TrackHeight => trackHeight;

        public TimelineController(SkillEditorWindow editor)
        {
            this.editor = editor;
        }

        public void Initialize(VisualElement rootElement)
        {
            // Get UI element references
            zoomSlider = rootElement.Q<Slider>("zoom-slider");
            fitButton = rootElement.Q<Button>("fit-button");
            timelineRuler = rootElement.Q<VisualElement>("timeline-ruler");
            timelineTracks = rootElement.Q<VisualElement>("timeline-tracks");
            timelineTracksContainer = rootElement.Q<VisualElement>("timeline-tracks-container");
            playhead = rootElement.Q<VisualElement>("playhead");
            frameLines = rootElement.Q<VisualElement>("frame-lines");
            cursorRuler = rootElement.Q<VisualElement>("cursor-ruler");

            // Get new ScrollView references
            timelineTracksScroll = rootElement.Q<ScrollView>("timeline-tracks-scroll");
            trackHeadersScroll = rootElement.Q<ScrollView>("track-headers-scroll");

            ValidateCursorRuler(rootElement);
            BindEvents();
        }

        private void ValidateCursorRuler(VisualElement rootElement)
        {
            if (cursorRuler == null)
            {
                // Fallback: Create cursor-ruler programmatically if not found
                var timelineContainer = rootElement.Q<VisualElement>("timeline-container");
                if (timelineContainer != null)
                {
                    cursorRuler = new VisualElement();
                    cursorRuler.name = "cursor-ruler-fallback";
                    cursorRuler.AddToClassList("cursor-ruler");
                    timelineContainer.Insert(0, cursorRuler); // Insert at beginning
                }
            }
        }

        private void BindEvents()
        {
            // Zoom control events
            if (zoomSlider != null)
                zoomSlider.RegisterValueChangedCallback(evt => SetZoomLevel(evt.newValue));
            if (fitButton != null)
                fitButton.clicked += FitTimelineToWindow;

            // Timeline ruler drag events - 让整个标尺区域支持拖�?
            if (timelineRuler != null)
            {
                timelineRuler.RegisterCallback<MouseDownEvent>(OnTimelineRulerMouseDown);
                timelineRuler.RegisterCallback<MouseMoveEvent>(OnTimelineRulerMouseMove);
                timelineRuler.RegisterCallback<MouseUpEvent>(OnTimelineRulerMouseUp);
            }

            // Cursor ruler drag events
            if (cursorRuler != null)
            {
                cursorRuler.RegisterCallback<MouseDownEvent>(OnCursorRulerMouseDown);
                cursorRuler.RegisterCallback<MouseMoveEvent>(OnCursorRulerMouseMove);
                cursorRuler.RegisterCallback<MouseUpEvent>(OnCursorRulerMouseUp);
            }
        }

        public void UpdateTimelineRuler(SkillData skillData)
        {
            if (timelineRuler == null || skillData == null) return;

            float totalWidth = skillData.totalDuration * frameWidth;
            timelineRuler.style.minWidth = totalWidth;
            timelineRuler.style.width = totalWidth;

            CreateRulerMarkers(skillData);
        }

        private void CreateRulerMarkers(SkillData skillData)
        {
            timelineRuler.Clear();

            // 计算刻度密度，避免标记过�?
            int displayInterval = CalculateDisplayInterval(frameWidth);

            // 确保最后一帧总是显示
            var displayedFrames = new HashSet<int>();

            // 按间隔显示刻�?
            for (int frame = 0; frame <= skillData.totalDuration; frame += displayInterval)
            {
                var marker = CreateFrameMarker(frame, frame % 5 == 0);
                timelineRuler.Add(marker);
                displayedFrames.Add(frame);
            }

            // 特殊处理：确保最后一帧总是显示（如果还没有显示的话�?
            if (!displayedFrames.Contains(skillData.totalDuration))
            {
                var lastFrameMarker = CreateFrameMarker(skillData.totalDuration, skillData.totalDuration % 5 == 0);
                timelineRuler.Add(lastFrameMarker);
            }
        }

        private int CalculateDisplayInterval(float frameWidth)
        {
            // 当帧宽度小于15像素时，增加显示间隔
            if (frameWidth < 10f) return 20;
            if (frameWidth < 15f) return 10;
            if (frameWidth < 25f) return 5;
            return 1;
        }

        private VisualElement CreateFrameMarker(int frame, bool isMajor)
        {
            var marker = new Label();
            marker.AddToClassList("frame-marker");

            if (isMajor)
            {
                marker.AddToClassList("major");
                marker.text = frame.ToString();
            }
            else
            {
                marker.AddToClassList("minor");
                marker.text = "";
            }

            marker.style.left = frame * frameWidth;
            marker.style.position = Position.Absolute;

            // 为刻度标记添加拖拽支�?
            marker.RegisterCallback<MouseDownEvent>(evt => OnFrameMarkerMouseDown(evt, frame));
            marker.RegisterCallback<MouseMoveEvent>(OnFrameMarkerMouseMove);
            marker.RegisterCallback<MouseUpEvent>(OnFrameMarkerMouseUp);

            return marker;
        }

        public void UpdateFrameLines(SkillData skillData)
        {
            if (frameLines == null || skillData == null) return;

            frameLines.Clear();
            for (int frame = 0; frame < skillData.totalDuration; frame++)
            {
                var line = new VisualElement();
                line.AddToClassList("frame-line");
                if (frame % 5 == 0) line.AddToClassList("major");
                line.style.left = frame * frameWidth;
                frameLines.Add(line);
            }
        }

        public void UpdatePlayhead(int currentFrame)
        {
            if (playhead != null)
            {
                // Playhead is inside the ScrollView, so it doesn't need scroll offset adjustment
                playhead.style.left = currentFrame * frameWidth;
            }
        }

        public void UpdateCursorRuler(int currentFrame)
        {
            if (cursorRuler != null)
            {
                // Calculate position with track header offset and scroll offset
                float trackHeaderWidth = 150f; // From CSS .track-header-space { width: 150px; }
                float scrollOffset = GetCurrentScrollOffset();
                float position = trackHeaderWidth + (currentFrame * frameWidth) - scrollOffset;

                cursorRuler.style.left = position;
                cursorRuler.BringToFront();
            }
        }

        private void SetZoomLevel(float zoom)
        {
            if (isUpdatingZoom) return;

            isUpdatingZoom = true;

            // 专业缩放计算，参考Unity Timeline实现
            const float maxTimeAreaScaling = 90000.0f;
            const float minTimeAreaScaling = 0.1f;

            float newFrameWidth = Mathf.Clamp(baseFrameWidth * zoom,
                baseFrameWidth * minTimeAreaScaling,
                baseFrameWidth * maxTimeAreaScaling);
            float newZoomLevel = newFrameWidth / baseFrameWidth;

            // Only update if zoom actually changed
            if (Mathf.Abs(frameWidth - newFrameWidth) > 0.001f)
            {
                zoomLevel = newZoomLevel;
                frameWidth = newFrameWidth;

                // Update zoom slider to reflect actual zoom level
                if (zoomSlider != null && Mathf.Abs(zoomSlider.value - zoomLevel) > 0.001f)
                {
                    zoomSlider.SetValueWithoutNotify(zoomLevel);
                }

                // Notify editor of zoom change
                editor.OnTimelineZoomChanged();
            }

            isUpdatingZoom = false;
        }

        private void FitTimelineToWindow()
        {
            // 真正的Fit功能：让所有内容都能在当前窗口中可�?
            if (timelineTracksScroll != null && editor.CurrentSkillData != null)
            {
                var skillData = editor.CurrentSkillData;

                // 获取ScrollView的可用宽度用于水平缩�?
                float availableWidth = timelineTracksScroll.resolvedStyle.width - 20f; // 减去垂直滚动条宽�?

                // 计算水平缩放：让整个技能时长适配宽度
                float optimalZoom = CalculateFitZoomLevel(availableWidth, baseFrameWidth, skillData.totalDuration);

                // 应用缩放
                if (zoomSlider != null)
                {
                    zoomSlider.value = optimalZoom;
                }
                SetZoomLevel(optimalZoom);

                // 重置滚动位置�?，确保显示完整内�?
                ResetScrollersToZero();
            }
        }

        /// <summary>
        /// 公共方法：调用fit功能展示完整时间�?
        /// </summary>
        public void FitToWindow()
        {
            FitTimelineToWindow();
        }

        private float CalculateFitZoomLevel(float availableWidth, float baseFrameWidth, int totalFrames)
        {
            if (totalFrames <= 0 || baseFrameWidth <= 0) return 1.0f;

            float requiredWidth = totalFrames * baseFrameWidth;
            if (requiredWidth <= availableWidth) return 1.0f;

            return Mathf.Clamp(availableWidth / requiredWidth, 0.1f, 1.0f);
        }


        private void UpdateAllTrackHeights()
        {
            // 更新轨道容器的高�?
            if (editor.CurrentSkillData != null)
            {
                UpdateTimelineSize(editor.CurrentSkillData);
            }

            // 通知编辑器更新轨道显�?
            editor.UpdateTracks();
        }


        public float GetCurrentScrollOffset()
        {
            // Get scroll offset from the timeline tracks scroll view
            if (timelineTracksScroll != null)
            {
                return timelineTracksScroll.horizontalScroller.value;
            }
            return 0;
        }

        private void OnTimelineRulerMouseDown(MouseDownEvent evt)
        {
            if (evt.button == 0) // Left click only
            {
                // 防止与cursor-ruler拖拽冲突
                if (isDraggingCursorRuler) return;

                // 开始从标尺拖拽，不立即定位到帧
                isDraggingFromRuler = true;
                timelineRuler.CaptureMouse();

                // 计算精确的帧位置（支持小数），用于流畅拖�?
                float exactFrame = evt.localMousePosition.x / frameWidth;
                int clickedFrame = Mathf.RoundToInt(exactFrame);

                // Clamp to valid frame range
                clickedFrame = Mathf.Clamp(clickedFrame, 0, editor.CurrentSkillData?.totalDuration ?? 0);

                editor.SetCurrentFrame(clickedFrame);

                // 停止事件传播，防止触发其他元素的点击事件
                evt.StopPropagation();
            }
        }

        private void OnCursorRulerMouseDown(MouseDownEvent evt)
        {
            if (evt.button == 0) // Left mouse button
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
                // Get the timeline container for coordinate conversion
                var timelineContainer = cursorRuler?.parent;
                if (timelineContainer != null)
                {
                    // Convert mouse position to local coordinates
                    Vector2 localPos = timelineContainer.WorldToLocal(evt.mousePosition);

                    // Adjust for the track header space offset (150px) to align with timeline content
                    float trackHeaderWidth = 150f;
                    float adjustedX = localPos.x - trackHeaderWidth;

                    // 专业坐标转换，参考Unity Timeline实现
                    float scrollOffset = GetCurrentScrollOffset();
                    // Use RoundToInt instead of FloorToInt to allow reaching the last frame
                    int targetFrame = Mathf.RoundToInt((adjustedX + scrollOffset) / frameWidth);

                    editor.SetCurrentFrame(targetFrame);
                }
                evt.StopPropagation();
            }
        }

        private void OnCursorRulerMouseUp(MouseUpEvent evt)
        {
            if (evt.button == 0 && isDraggingCursorRuler)
            {
                isDraggingCursorRuler = false;
                cursorRuler.ReleaseMouse();
                evt.StopPropagation();
            }
        }

        private void OnTimelineRulerMouseMove(MouseMoveEvent evt)
        {
            if (isDraggingFromRuler)
            {
                // 精确计算帧位置，支持流畅拖拽
                float exactFrame = evt.localMousePosition.x / frameWidth;
                int targetFrame = Mathf.RoundToInt(exactFrame);

                // Clamp to valid range
                targetFrame = Mathf.Clamp(targetFrame, 0, editor.CurrentSkillData?.totalDuration ?? 0);

                editor.SetCurrentFrame(targetFrame);
                evt.StopPropagation();
            }
        }

        private void OnTimelineRulerMouseUp(MouseUpEvent evt)
        {
            if (evt.button == 0 && isDraggingFromRuler)
            {
                isDraggingFromRuler = false;
                timelineRuler.ReleaseMouse();
                evt.StopPropagation();
            }
        }

        private void OnFrameMarkerMouseDown(MouseDownEvent evt, int markerFrame)
        {
            if (evt.button == 0) // Left click only
            {
                // 防止与其他拖拽冲�?
                if (isDraggingCursorRuler || isDraggingFromRuler) return;

                // 直接设置到该帧，然后开始拖�?
                editor.SetCurrentFrame(markerFrame);

                // 开始从刻度标记拖拽
                isDraggingFromRuler = true;
                ((VisualElement)evt.target).CaptureMouse();

                evt.StopPropagation();
            }
        }

        private void OnFrameMarkerMouseMove(MouseMoveEvent evt)
        {
            if (isDraggingFromRuler)
            {
                // 获取标尺容器，用于坐标转�?
                var ruler = timelineRuler;
                if (ruler != null)
                {
                    // 将鼠标位置转换到标尺坐标�?
                    Vector2 localPos = ruler.WorldToLocal(evt.mousePosition);

                    // 精确计算帧位�?
                    float exactFrame = localPos.x / frameWidth;
                    int targetFrame = Mathf.RoundToInt(exactFrame);

                    // Clamp to valid range
                    targetFrame = Mathf.Clamp(targetFrame, 0, editor.CurrentSkillData?.totalDuration ?? 0);

                    editor.SetCurrentFrame(targetFrame);
                }
                evt.StopPropagation();
            }
        }

        private void OnFrameMarkerMouseUp(MouseUpEvent evt)
        {
            if (evt.button == 0 && isDraggingFromRuler)
            {
                isDraggingFromRuler = false;
                ((VisualElement)evt.target).ReleaseMouse();
                evt.StopPropagation();
            }
        }

        public void UpdateTimelineSize(SkillData skillData)
        {
            if (timelineTracks == null || skillData == null) return;

            float totalWidth = skillData.totalDuration * frameWidth;
            float totalHeight = skillData.tracks.Count * (trackHeight + 2);

            // Update both timeline tracks and its container
            timelineTracks.style.minWidth = totalWidth;
            timelineTracks.style.minHeight = totalHeight;
            timelineTracks.style.width = totalWidth;
            timelineTracks.style.height = totalHeight;

            // Update the container that holds the timeline tracks
            if (timelineTracksContainer != null)
            {
                timelineTracksContainer.style.minWidth = totalWidth;
                timelineTracksContainer.style.minHeight = totalHeight;
                timelineTracksContainer.style.width = totalWidth;
                timelineTracksContainer.style.height = totalHeight;
            }

            // 关键修复：直接更新ScrollView的content container
            if (timelineTracksScroll != null)
            {
                // 强制更新content container - 这是ScrollView内容大小的关�?
                var contentContainer = timelineTracksScroll.contentContainer;
                if (contentContainer != null)
                {
                    contentContainer.style.width = totalWidth;
                    contentContainer.style.height = totalHeight;
                    contentContainer.MarkDirtyRepaint();
                }

                // 确保ScrollView本身也知道新的内容大�?
                timelineTracksScroll.MarkDirtyRepaint();
            }

            // Force scroll view to refresh its scrolling range
            RefreshScrollView();
        }

        private void ResetScrollersToZero()
        {
            // 正确地将滚动条重置到0位置
            if (timelineTracksScroll != null)
            {
                // 使用延迟执行确保布局更新完成后再重置滚动�?
                timelineTracksScroll.schedule.Execute(() =>
                {
                    if (timelineTracksScroll.horizontalScroller != null)
                    {
                        timelineTracksScroll.horizontalScroller.value = 0f;
                    }
                    if (timelineTracksScroll.verticalScroller != null)
                    {
                        timelineTracksScroll.verticalScroller.value = 0f;
                    }
                });
            }

            // 同步重置track headers的垂直滚�?
            if (trackHeadersScroll != null)
            {
                trackHeadersScroll.schedule.Execute(() =>
                {
                    if (trackHeadersScroll.verticalScroller != null)
                    {
                        trackHeadersScroll.verticalScroller.value = 0f;
                    }
                });
            }
        }

        private void RefreshScrollView()
        {
            // 简化的ScrollView刷新逻辑，避免过度操作导致滚动条消失
            if (timelineTracksScroll != null)
            {
                // 标记需要重新计算布局
                timelineTracksScroll.MarkDirtyRepaint();

                // 延迟执行，让Unity有时间完成布局计算
                timelineTracksScroll.schedule.Execute(() =>
                {
                    // 强制显示滚动条dragger，防止被隐藏
                    if (timelineTracksScroll.horizontalScroller != null)
                    {
                        var horizontalDragger = timelineTracksScroll.horizontalScroller.Q(className: "unity-base-slider__dragger");
                        if (horizontalDragger != null)
                        {
                            horizontalDragger.style.display = DisplayStyle.Flex;
                            horizontalDragger.style.visibility = Visibility.Visible;
                        }
                    }
                    if (timelineTracksScroll.verticalScroller != null)
                    {
                        var verticalDragger = timelineTracksScroll.verticalScroller.Q(className: "unity-base-slider__dragger");
                        if (verticalDragger != null)
                        {
                            verticalDragger.style.display = DisplayStyle.Flex;
                            verticalDragger.style.visibility = Visibility.Visible;
                        }
                    }
                }).ExecuteLater(10); // 稍长延迟确保布局完成
            }
        }
    }
}