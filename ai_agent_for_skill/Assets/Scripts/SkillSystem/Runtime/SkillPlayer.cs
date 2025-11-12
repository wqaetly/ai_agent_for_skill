using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SkillSystem.Data;
using SkillSystem.Actions;

namespace SkillSystem.Runtime
{
    public class SkillPlayer : MonoBehaviour
    {
        [SerializeField] private bool playOnStart = false;
        [SerializeField] private bool loopSkill = false;
        [SerializeField] private string skillFilePath = "";

        private SkillData currentSkillData;
        private int currentFrame = 0;
        private bool isPlaying = false;
        private float frameTimer = 0f;
        private float frameInterval = 1f / 30f; // Default 30 FPS

        // Events
        public System.Action<SkillData> OnSkillStarted;
        public System.Action<SkillData> OnSkillFinished;
        public System.Action<int> OnFrameChanged;
        public System.Action<ISkillAction> OnActionExecuted;

        // Active actions tracking
        private Dictionary<ISkillAction, bool> activeActions = new Dictionary<ISkillAction, bool>();

        void Start()
        {
            if (playOnStart && !string.IsNullOrEmpty(skillFilePath))
            {
                LoadAndPlaySkill(skillFilePath);
            }
        }

        void Update()
        {
            if (isPlaying && currentSkillData != null)
            {
                UpdateSkillPlayback();
            }
        }

        public bool LoadSkill(string filePath)
        {
            var skillData = SkillDataSerializer.LoadFromFile(filePath);
            if (skillData != null)
            {
                currentSkillData = skillData;
                frameInterval = 1f / currentSkillData.frameRate;
                Debug.Log($"Loaded skill: {currentSkillData.skillName}");
                return true;
            }
            return false;
        }

        public bool LoadSkillFromJson(string jsonData)
        {
            var skillData = SkillDataSerializer.DeserializeFromJson(jsonData);
            if (skillData != null)
            {
                currentSkillData = skillData;
                frameInterval = 1f / currentSkillData.frameRate;
                Debug.Log($"Loaded skill from JSON: {currentSkillData.skillName}");
                return true;
            }
            return false;
        }

        public void PlaySkill()
        {
            if (currentSkillData == null)
            {
                Debug.LogWarning("No skill data loaded!");
                return;
            }

            isPlaying = true;
            currentFrame = 0;
            frameTimer = 0f;
            activeActions.Clear();

            // Subscribe to skill system events
            SubscribeToSkillSystemEvents();

            InitializeAllActions();
            OnSkillStarted?.Invoke(currentSkillData);
            Debug.Log($"Started playing skill: {currentSkillData.skillName}");
        }

        public void StopSkill()
        {
            if (!isPlaying) return;

            isPlaying = false;

            // Unsubscribe from skill system events
            UnsubscribeFromSkillSystemEvents();

            CleanupAllActions();
            OnSkillFinished?.Invoke(currentSkillData);
            Debug.Log($"Stopped playing skill: {currentSkillData.skillName}");
        }

        public void PauseSkill()
        {
            isPlaying = false;
        }

        public void ResumeSkill()
        {
            if (currentSkillData != null)
            {
                isPlaying = true;
            }
        }

        public void SetFrame(int frame)
        {
            if (currentSkillData == null) return;

            currentFrame = Mathf.Clamp(frame, 0, currentSkillData.totalDuration - 1);
            frameTimer = 0f;
            OnFrameChanged?.Invoke(currentFrame);

            // Update active actions for the new frame
            UpdateActiveActions();
        }

        public void LoadAndPlaySkill(string filePath)
        {
            if (LoadSkill(filePath))
            {
                PlaySkill();
            }
        }

        public void LoadAndPlaySkillFromJson(string jsonData)
        {
            if (LoadSkillFromJson(jsonData))
            {
                PlaySkill();
            }
        }

        private void UpdateSkillPlayback()
        {
            frameTimer += Time.deltaTime;

            while (frameTimer >= frameInterval)
            {
                frameTimer -= frameInterval;
                AdvanceFrame();
            }
        }

        private void AdvanceFrame()
        {
            if (currentFrame >= currentSkillData.totalDuration)
            {
                if (loopSkill)
                {
                    currentFrame = 0;
                    CleanupAllActions();
                    InitializeAllActions();
                }
                else
                {
                    StopSkill();
                    return;
                }
            }

            OnFrameChanged?.Invoke(currentFrame);
            ExecuteActionsAtFrame(currentFrame);
            UpdateActiveActions();

            currentFrame++;
        }

        private void ExecuteActionsAtFrame(int frame)
        {
            var enabledTracks = currentSkillData.GetEnabledTracks();

            foreach (var track in enabledTracks)
            {
                var actionsAtFrame = track.GetActionsAtFrame(frame);

                foreach (var action in actionsAtFrame)
                {
                    // Only execute on the first frame of the action
                    if (action.frame == frame)
                    {
                        try
                        {
                            action.Execute();
                            OnActionExecuted?.Invoke(action);
                            Debug.Log($"Executed action: {action.GetDisplayName()} at frame {frame}");
                        }
                        catch (System.Exception e)
                        {
                            Debug.LogError($"Error executing action {action.GetDisplayName()}: {e.Message}");
                        }
                    }
                }
            }
        }

        private void UpdateActiveActions()
        {
            var enabledTracks = currentSkillData.GetEnabledTracks();

            // Clear previous active actions
            activeActions.Clear();

            foreach (var track in enabledTracks)
            {
                // 防御性检查：track.actions 可能在反序列化时为 null
                if (track.actions == null) continue;

                foreach (var action in track.actions)
                {
                    // 防御性检查：action 可能为 null
                    if (action == null) continue;

                    if (action.IsActiveAtFrame(currentFrame))
                    {
                        activeActions[action] = true;
                        action.ProcessLifecycle(currentFrame);
                    }
                }
            }
        }

        private void InitializeAllActions()
        {
            var enabledTracks = currentSkillData.GetEnabledTracks();

            foreach (var track in enabledTracks)
            {
                // 防御性检查：track.actions 可能在反序列化时为 null
                if (track.actions == null) continue;

                foreach (var action in track.actions)
                {
                    // 防御性检查：action 可能为 null
                    if (action == null) continue;

                    try
                    {
                        action.Initialize();
                    }
                    catch (System.Exception e)
                    {
                        Debug.LogError($"Error initializing action {action.GetDisplayName()}: {e.Message}");
                    }
                }
            }
        }

        private void CleanupAllActions()
        {
            if (currentSkillData == null) return;

            var enabledTracks = currentSkillData.GetEnabledTracks();

            foreach (var track in enabledTracks)
            {
                // 防御性检查：track.actions 可能在反序列化时为 null
                if (track.actions == null) continue;

                foreach (var action in track.actions)
                {
                    // 防御性检查：action 可能为 null
                    if (action == null) continue;

                    try
                    {
                        action.ForceExit();
                    }
                    catch (System.Exception e)
                    {
                        Debug.LogError($"Error cleaning up action {action.GetDisplayName()}: {e.Message}");
                    }
                }
            }

            activeActions.Clear();
        }

        // Public getters
        public SkillData CurrentSkillData => currentSkillData;
        public int CurrentFrame => currentFrame;
        public bool IsPlaying => isPlaying;
        public float Progress => currentSkillData != null ? (float)currentFrame / currentSkillData.totalDuration : 0f;
        public List<ISkillAction> GetActiveActions() => new List<ISkillAction>(activeActions.Keys);

        // Debugging
        [ContextMenu("Debug Current State")]
        private void DebugCurrentState()
        {
            if (currentSkillData == null)
            {
                Debug.Log("No skill data loaded");
                return;
            }

            Debug.Log($"Skill: {currentSkillData.skillName}");
            Debug.Log($"Frame: {currentFrame}/{currentSkillData.totalDuration}");
            Debug.Log($"Playing: {isPlaying}");
            Debug.Log($"Active Actions: {activeActions.Count}");
        }

        // Skill System Events Integration
        private void SubscribeToSkillSystemEvents()
        {
            SkillSystemEvents.OnRequestFrameJump += HandleFrameJump;
            SkillSystemEvents.OnRequestSkillStop += HandleSkillStop;
        }

        private void UnsubscribeFromSkillSystemEvents()
        {
            SkillSystemEvents.OnRequestFrameJump -= HandleFrameJump;
            SkillSystemEvents.OnRequestSkillStop -= HandleSkillStop;
        }

        private void HandleFrameJump(int targetFrame)
        {
            if (!isPlaying) return;

            Debug.Log($"[SkillPlayer] Jumping from frame {currentFrame} to frame {targetFrame}");
            SetFrame(targetFrame);
        }

        private void HandleSkillStop()
        {
            if (!isPlaying) return;

            Debug.Log($"[SkillPlayer] Stopping skill via event");
            StopSkill();
        }

        void OnDestroy()
        {
            // Ensure events are unsubscribed when the object is destroyed
            UnsubscribeFromSkillSystemEvents();
        }
    }
}