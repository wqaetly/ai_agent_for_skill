using UnityEngine;
using UnityEngine.UIElements;
using UnityEditor;
using System.Collections.Generic;
using System.IO;
using SkillSystem.Data;
using SkillSystem.Actions;

namespace SkillSystem.Editor
{
    /// <summary>
    /// 技能编辑器主窗�?- 核心编辑器逻辑和组件协�?
    /// 职责：窗口管理、组件协调、数据管理、选择状态管�?
    /// </summary>
    public class SkillEditorWindow : EditorWindow
    {
        // 常量配置
        private const float MIN_INSPECTOR_WIDTH = 200f;
        private const float MAX_INSPECTOR_WIDTH = 500f;
        private const int AUTO_FIT_DELAY_MS = 50; // UI完全刷新后执行fit的延迟时�?

        [MenuItem("Tools/Skill Editor")]
        public static void OpenWindow()
        {
            GetWindow<SkillEditorWindow>("Skill Editor").Show();
        }

        /// <summary>
        /// Opens the skill editor window and loads the specified skill data
        /// </summary>
        public static void OpenSkill(SkillData skillData)
        {
            var window = GetWindow<SkillEditorWindow>("Skill Editor");
            window.Show();
            window.LoadSkillData(skillData);
        }

        /// <summary>
        /// Loads skill data into the editor (called by OpenSkill)
        /// </summary>
        private void LoadSkillData(SkillData skillData)
        {
            if (skillData != null)
            {
                currentSkillData = skillData;
                selectedTrackIndex = -1;
                selectedActionIndex = -1;
                currentFrame = 0;

                // Update skill executor with loaded data
                skillExecutor?.SetSkillData(currentSkillData);

                RefreshUI();

                // Auto-fit timeline to show complete skill configuration
                AutoFitTimelineAfterLoad();
            }
        }

        // Core data
        private SkillData currentSkillData;
        private int selectedTrackIndex = -1;
        private int selectedActionIndex = -1;
        private int currentFrame = 0;

        // UI Elements
        private VisualElement rootElement;
        private VisualElement timelineTracks;
        private VisualElement trackHeaders;

        // Controllers
        private TimelineController timelineController;
        private ActionInspector actionInspector;
        private PlaybackController playbackController;
        private EditorSkillExecutor skillExecutor;

        // Track and action management
        private readonly List<TrackElement> trackElements = new List<TrackElement>();
        private readonly Dictionary<ISkillAction, SkillActionElement> actionElements = new Dictionary<ISkillAction, SkillActionElement>();

        // Inspector resize functionality
        private VisualElement resizeHandle;
        private VisualElement inspector;
        private bool isResizing = false;

        // 滚动同步标志位，防止双向绑定导致无限递归
        private bool isSyncingScroll = false;

        // 未保存更改标�?
        private new bool hasUnsavedChanges = false;

        public SkillData CurrentSkillData => currentSkillData;
        public int CurrentFrame => currentFrame;
        public float FrameWidth => timelineController?.FrameWidth ?? 20f;

        /// <summary>
        /// 获取当前选中的轨道索引（REQ-04�?
        /// </summary>
        public int GetSelectedTrackIndex() => selectedTrackIndex;

        private void OnEnable()
        {
            if (currentSkillData == null)
            {
                CreateNewSkill();
            }

            // 订阅编辑器更新事�?
            EditorApplication.update += OnEditorUpdate;
        }

        private void OnDisable()
        {
            // 取消编辑器更新事件订�?
            EditorApplication.update -= OnEditorUpdate;

            // Clean up resources when window is disabled
            actionInspector?.Dispose();

            // 取消事件订阅，防止内存泄�?
            if (skillExecutor != null)
            {
                skillExecutor.OnFrameChanged -= OnExecutorFrameChanged;
                skillExecutor.OnActionEntered -= OnActionEntered;
                skillExecutor.OnActionTicked -= OnActionTicked;
                skillExecutor.OnActionExited -= OnActionExited;
                skillExecutor.OnSkillStarted -= OnSkillExecutionStarted;
                skillExecutor.OnSkillStopped -= OnSkillExecutionStopped;
                skillExecutor.OnExecutionError -= OnExecutionError;
            }
        }

        private void OnDestroy()
        {
            // 检查未保存更改
            if (hasUnsavedChanges && currentSkillData != null)
            {
                int option = EditorUtility.DisplayDialogComplex(
                    "未保存更�?,
                    $"技�?'{currentSkillData.skillName}' 有未保存的更改，是否保存�?,
                    "保存",
                    "取消",
                    "不保�?
                );

                switch (option)
                {
                    case 0: // 保存
                        SaveSkill();
                        break;
                    case 1: // 取消
                        // 用户取消，但窗口已经在销毁中，无法阻�?
                        break;
                    case 2: // 不保�?
                        // 什么也不做
                        break;
                }
            }
        }

        private void CreateGUI()
        {
            // 使用脚本相对路径加载资源，避免硬编码
            var scriptPath = AssetDatabase.GetAssetPath(MonoScript.FromScriptableObject(this));
            var scriptDirectory = Path.GetDirectoryName(scriptPath);

            // Load UXML
            var uxmlPath = Path.Combine(scriptDirectory, "SkillEditor.uxml");
            var visualTree = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(uxmlPath);
            if (visualTree != null)
            {
                visualTree.CloneTree(rootVisualElement);
            }
            else
            {
                Debug.LogError($"无法加载 UXML 文件: {uxmlPath}");
                return;
            }

            rootElement = rootVisualElement;

            // Load USS
            var ussPath = Path.Combine(scriptDirectory, "SkillEditor.uss");
            var styleSheet = AssetDatabase.LoadAssetAtPath<StyleSheet>(ussPath);
            if (styleSheet != null)
            {
                rootElement.styleSheets.Add(styleSheet);
            }
            else
            {
                Debug.LogWarning($"无法加载 USS 文件: {ussPath}");
            }

            InitializeComponents();
            BindEvents();
            RefreshUI();
        }

        /// <summary>
        /// 编辑器更新回调，仅在窗口启用时执�?
        /// </summary>
        private void OnEditorUpdate()
        {
            if (playbackController?.IsPlaying == true)
            {
                playbackController.UpdatePlayback(currentSkillData, currentFrame);
            }

            // Update skill executor for real-time execution
            skillExecutor?.UpdateExecution();
        }

        private void InitializeComponents()
        {
            // Get key UI elements with new ScrollView structure
            timelineTracks = rootElement.Q<VisualElement>("timeline-tracks");
            trackHeaders = rootElement.Q<VisualElement>("track-headers");

            // Get resize elements
            resizeHandle = rootElement.Q<VisualElement>("resize-handle");
            inspector = rootElement.Q<VisualElement>("inspector");

            // Get new ScrollView elements
            var trackHeadersScroll = rootElement.Q<ScrollView>("track-headers-scroll");
            var timelineTracksScroll = rootElement.Q<ScrollView>("timeline-tracks-scroll");

            // Synchronize scrolling between track headers and timeline tracks
            if (trackHeadersScroll != null && timelineTracksScroll != null)
            {
                // Sync vertical scrolling: when tracks scroll vertically, track headers should follow
                // 使用标志位防止双向绑定导致无限递归
                timelineTracksScroll.verticalScroller.valueChanged += (scrollValue) =>
                {
                    if (isSyncingScroll) return;
                    isSyncingScroll = true;
                    trackHeadersScroll.verticalScroller.value = scrollValue;
                    isSyncingScroll = false;
                };

                // Also sync the other direction
                trackHeadersScroll.verticalScroller.valueChanged += (scrollValue) =>
                {
                    if (isSyncingScroll) return;
                    isSyncingScroll = true;
                    timelineTracksScroll.verticalScroller.value = scrollValue;
                    isSyncingScroll = false;
                };

                // Sync horizontal scrolling with timeline ruler
                timelineTracksScroll.horizontalScroller.valueChanged += (scrollValue) =>
                {
                    SyncTimelineRulerScroll(scrollValue);
                };
            }

            // Initialize controllers
            timelineController = new TimelineController(this);
            timelineController.Initialize(rootElement);

            actionInspector = new ActionInspector(this);
            actionInspector.Initialize(rootElement);

            playbackController = new PlaybackController(this);
            playbackController.Initialize(rootElement);

            skillExecutor = new EditorSkillExecutor();
            InitializeSkillExecutor();
        }

        private void InitializeSkillExecutor()
        {
            // Bind events for execution feedback
            skillExecutor.OnFrameChanged += OnExecutorFrameChanged;
            skillExecutor.OnActionEntered += OnActionEntered;
            skillExecutor.OnActionTicked += OnActionTicked;
            skillExecutor.OnActionExited += OnActionExited;

            // 连接到训练场可视化系�?
            ConnectToTrainingGroundVisualizer();
            skillExecutor.OnSkillStarted += OnSkillExecutionStarted;
            skillExecutor.OnSkillStopped += OnSkillExecutionStopped;
            skillExecutor.OnExecutionError += OnExecutionError;

            // Set initial skill data
            if (currentSkillData != null)
            {
                skillExecutor.SetSkillData(currentSkillData);
            }
        }

        private void BindEvents()
        {
            // Toolbar events
            rootElement.Q<Button>("new-button").clicked += CreateNewSkill;
            rootElement.Q<Button>("load-button").clicked += LoadSkill;
            rootElement.Q<Button>("save-button").clicked += SaveSkill;
            rootElement.Q<Button>("save-as-button").clicked += SaveSkillAs;

            rootElement.Q<Button>("add-track-button").clicked += AddNewTrack;

            // Timeline click event
            timelineTracks?.RegisterCallback<MouseDownEvent>(OnTimelineMouseDown);

            // Inspector resize handle events
            InitializeResizeHandle();
        }

        private void RefreshUI()
        {
            if (currentSkillData == null) return;

            // Update all controllers
            playbackController?.UpdateFrameControls(currentSkillData, currentFrame);
            timelineController?.UpdateTimelineRuler(currentSkillData);
            timelineController?.UpdateFrameLines(currentSkillData);
            timelineController?.UpdatePlayhead(currentFrame);
            timelineController?.UpdateCursorRuler(currentFrame);

            UpdateTracks();
            actionInspector?.RefreshInspector(currentSkillData, selectedTrackIndex, selectedActionIndex, currentFrame);
        }

        public void UpdateTracks()
        {
            // Clear existing track elements
            trackHeaders.Clear();
            timelineTracks.Clear();
            trackElements.Clear();
            actionElements.Clear();

            // Create track elements with unified height management
            for (int trackIndex = 0; trackIndex < currentSkillData.tracks.Count; trackIndex++)
            {
                var track = currentSkillData.tracks[trackIndex];
                var trackElement = new TrackElement(track, trackIndex, this);
                trackElements.Add(trackElement);

                // Set unified height for both header and row
                float trackTopPosition = trackIndex * (timelineController.TrackHeight + 2);

                // Add header with consistent height
                trackElement.style.height = timelineController.TrackHeight;
                trackElement.style.marginBottom = 2;
                trackHeaders.Add(trackElement);

                // Add track row to timeline with same height and position
                var trackRow = trackElement.GetTrackRow();
                trackRow.style.height = timelineController.TrackHeight;
                trackRow.style.top = trackTopPosition;
                trackRow.style.position = Position.Absolute;
                timelineTracks.Add(trackRow);

                // Create action elements for this track
                // 防御性检查：track.actions 可能在反序列化时�?null
                if (track.actions != null)
                {
                    for (int actionIndex = 0; actionIndex < track.actions.Count; actionIndex++)
                    {
                        var action = track.actions[actionIndex];
                        if (action != null)
                        {
                            var actionElement = new SkillActionElement(action, trackIndex, actionIndex, this);
                            actionElement.style.top = trackTopPosition + 1; // Small offset inside track
                            actionElement.style.position = Position.Absolute;
                            timelineTracks.Add(actionElement);
                            actionElements[action] = actionElement;
                        }
                    }
                }
            }

            // Update timeline size
            timelineController?.UpdateTimelineSize(currentSkillData);
        }

        public void SelectTrack(int trackIndex)
        {
            // Deselect current selection
            if (selectedTrackIndex >= 0 && selectedTrackIndex < trackElements.Count)
            {
                trackElements[selectedTrackIndex].SetSelected(false);
            }

            if (selectedActionIndex >= 0)
            {
                DeselectAction();
            }

            selectedTrackIndex = selectedTrackIndex == trackIndex ? -1 : trackIndex;
            selectedActionIndex = -1;

            // Select new track
            if (selectedTrackIndex >= 0 && selectedTrackIndex < trackElements.Count)
            {
                trackElements[selectedTrackIndex].SetSelected(true);
            }

            actionInspector?.RefreshInspector(currentSkillData, selectedTrackIndex, selectedActionIndex, currentFrame);
        }

        public void SelectAction(int trackIndex, int actionIndex)
        {
            // Deselect current selection
            DeselectAction();
            if (selectedTrackIndex >= 0 && selectedTrackIndex < trackElements.Count)
            {
                trackElements[selectedTrackIndex].SetSelected(false);
            }

            selectedTrackIndex = trackIndex;
            selectedActionIndex = actionIndex;

            // Select new action
            var track = currentSkillData.tracks[trackIndex];
            // 防御性检查：track.actions �?action 可能�?null
            if (track.actions != null && actionIndex < track.actions.Count)
            {
                var action = track.actions[actionIndex];
                if (action != null && actionElements.ContainsKey(action))
                {
                    actionElements[action].SetSelected(true);
                }
            }

            actionInspector?.RefreshInspector(currentSkillData, selectedTrackIndex, selectedActionIndex, currentFrame);
        }

        private void DeselectAction()
        {
            if (selectedTrackIndex >= 0 && selectedActionIndex >= 0)
            {
                var track = currentSkillData.tracks[selectedTrackIndex];
                // 防御性检查：track.actions 可能�?null
                if (track.actions != null && selectedActionIndex < track.actions.Count)
                {
                    var action = track.actions[selectedActionIndex];
                    // 防御性检查：action 可能�?null
                    if (action != null && actionElements.ContainsKey(action))
                    {
                        actionElements[action].SetSelected(false);
                    }
                }
            }
        }

        public void SetCurrentFrame(int newFrame)
        {
            // Allow frame range from 0 to totalDuration (inclusive) to match ruler display
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

        public void SetTotalDuration(int newDuration)
        {
            playbackController?.SetTotalDuration(newDuration, currentSkillData, currentFrame);
        }

        private void OnTimelineMouseDown(MouseDownEvent evt)
        {
            if (evt.button == 0) // Left click
            {
                float scrollOffset = timelineController?.GetCurrentScrollOffset() ?? 0;
                playbackController?.OnTimelineMouseDown(evt, FrameWidth, scrollOffset);
            }
        }

        private void InitializeResizeHandle()
        {
            if (resizeHandle == null) return;

            resizeHandle.RegisterCallback<MouseDownEvent>(OnResizeStart);
            resizeHandle.RegisterCallback<MouseMoveEvent>(OnResizeMove);
            resizeHandle.RegisterCallback<MouseUpEvent>(OnResizeEnd);
            rootElement.RegisterCallback<MouseUpEvent>(OnResizeEnd);
            rootElement.RegisterCallback<MouseMoveEvent>(OnResizeMove);
        }

        private void OnResizeStart(MouseDownEvent evt)
        {
            if (evt.button == 0) // Left mouse button
            {
                isResizing = true;
                resizeHandle.CaptureMouse();
                evt.StopPropagation();
            }
        }

        private void OnResizeMove(MouseMoveEvent evt)
        {
            if (!isResizing) return;

            // Calculate new inspector width based on mouse position
            var containerWidth = rootElement.resolvedStyle.width;
            var mouseX = evt.mousePosition.x;
            var newInspectorWidth = containerWidth - mouseX - 4; // Account for handle width

            // Clamp to min/max values
            newInspectorWidth = Mathf.Clamp(newInspectorWidth, MIN_INSPECTOR_WIDTH, MAX_INSPECTOR_WIDTH);

            // Apply new width
            inspector.style.width = newInspectorWidth;
            evt.StopPropagation();
        }

        private void OnResizeEnd(MouseUpEvent evt)
        {
            if (isResizing)
            {
                isResizing = false;
                resizeHandle.ReleaseMouse();
                evt.StopPropagation();
            }
        }


        public Vector2 GetTimelineScrollOffset()
        {
            float scrollOffset = timelineController?.GetCurrentScrollOffset() ?? 0;
            return new Vector2(scrollOffset, 0);
        }

        public float GetCurrentScrollOffset()
        {
            return timelineController?.GetCurrentScrollOffset() ?? 0;
        }

        public void MarkDirty()
        {
            hasUnsavedChanges = true;
            // 可选：在窗口标题显�?* 标记
            titleContent = new GUIContent(hasUnsavedChanges ? "Skill Editor *" : "Skill Editor");
        }

        public void AddActionToTrack<T>(int trackIndex, int frame) where T : ISkillAction, new()
        {
            if (trackIndex >= 0 && trackIndex < currentSkillData.tracks.Count)
            {
                var action = new T();
                action.frame = Mathf.Clamp(frame, 0, currentSkillData.totalDuration - action.duration);
                currentSkillData.tracks[trackIndex].AddAction(action);

                // Auto-select the newly added action
                selectedTrackIndex = trackIndex;
                selectedActionIndex = currentSkillData.tracks[trackIndex].actions.Count - 1;

                RefreshUI();
                MarkDirty();
            }
        }

        public void DeleteAction(int trackIndex, int actionIndex)
        {
            if (trackIndex >= 0 && trackIndex < currentSkillData.tracks.Count)
            {
                var track = currentSkillData.tracks[trackIndex];
                // 防御性检查：track.actions 可能�?null
                if (track.actions == null) return;

                if (actionIndex >= 0 && actionIndex < track.actions.Count)
                {
                    var action = track.actions[actionIndex];

                    // Remove from action elements dictionary
                    // 防御性检查：action 可能�?null
                    if (action != null && actionElements.ContainsKey(action))
                    {
                        actionElements.Remove(action);
                    }

                    // Remove from track
                    track.actions.RemoveAt(actionIndex);

                    // Update indices for remaining actions in the same track
                    for (int i = actionIndex; i < track.actions.Count; i++)
                    {
                        var remainingAction = track.actions[i];
                        // 防御性检查：remainingAction 可能�?null
                        if (remainingAction != null && actionElements.ContainsKey(remainingAction))
                        {
                            actionElements[remainingAction].UpdateIndices(trackIndex, i);
                        }
                    }

                    // Clear selection if this action was selected
                    if (selectedTrackIndex == trackIndex && selectedActionIndex == actionIndex)
                    {
                        selectedActionIndex = -1;
                    }
                    // Update selection index if selected action was after deleted one
                    else if (selectedTrackIndex == trackIndex && selectedActionIndex > actionIndex)
                    {
                        selectedActionIndex--;
                    }

                    RefreshUI();
                    MarkDirty();
                }
            }
        }

        private void CreateNewSkill()
        {
            currentSkillData = new SkillData();
            currentSkillData.skillName = "New Skill";
            currentSkillData.totalDuration = 60;
            currentSkillData.frameRate = 30;

            // Add a default track
            var defaultTrack = new SkillTrack();
            defaultTrack.trackName = "Default Track";
            currentSkillData.AddTrack(defaultTrack);

            selectedTrackIndex = -1;
            selectedActionIndex = -1;
            currentFrame = 0;

            // 清除未保存更改标�?
            hasUnsavedChanges = false;
            titleContent = new GUIContent("Skill Editor");

            // Update skill executor with new data
            skillExecutor?.SetSkillData(currentSkillData);

            if (rootElement != null)
            {
                RefreshUI();

                // Auto-fit timeline to show complete skill configuration
                AutoFitTimelineAfterLoad();
            }
        }

        private void AddNewTrack()
        {
            var newTrack = new SkillTrack();
            newTrack.trackName = $"Track {currentSkillData.tracks.Count + 1}";
            currentSkillData.AddTrack(newTrack);
            RefreshUI();
        }

        public void DeleteTrack(int trackIndex)
        {
            if (trackIndex >= 0 && trackIndex < currentSkillData.tracks.Count)
            {
                currentSkillData.tracks.RemoveAt(trackIndex);
                if (selectedTrackIndex == trackIndex)
                {
                    selectedTrackIndex = -1;
                    selectedActionIndex = -1;
                }
                RefreshUI();
            }
        }

        private void LoadSkill()
        {
            string path = EditorUtility.OpenFilePanel("Load Skill", SkillDataSerializer.GetDefaultSkillPath(), "json");
            if (!string.IsNullOrEmpty(path))
            {
                var loadedSkill = SkillDataSerializer.LoadFromFile(path);
                if (loadedSkill != null)
                {
                    currentSkillData = loadedSkill;
                    selectedTrackIndex = -1;
                    selectedActionIndex = -1;
                    currentFrame = 0;

                    // 清除未保存更改标�?
                    hasUnsavedChanges = false;
                    titleContent = new GUIContent("Skill Editor");

                    // Update skill executor with loaded data
                    skillExecutor?.SetSkillData(currentSkillData);

                    RefreshUI();

                    // Auto-fit timeline to show complete skill configuration
                    AutoFitTimelineAfterLoad();
                }
            }
        }

        private void SaveSkill()
        {
            if (currentSkillData != null)
            {
                string path = SkillDataSerializer.GetSkillFilePath(currentSkillData.skillName);
                SkillDataSerializer.SaveToFile(currentSkillData, path);

                // 清除未保存更改标�?
                hasUnsavedChanges = false;
                titleContent = new GUIContent("Skill Editor");
            }
        }

        private void SaveSkillAs()
        {
            if (currentSkillData != null)
            {
                string path = EditorUtility.SaveFilePanel("Save Skill As", SkillDataSerializer.GetDefaultSkillPath(), currentSkillData.skillName, "json");
                if (!string.IsNullOrEmpty(path))
                {
                    SkillDataSerializer.SaveToFile(currentSkillData, path);

                    // 清除未保存更改标�?
                    hasUnsavedChanges = false;
                    titleContent = new GUIContent("Skill Editor");
                }
            }
        }

        // Event handlers for controllers
        public void OnTimelineZoomChanged()
        {
            // Update zoom-related elements
            timelineController?.UpdateTimelineRuler(currentSkillData);
            timelineController?.UpdateFrameLines(currentSkillData);
            timelineController?.UpdateTimelineSize(currentSkillData); // Critical: Update timeline size for scroll view

            // Update action positions
            foreach (var actionElement in actionElements.Values)
            {
                actionElement.UpdatePosition();
            }

            // Update playhead and cursor ruler
            timelineController?.UpdatePlayhead(currentFrame);
            timelineController?.UpdateCursorRuler(currentFrame);
        }

        public void OnFrameChanged(int newFrame)
        {
            currentFrame = newFrame;
            playbackController?.UpdateFrameControls(currentSkillData, currentFrame);
            timelineController?.UpdatePlayhead(currentFrame);
            timelineController?.UpdateCursorRuler(currentFrame);
        }

        public void OnDurationChanged(int newFrame)
        {
            currentFrame = newFrame;
            RefreshUI();
            MarkDirty();
        }

        public void OnActionPropertyChanged(ISkillAction action)
        {
            if (actionElements.ContainsKey(action))
            {
                actionElements[action].UpdatePosition();
                actionElements[action].UpdateAppearance();
            }
            MarkDirty();
        }

        public void OnTrackPropertyChanged()
        {
            RefreshUI();
            MarkDirty();
        }

        public void OnSkillPropertyChanged()
        {
            RefreshUI();
            MarkDirty();
        }

        private void SyncTimelineRulerScroll(float scrollValue)
        {
            // Get the timeline ruler element
            var timelineRuler = rootElement.Q<VisualElement>("timeline-ruler");
            if (timelineRuler != null)
            {
                // Apply horizontal offset to the ruler to sync with timeline scrolling
                timelineRuler.style.left = -scrollValue;
            }

            // Update cursor ruler position to account for scrolling
            timelineController?.UpdateCursorRuler(currentFrame);
        }

        // Skill Executor Event Handlers
        private void OnExecutorFrameChanged(int frame)
        {
            // Sync the editor frame with the executor frame
            if (currentFrame != frame)
            {
                currentFrame = frame;
                playbackController?.UpdateFrameControls(currentSkillData, currentFrame);
                timelineController?.UpdatePlayhead(currentFrame);
                timelineController?.UpdateCursorRuler(currentFrame);
            }
        }

        private void OnActionEntered(ISkillAction action)
        {
            // Visual feedback for action entry
            if (actionElements.ContainsKey(action))
            {
                actionElements[action].SetExecutionState(true, false);
            }

            // 转发到训练场可视化系�?
            ForwardToTrainingGroundVisualizer(action, "Enter", 0);
        }

        private void OnActionTicked(ISkillAction action, int relativeFrame)
        {
            // Visual feedback for action ticking
            if (actionElements.ContainsKey(action))
            {
                actionElements[action].SetExecutionState(true, true);
            }

            // 转发到训练场可视化系�?
            ForwardToTrainingGroundVisualizer(action, "Tick", relativeFrame);
        }

        private void OnActionExited(ISkillAction action)
        {
            // Visual feedback for action exit
            if (actionElements.ContainsKey(action))
            {
                actionElements[action].SetExecutionState(false, false);
            }

            // 转发到训练场可视化系�?
            ForwardToTrainingGroundVisualizer(action, "Exit", 0);
        }

        #region 训练场可视化系统集成

        /// <summary>
        /// 连接到训练场可视化系�?
        /// </summary>
        private void ConnectToTrainingGroundVisualizer()
        {
            // 这个方法在InitializeSkillExecutor时被调用
            // 实际的转发逻辑在ForwardToTrainingGroundVisualizer�?
            Debug.Log("[SkillEditorWindow] Ready to forward events to TrainingGround Visualizer");
        }

        /// <summary>
        /// 将EditorSkillExecutor的事件转发到训练场可视化系统
        /// </summary>
        private void ForwardToTrainingGroundVisualizer(ISkillAction action, string eventType, int relativeFrame)
        {
            // 只在训练场运行时且有可视化管理器时转�?
            if (!Application.isPlaying) return;

            // 查找场景中的SkillVisualizerManager
            var visualizerManager = Object.FindFirstObjectByType<TrainingGround.Visualizer.SkillVisualizerManager>();
            if (visualizerManager == null) return;

            // 根据事件类型调用对应的方�?
            switch (eventType)
            {
                case "Enter":
                    visualizerManager.TriggerActionEnter(action);
                    break;
                case "Tick":
                    visualizerManager.TriggerActionTick(action, relativeFrame);
                    break;
                case "Exit":
                    visualizerManager.TriggerActionExit(action);
                    break;
            }
        }

        #endregion

        private void OnSkillExecutionStarted(SkillData skillData)
        {
            // Skill execution started
        }

        private void OnSkillExecutionStopped(SkillData skillData)
        {
            // Clear all action execution states
            foreach (var actionElement in actionElements.Values)
            {
                actionElement.SetExecutionState(false, false);
            }
        }

        private void OnExecutionError(string error)
        {
            // 显示执行错误给用�?
            Debug.LogError($"[技能编辑器] {error}");
            EditorUtility.DisplayDialog("技能执行错�?, error, "确定");
        }

        // Public methods for controlling execution
        public void StartSkillExecution()
        {
            if (skillExecutor != null && currentSkillData != null)
            {
                skillExecutor.SetSkillData(currentSkillData);
                skillExecutor.StartExecution();
            }
        }

        public void StopSkillExecution()
        {
            skillExecutor?.StopExecution();
        }

        public bool IsSkillExecuting => skillExecutor?.IsExecuting ?? false;

        /// <summary>
        /// 在技能加载后自动调用fit功能，展示完整技能配置全�?
        /// 使用延迟执行确保UI完全渲染后再进行fit操作
        /// </summary>
        private void AutoFitTimelineAfterLoad()
        {
            if (timelineController != null)
            {
                // 使用schedule.Execute延迟执行，确保RefreshUI完成后再fit
                // 这样可以确保timeline尺寸和布局都已经正确更�?
                rootElement.schedule.Execute(() =>
                {
                    // 直接调用TimelineController的FitTimelineToWindow方法
                    // 这会自动计算最佳缩放比例并重置滚动位置
                    FitTimelineToWindow();
                }).ExecuteLater(AUTO_FIT_DELAY_MS); // 延迟执行，确保UI完全刷新后执�?
            }
        }

        /// <summary>
        /// 调用TimelineController的fit功能
        /// </summary>
        private void FitTimelineToWindow()
        {
            // 调用TimelineController的公共fit方法
            timelineController?.FitToWindow();
        }
    }
}