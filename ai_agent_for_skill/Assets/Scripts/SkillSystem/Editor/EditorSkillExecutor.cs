using UnityEngine;
using SkillSystem.Data;
using SkillSystem.Actions;
using System.Collections.Generic;

namespace SkillSystem.Editor
{
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
        }

        public void StopExecution()
        {
            if (!isExecuting) return;

            // 检查是否应该执行Action逻辑
            bool shouldExecute = ExecutionEnvironmentDetector.ShouldExecuteActions();

            foreach (var action in activeActions)
            {
                try
                {
                    // 只有在应该执行的情况下才调用Action的真实逻辑
                    if (shouldExecute)
                    {
                        action.ForceExit();
                    }
                    else
                    {
                        // 编辑器预览模式，只重置状态
                        action.ResetLifecycleState();
                    }
                    OnActionExited?.Invoke(action);
                }
                catch (System.Exception e)
                {
                    OnExecutionError?.Invoke($"Error exiting action {action.GetDisplayName()}: {e.Message}");
                }
            }

            activeActions.Clear();
            isExecuting = false;
            OnSkillStopped?.Invoke(currentSkillData);
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

            // 检查是否应该执行Action逻辑
            bool shouldExecute = ExecutionEnvironmentDetector.ShouldExecuteActions();

            var allActiveActionsThisFrame = new HashSet<ISkillAction>();

            foreach (var track in currentSkillData.tracks)
            {
                if (!track.enabled) continue;

                // 防御性检查：track.actions 可能在反序列化时为 null
                if (track.actions == null) continue;

                foreach (var action in track.actions)
                {
                    // 防御性检查：action 可能为 null
                    if (action == null) continue;

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
                    // 只有在应该执行的情况下才调用Action的真实逻辑
                    if (shouldExecute)
                    {
                        action.OnExit();
                    }
                    activeActions.Remove(action);
                    OnActionExited?.Invoke(action);
                }
                catch (System.Exception e)
                {
                    OnExecutionError?.Invoke($"Error in OnExit for {action.GetDisplayName()}: {e.Message}");
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
                    // 只有在应该执行的情况下才调用Action的真实逻辑
                    if (shouldExecute)
                    {
                        action.OnEnter();
                    }
                    activeActions.Add(action);
                    OnActionEntered?.Invoke(action);
                }
                catch (System.Exception e)
                {
                    OnExecutionError?.Invoke($"Error in OnEnter for {action.GetDisplayName()}: {e.Message}");
                }
            }

            // Process ticks
            foreach (var action in activeActions)
            {
                try
                {
                    // 只有在应该执行的情况下才调用Action的真实逻辑
                    if (shouldExecute)
                    {
                        int relativeFrame = currentFrame - action.frame;
                        action.OnTick(relativeFrame);
                    }
                    OnActionTicked?.Invoke(action, currentFrame - action.frame);
                }
                catch (System.Exception e)
                {
                    OnExecutionError?.Invoke($"Error in OnTick for {action.GetDisplayName()}: {e.Message}");
                }
            }
        }

        private void ResetAllActionStates()
        {
            // 检查是否应该执行Action逻辑
            bool shouldExecute = ExecutionEnvironmentDetector.ShouldExecuteActions();

            foreach (var action in activeActions)
            {
                try
                {
                    // 只有在应该执行的情况下才调用Action的真实逻辑
                    if (shouldExecute)
                    {
                        action.ForceExit();
                    }
                    else
                    {
                        // 编辑器预览模式，只重置状态
                        action.ResetLifecycleState();
                    }
                }
                catch (System.Exception)
                {
                    // Handle force exit error silently
                }
            }

            activeActions.Clear();

            if (currentSkillData != null)
            {
                foreach (var track in currentSkillData.tracks)
                {
                    // 防御性检查：track.actions 可能在反序列化时为 null
                    if (track.actions == null) continue;

                    foreach (var action in track.actions)
                    {
                        // 防御性检查：action 可能为 null
                        if (action == null) continue;

                        action.ResetLifecycleState();
                    }
                }
            }
        }
    }
}