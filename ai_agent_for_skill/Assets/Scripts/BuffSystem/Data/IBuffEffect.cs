using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace BuffSystem.Data
{
    /// <summary>
    /// Buff效果接口 - 定义Buff的具体效果行为
    /// </summary>
    public interface IBuffEffect
    {
        /// <summary>
        /// 效果名称
        /// </summary>
        string EffectName { get; }
        
        /// <summary>
        /// 效果描述
        /// </summary>
        string Description { get; }
        
        /// <summary>
        /// Buff应用时调用
        /// </summary>
        void OnApply(BuffContext context);
        
        /// <summary>
        /// Buff移除时调用
        /// </summary>
        void OnRemove(BuffContext context);
        
        /// <summary>
        /// 每帧/每Tick调用（可选）
        /// </summary>
        void OnTick(BuffContext context, float deltaTime);
        
        /// <summary>
        /// 层数变化时调用
        /// </summary>
        void OnStackChange(BuffContext context, int oldStacks, int newStacks);
    }

    /// <summary>
    /// Buff运行时上下文
    /// </summary>
    [Serializable]
    public class BuffContext
    {
        /// <summary>
        /// Buff来源（施加者）
        /// </summary>
        public GameObject Source { get; set; }

        /// <summary>
        /// Buff目标（承受者）
        /// </summary>
        public GameObject Target { get; set; }

        /// <summary>
        /// 当前层数
        /// </summary>
        public int CurrentStacks { get; set; } = 1;

        /// <summary>
        /// 剩余持续时间
        /// </summary>
        public float RemainingDuration { get; set; }

        /// <summary>
        /// Buff实例ID
        /// </summary>
        public string InstanceId { get; set; }

        /// <summary>
        /// Buff模板引用
        /// </summary>
        public BuffTemplate Template { get; set; }

        /// <summary>
        /// 额外数据（用于传递自定义信息）
        /// </summary>
        public object ExtraData { get; set; }
    }

    /// <summary>
    /// Buff效果基类 - 提供默认实现
    /// </summary>
    [Serializable]
    public abstract class BuffEffectBase : IBuffEffect
    {
        [SerializeField]
        [LabelText("效果名称")]
        protected string effectName = "未命名效果";
        
        [SerializeField]
        [TextArea(2, 4)]
        [LabelText("效果描述")]
        protected string description = "";
        
        public virtual string EffectName => effectName;
        public virtual string Description => description;
        
        public virtual void OnApply(BuffContext context) { }
        public virtual void OnRemove(BuffContext context) { }
        public virtual void OnTick(BuffContext context, float deltaTime) { }
        public virtual void OnStackChange(BuffContext context, int oldStacks, int newStacks) { }
    }
}

