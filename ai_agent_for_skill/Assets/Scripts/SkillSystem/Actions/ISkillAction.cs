using System;
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

        public abstract string GetActionName();
        public abstract void Execute();

        public virtual void Initialize() { }
        public virtual void Cleanup() { }
        public virtual void Update(int currentFrame) { }

        public bool IsActiveAtFrame(int currentFrame)
        {
            return enabled && currentFrame >= frame && currentFrame < frame + duration;
        }
    }
}