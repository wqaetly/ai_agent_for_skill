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
    /// 技能编辑器主窗口 - 核心编辑器逻辑和组件协调
    /// 职责：窗口管理、组件协调、数据管理、选择状态管理
    /// </summary>
    public class SkillEditorWindow : EditorWindow
    {
        [MenuItem("Tools/Skill Editor")]
        public static void OpenWindow()
        {
            GetWindow<SkillEditorWindow>("Skill Editor").Show();
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

        public SkillData CurrentSkillData => currentSkillData;
        public int CurrentFrame => currentFrame;
        public float FrameWidth => timelineController?.FrameWidth ?? 20f;

        private void OnEnable()
        {
            if (currentSkillData == null)
            {
                CreateNewSkill();
            }
        }

        private void CreateGUI()
        {
            // Load UXML
            var visualTree = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(
                "Assets/Scripts/SkillSystem/Editor/SkillEditor.uxml");
            rootElement = visualTree.Instantiate();
            rootVisualElement.Add(rootElement);

            // Load USS
            var styleSheet = AssetDatabase.LoadAssetAtPath<StyleSheet>(
                "Assets/Scripts/SkillSystem/Editor/SkillEditor.uss");
            rootElement.styleSheets.Add(styleSheet);

            InitializeComponents();
            BindEvents();
            RefreshUI();
        }

        private void Update()
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

            // Get new ScrollView elements
            var trackHeadersScroll = rootElement.Q<ScrollView>("track-headers-scroll");
            var timelineTracksScroll = rootElement.Q<ScrollView>("timeline-tracks-scroll");

            // Synchronize scrolling between track headers and timeline tracks
            if (trackHeadersScroll != null && timelineTracksScroll != null)
            {
                // Sync vertical scrolling: when tracks scroll vertically, track headers should follow
                timelineTracksScroll.verticalScroller.valueChanged += (scrollValue) =>
                {
                    trackHeadersScroll.verticalScroller.value = scrollValue;
                };

                // Also sync the other direction
                trackHeadersScroll.verticalScroller.valueChanged += (scrollValue) =>
                {
                    timelineTracksScroll.verticalScroller.value = scrollValue;
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

        private void UpdateTracks()
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
            var action = track.actions[actionIndex];
            if (actionElements.ContainsKey(action))
            {
                actionElements[action].SetSelected(true);
            }

            actionInspector?.RefreshInspector(currentSkillData, selectedTrackIndex, selectedActionIndex, currentFrame);
        }

        private void DeselectAction()
        {
            if (selectedTrackIndex >= 0 && selectedActionIndex >= 0)
            {
                var track = currentSkillData.tracks[selectedTrackIndex];
                if (selectedActionIndex < track.actions.Count)
                {
                    var action = track.actions[selectedActionIndex];
                    if (actionElements.ContainsKey(action))
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
            // Mark the editor as dirty for save purposes
            // Could implement undo/redo here
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
                if (actionIndex >= 0 && actionIndex < track.actions.Count)
                {
                    var action = track.actions[actionIndex];

                    // Remove from action elements dictionary
                    if (actionElements.ContainsKey(action))
                    {
                        actionElements.Remove(action);
                    }

                    // Remove from track
                    track.actions.RemoveAt(actionIndex);

                    // Update indices for remaining actions in the same track
                    for (int i = actionIndex; i < track.actions.Count; i++)
                    {
                        var remainingAction = track.actions[i];
                        if (actionElements.ContainsKey(remainingAction))
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

            // Update skill executor with new data
            skillExecutor?.SetSkillData(currentSkillData);

            if (rootElement != null)
            {
                RefreshUI();
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

                    // Update skill executor with loaded data
                    skillExecutor?.SetSkillData(currentSkillData);

                    RefreshUI();
                }
            }
        }

        private void SaveSkill()
        {
            if (currentSkillData != null)
            {
                string path = SkillDataSerializer.GetSkillFilePath(currentSkillData.skillName);
                SkillDataSerializer.SaveToFile(currentSkillData, path);
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
            Debug.Log($"[Editor] Action Entered: {action.GetActionName()} at frame {action.frame}");
        }

        private void OnActionTicked(ISkillAction action, int relativeFrame)
        {
            // Visual feedback for action ticking
            if (actionElements.ContainsKey(action))
            {
                actionElements[action].SetExecutionState(true, true);
            }
        }

        private void OnActionExited(ISkillAction action)
        {
            // Visual feedback for action exit
            if (actionElements.ContainsKey(action))
            {
                actionElements[action].SetExecutionState(false, false);
            }
            Debug.Log($"[Editor] Action Exited: {action.GetActionName()} at frame {currentFrame}");
        }

        private void OnSkillExecutionStarted(SkillData skillData)
        {
            Debug.Log($"[Editor] Skill execution started: {skillData.skillName}");
        }

        private void OnSkillExecutionStopped(SkillData skillData)
        {
            Debug.Log($"[Editor] Skill execution stopped: {skillData.skillName}");

            // Clear all action execution states
            foreach (var actionElement in actionElements.Values)
            {
                actionElement.SetExecutionState(false, false);
            }
        }

        private void OnExecutionError(string error)
        {
            Debug.LogError($"[Editor] Skill execution error: {error}");
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
    }

    /// <summary>
    /// 编辑器技能执行器 - 在编辑器中实时执行技能逻辑
    /// </summary>
    public class EditorSkillExecutor
    {
        // Events
        public System.Action<int> OnFrameChanged;
        public System.Action<ISkillAction> OnActionEntered;
        public System.Action<ISkillAction, int> OnActionTicked;
        public System.Action<ISkillAction> OnActionExited;
        public System.Action<SkillData> OnSkillStarted;
        public System.Action<SkillData> OnSkillStopped;
        public System.Action<string> OnExecutionError;

        // Core state
        private SkillData currentSkillData;
        private int currentFrame;
        private bool isExecuting;
        private float frameTimer;

        // Action tracking
        private readonly HashSet<ISkillAction> activeActions = new HashSet<ISkillAction>();

        public SkillData CurrentSkillData => currentSkillData;
        public int CurrentFrame => currentFrame;
        public bool IsExecuting => isExecuting;

        public void SetSkillData(SkillData skillData)
        {
            if (isExecuting)
            {
                StopExecution();
            }

            currentSkillData = skillData;
            currentFrame = 0;
            frameTimer = 0f;

            if (skillData != null)
            {
                ResetAllActionStates();
            }
        }

        public void StartExecution()
        {
            if (currentSkillData == null)
            {
                OnExecutionError?.Invoke("No skill data to execute");
                return;
            }

            isExecuting = true;
            currentFrame = 0;
            frameTimer = 0f;

            ResetAllActionStates();
            OnSkillStarted?.Invoke(currentSkillData);
            Debug.Log($"[EditorSkillExecutor] Started executing skill: {currentSkillData.skillName}");
        }

        public void StopExecution()
        {
            if (!isExecuting) return;

            foreach (var action in activeActions)
            {
                try
                {
                    action.ForceExit();
                    OnActionExited?.Invoke(action);
                }
                catch (System.Exception e)
                {
                    OnExecutionError?.Invoke($"Error exiting action {action.GetActionName()}: {e.Message}");
                }
            }

            activeActions.Clear();
            isExecuting = false;
            OnSkillStopped?.Invoke(currentSkillData);
            Debug.Log($"[EditorSkillExecutor] Stopped executing skill: {currentSkillData?.skillName}");
        }

        public void SetFrame(int targetFrame)
        {
            if (currentSkillData == null) return;

            int clampedFrame = Mathf.Clamp(targetFrame, 0, currentSkillData.totalDuration);
            if (clampedFrame == currentFrame && isExecuting) return;

            currentFrame = clampedFrame;
            ProcessFrame();
            OnFrameChanged?.Invoke(currentFrame);
        }

        public void UpdateExecution()
        {
            if (!isExecuting || currentSkillData == null) return;

            frameTimer += Time.deltaTime;
            float frameInterval = 1f / currentSkillData.frameRate;

            while (frameTimer >= frameInterval)
            {
                frameTimer -= frameInterval;
                AdvanceFrame();
            }
        }

        private void AdvanceFrame()
        {
            currentFrame++;

            if (currentFrame >= currentSkillData.totalDuration)
            {
                currentFrame = 0;
                ResetAllActionStates();
            }

            ProcessFrame();
            OnFrameChanged?.Invoke(currentFrame);
        }

        private void ProcessFrame()
        {
            if (currentSkillData == null) return;

            var allActiveActionsThisFrame = new HashSet<ISkillAction>();

            foreach (var track in currentSkillData.tracks)
            {
                if (!track.enabled) continue;

                foreach (var action in track.actions)
                {
                    if (action.IsActiveAtFrame(currentFrame))
                    {
                        allActiveActionsThisFrame.Add(action);
                    }
                }
            }

            // Process exits
            var actionsToExit = new List<ISkillAction>();
            foreach (var activeAction in activeActions)
            {
                if (!allActiveActionsThisFrame.Contains(activeAction))
                {
                    actionsToExit.Add(activeAction);
                }
            }

            foreach (var action in actionsToExit)
            {
                try
                {
                    action.OnExit();
                    activeActions.Remove(action);
                    OnActionExited?.Invoke(action);
                }
                catch (System.Exception e)
                {
                    OnExecutionError?.Invoke($"Error in OnExit for {action.GetActionName()}: {e.Message}");
                }
            }

            // Process enters
            var actionsToEnter = new List<ISkillAction>();
            foreach (var newActiveAction in allActiveActionsThisFrame)
            {
                if (!activeActions.Contains(newActiveAction))
                {
                    actionsToEnter.Add(newActiveAction);
                }
            }

            foreach (var action in actionsToEnter)
            {
                try
                {
                    action.OnEnter();
                    activeActions.Add(action);
                    OnActionEntered?.Invoke(action);
                }
                catch (System.Exception e)
                {
                    OnExecutionError?.Invoke($"Error in OnEnter for {action.GetActionName()}: {e.Message}");
                }
            }

            // Process ticks
            foreach (var action in activeActions)
            {
                try
                {
                    int relativeFrame = currentFrame - action.frame;
                    action.OnTick(relativeFrame);
                    OnActionTicked?.Invoke(action, relativeFrame);
                }
                catch (System.Exception e)
                {
                    OnExecutionError?.Invoke($"Error in OnTick for {action.GetActionName()}: {e.Message}");
                }
            }
        }

        private void ResetAllActionStates()
        {
            foreach (var action in activeActions)
            {
                try
                {
                    action.ForceExit();
                }
                catch (System.Exception e)
                {
                    Debug.LogError($"Error force exiting action {action.GetActionName()}: {e.Message}");
                }
            }

            activeActions.Clear();

            if (currentSkillData != null)
            {
                foreach (var track in currentSkillData.tracks)
                {
                    foreach (var action in track.actions)
                    {
                        action.ResetLifecycleState();
                    }
                }
            }
        }
    }
}