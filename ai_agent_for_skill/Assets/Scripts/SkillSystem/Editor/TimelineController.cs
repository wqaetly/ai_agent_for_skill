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
    /// 职责：标尺显示、缩放控制、滚动管理、游标操作
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
            Debug.Log($"CursorRuler found: {cursorRuler != null}");
            if (cursorRuler != null)
            {
                Debug.Log($"CursorRuler parent: {cursorRuler.parent?.name}");
                Debug.Log($"CursorRuler layout: {cursorRuler.layout}");
            }
            else
            {
                // Fallback: Create cursor-ruler programmatically if not found
                Debug.LogWarning("Creating cursor-ruler programmatically!");
                var timelineContainer = rootElement.Q<VisualElement>("timeline-container");
                if (timelineContainer != null)
                {
                    cursorRuler = new VisualElement();
                    cursorRuler.name = "cursor-ruler-fallback";
                    cursorRuler.AddToClassList("cursor-ruler");
                    timelineContainer.Insert(0, cursorRuler); // Insert at beginning
                    Debug.Log($"Created fallback cursor-ruler in {timelineContainer.name}");
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

            // Timeline ruler click event
            if (timelineRuler != null)
                timelineRuler.RegisterCallback<MouseDownEvent>(OnTimelineRulerMouseDown);

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

            // 计算刻度密度，避免标记过密
            int displayInterval = CalculateDisplayInterval(frameWidth);

            for (int frame = 0; frame <= skillData.totalDuration; frame += displayInterval)
            {
                var marker = CreateFrameMarker(frame, frame % 5 == 0);
                timelineRuler.Add(marker);
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
            // 智能缩放算法，参考Unity Timeline实现
            if (timelineTracksContainer != null && editor.CurrentSkillData != null)
            {
                float availableWidth = timelineTracksContainer.resolvedStyle.width;

                // 计算最佳缩放级别
                float optimalZoom = CalculateFitZoomLevel(availableWidth, baseFrameWidth, editor.CurrentSkillData.totalDuration);

                if (zoomSlider != null)
                {
                    zoomSlider.value = optimalZoom;
                }
                SetZoomLevel(optimalZoom);
            }
        }

        private float CalculateFitZoomLevel(float availableWidth, float baseFrameWidth, int totalFrames)
        {
            if (totalFrames <= 0 || baseFrameWidth <= 0) return 1.0f;

            float requiredWidth = totalFrames * baseFrameWidth;
            if (requiredWidth <= availableWidth) return 1.0f;

            return Mathf.Clamp(availableWidth / requiredWidth, 0.1f, 1.0f);
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

                // Since Timeline Ruler now moves with scroll (style.left = -scrollOffset),
                // we should use the mouse position directly without adding scrollOffset again
                int clickedFrame = Mathf.RoundToInt(evt.localMousePosition.x / frameWidth);

                // Clamp to valid frame range
                clickedFrame = Mathf.Clamp(clickedFrame, 0, editor.CurrentSkillData?.totalDuration ?? 0);

                Debug.Log($"Ruler click: x={evt.localMousePosition.x}, frameWidth={frameWidth}, clickedFrame={clickedFrame}");
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

                    Debug.Log($"Drag to frame: calculated={targetFrame}, totalDuration={editor.CurrentSkillData?.totalDuration}, maxAllowed={(editor.CurrentSkillData?.totalDuration ?? 1) - 1}");
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

            // Force scroll view to refresh its scrolling range
            RefreshScrollView();
        }

        private void RefreshScrollView()
        {
            // Force the ScrollView to recalculate its content size and scrolling range
            if (timelineTracksScroll != null)
            {
                // This forces a layout update and scroll range recalculation
                timelineTracksScroll.MarkDirtyRepaint();

                // Schedule a callback to ensure the scroll view updates
                timelineTracksScroll.schedule.Execute(() =>
                {
                    timelineTracksScroll.ScrollTo(timelineTracksScroll.contentContainer.Children().FirstOrDefault());
                });
            }
        }
    }
}