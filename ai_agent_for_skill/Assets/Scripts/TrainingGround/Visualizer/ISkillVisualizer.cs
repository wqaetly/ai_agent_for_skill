using UnityEngine;
using SkillSystem.Actions;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// 技能可视化器接口 - 定义如何将Action转换为可视化效果
    /// </summary>
    public interface ISkillVisualizer
    {
        /// <summary>
        /// 该可视化器支持的Action类型
        /// </summary>
        System.Type SupportedActionType { get; }

        /// <summary>
        /// 可视化Action进入
        /// </summary>
        void VisualizeEnter(ISkillAction action, GameObject caster);

        /// <summary>
        /// 可视化Action更新
        /// </summary>
        void VisualizeTick(ISkillAction action, GameObject caster, int relativeFrame);

        /// <summary>
        /// 可视化Action退出
        /// </summary>
        void VisualizeExit(ISkillAction action, GameObject caster);

        /// <summary>
        /// 清理资源
        /// </summary>
        void Cleanup();
    }

    /// <summary>
    /// 可视化器基类 - 提供通用功能
    /// </summary>
    public abstract class SkillVisualizerBase<T> : ISkillVisualizer where T : ISkillAction
    {
        public System.Type SupportedActionType => typeof(T);

        public void VisualizeEnter(ISkillAction action, GameObject caster)
        {
            if (action is T typedAction)
            {
                OnVisualizeEnter(typedAction, caster);
            }
        }

        public void VisualizeTick(ISkillAction action, GameObject caster, int relativeFrame)
        {
            if (action is T typedAction)
            {
                OnVisualizeTick(typedAction, caster, relativeFrame);
            }
        }

        public void VisualizeExit(ISkillAction action, GameObject caster)
        {
            if (action is T typedAction)
            {
                OnVisualizeExit(typedAction, caster);
            }
        }

        protected abstract void OnVisualizeEnter(T action, GameObject caster);
        protected abstract void OnVisualizeTick(T action, GameObject caster, int relativeFrame);
        protected abstract void OnVisualizeExit(T action, GameObject caster);

        public virtual void Cleanup() { }
    }
}
