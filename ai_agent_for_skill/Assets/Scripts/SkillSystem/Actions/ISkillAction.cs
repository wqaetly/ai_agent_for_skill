using System;
using System.Reflection;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    [Serializable]
    public abstract class ISkillAction
    {
        [LabelText("Frame")]
        [MinValue(0)]
        public int frame;

        [LabelText("Duration (Frames)")]
        [MinValue(1)]
        public int duration = 1;

        [LabelText("Enabled")]
        public bool enabled = true;

        // Lifecycle state tracking
        [System.NonSerialized]
        private bool hasEntered = false;
        [System.NonSerialized]
        private bool hasExecuted = false;

        public abstract string GetActionName();

        /// <summary>
        /// 获取Action的显示名称（中文）
        /// 优先使用ActionDisplayName特性，如果没有则使用GetActionName()
        /// </summary>
        public virtual string GetDisplayName()
        {
            var attr = this.GetType().GetCustomAttribute<ActionDisplayNameAttribute>();
            return attr?.DisplayName ?? GetActionName();
        }

        // Core lifecycle methods - must be implemented by derived classes
        /// <summary>
        /// Called once when the action becomes active (frame >= action.frame)
        /// Use this for initialization that should happen when the action starts
        /// </summary>
        public virtual void OnEnter() { }

        /// <summary>
        /// Called every frame while the action is active (during action.frame to action.frame + duration)
        /// currentFrame is relative to the action's start frame (0 = first frame, duration-1 = last frame)
        /// </summary>
        public virtual void OnTick(int relativeFrame) { }

        /// <summary>
        /// Called once when the action becomes inactive (frame >= action.frame + duration)
        /// Use this for cleanup that should happen when the action ends
        /// </summary>
        public virtual void OnExit() { }

        // Legacy method for backward compatibility - calls OnEnter
        [Obsolete("Use OnEnter() instead of Execute()")]
        public virtual void Execute()
        {
            OnEnter();
        }

        // Legacy methods for backward compatibility
        public virtual void Initialize() { }
        public virtual void Cleanup() { }
        public virtual void Update(int currentFrame)
        {
            if (IsActiveAtFrame(currentFrame))
            {
                int relativeFrame = currentFrame - frame;
                OnTick(relativeFrame);
            }
        }

        /// <summary>
        /// Processes the action lifecycle based on current frame
        /// This method handles Enter/Tick/Exit state transitions automatically
        /// </summary>
        public void ProcessLifecycle(int currentFrame)
        {
            bool shouldBeActive = IsActiveAtFrame(currentFrame);

            if (shouldBeActive && !hasEntered)
            {
                // Action is becoming active - call OnEnter
                hasEntered = true;
                hasExecuted = false;
                OnEnter();
            }
            else if (shouldBeActive && hasEntered)
            {
                // Action is currently active - call OnTick
                int relativeFrame = currentFrame - frame;
                OnTick(relativeFrame);
            }
            else if (!shouldBeActive && hasEntered)
            {
                // Action is becoming inactive - call OnExit
                hasEntered = false;
                OnExit();
            }
        }

        /// <summary>
        /// Resets the action's lifecycle state (useful for skill looping or restarting)
        /// </summary>
        public void ResetLifecycleState()
        {
            hasEntered = false;
            hasExecuted = false;
        }

        /// <summary>
        /// Forces the action to exit (useful for stopping skills mid-execution)
        /// </summary>
        public void ForceExit()
        {
            if (hasEntered)
            {
                hasEntered = false;
                OnExit();
            }
        }

        public bool IsActiveAtFrame(int currentFrame)
        {
            return enabled && currentFrame >= frame && currentFrame < frame + duration;
        }

        // Helper properties for lifecycle state
        public bool HasEntered => hasEntered;
        public bool IsCurrentlyActive(int currentFrame) => IsActiveAtFrame(currentFrame) && hasEntered;
    }
}