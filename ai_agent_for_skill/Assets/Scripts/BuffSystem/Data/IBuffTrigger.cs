using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace BuffSystem.Data
{
    /// <summary>
    /// Buff触发器接口 - 定义Buff的触发条件和行为
    /// </summary>
    public interface IBuffTrigger
    {
        /// <summary>
        /// 触发器名称
        /// </summary>
        string TriggerName { get; }
        
        /// <summary>
        /// 触发器描述
        /// </summary>
        string Description { get; }
        
        /// <summary>
        /// 初始化触发器
        /// </summary>
        void Initialize(BuffContext context);
        
        /// <summary>
        /// 检查是否应该触发
        /// </summary>
        bool ShouldTrigger(BuffContext context, TriggerEventArgs args);
        
        /// <summary>
        /// 执行触发逻辑
        /// </summary>
        void Execute(BuffContext context, TriggerEventArgs args);
        
        /// <summary>
        /// 清理触发器
        /// </summary>
        void Cleanup(BuffContext context);
    }

    /// <summary>
    /// 触发器事件参数
    /// </summary>
    public class TriggerEventArgs
    {
        /// <summary>
        /// 事件类型
        /// </summary>
        public TriggerEventType EventType { get; set; }
        
        /// <summary>
        /// 事件来源
        /// </summary>
        public GameObject EventSource { get; set; }
        
        /// <summary>
        /// 事件目标
        /// </summary>
        public GameObject EventTarget { get; set; }
        
        /// <summary>
        /// 数值参数（伤害值、治疗值等）
        /// </summary>
        public float Value { get; set; }
        
        /// <summary>
        /// 额外数据
        /// </summary>
        public object ExtraData { get; set; }
    }

    /// <summary>
    /// 触发事件类型
    /// </summary>
    public enum TriggerEventType
    {
        [LabelText("无")] None = 0,
        [LabelText("Buff施加")] OnApply,
        [LabelText("Buff移除")] OnRemove,
        [LabelText("每帧更新")] OnTick,
        [LabelText("受到伤害")] OnDamageTaken,
        [LabelText("造成伤害")] OnDamageDealt,
        [LabelText("受到治疗")] OnHealReceived,
        [LabelText("施放治疗")] OnHealDealt,
        [LabelText("释放技能")] OnSkillCast,
        [LabelText("技能命中")] OnSkillHit,
        [LabelText("暴击")] OnCriticalHit,
        [LabelText("闪避")] OnDodge,
        [LabelText("格挡")] OnBlock,
        [LabelText("击杀")] OnKill,
        [LabelText("死亡")] OnDeath,
        [LabelText("进入战斗")] OnEnterCombat,
        [LabelText("离开战斗")] OnLeaveCombat,
        [LabelText("移动")] OnMove,
        [LabelText("停止移动")] OnStopMove,
        [LabelText("生命值变化")] OnHealthChange,
        [LabelText("法力值变化")] OnManaChange,
        [LabelText("周期触发")] OnInterval
    }

    /// <summary>
    /// Buff触发器基类 - 提供默认实现
    /// </summary>
    [Serializable]
    public abstract class BuffTriggerBase : IBuffTrigger
    {
        [SerializeField]
        [LabelText("触发器名称")]
        protected string triggerName = "未命名触发器";
        
        [SerializeField]
        [TextArea(2, 4)]
        [LabelText("触发器描述")]
        protected string description = "";
        
        public virtual string TriggerName => triggerName;
        public virtual string Description => description;
        
        public virtual void Initialize(BuffContext context) { }
        public virtual bool ShouldTrigger(BuffContext context, TriggerEventArgs args) => true;
        public virtual void Execute(BuffContext context, TriggerEventArgs args) { }
        public virtual void Cleanup(BuffContext context) { }
    }
}

