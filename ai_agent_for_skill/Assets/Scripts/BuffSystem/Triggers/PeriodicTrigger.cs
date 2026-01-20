using System;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Triggers
{
    /// <summary>
    /// 周期触发器 - 按固定时间间隔触发效果
    /// </summary>
    [Serializable]
    [LabelText("周期触发")]
    public class PeriodicTrigger : BuffTriggerBase
    {
        [BoxGroup("Timing")]
        [LabelText("触发间隔(秒)")]
        [MinValue(0.1f)]
        public float interval = 1f;
        
        [BoxGroup("Timing")]
        [LabelText("首次触发延迟(秒)")]
        [MinValue(0)]
        public float initialDelay = 0f;
        
        [BoxGroup("Timing")]
        [LabelText("立即触发一次")]
        [InfoBox("Buff施加时立即触发一次")]
        public bool triggerOnApply = false;
        
        [BoxGroup("Effect")]
        [LabelText("触发时执行的效果索引")]
        [InfoBox("对应BuffTemplate.effects列表中的索引，-1表示执行所有效果")]
        public int effectIndex = -1;
        
        private float timer;
        private bool initialDelayPassed;
        
        public PeriodicTrigger()
        {
            triggerName = "周期触发";
            description = "按固定时间间隔触发效果";
        }
        
        public override void Initialize(BuffContext context)
        {
            base.Initialize(context);
            timer = 0f;
            initialDelayPassed = initialDelay <= 0;
            
            if (triggerOnApply)
            {
                Execute(context, new TriggerEventArgs { EventType = TriggerEventType.OnApply });
            }
        }
        
        public override bool ShouldTrigger(BuffContext context, TriggerEventArgs args)
        {
            if (!base.ShouldTrigger(context, args))
                return false;
                
            if (args.EventType != TriggerEventType.OnTick)
                return false;
            
            return true;
        }
        
        public override void Execute(BuffContext context, TriggerEventArgs args)
        {
            base.Execute(context, args);
            
            Debug.Log($"[PeriodicTrigger] Triggered at interval {interval}s");
            
            // 执行指定的效果
            if (effectIndex >= 0 && effectIndex < context.Template.effects.Count)
            {
                context.Template.effects[effectIndex].OnTick(context, interval);
            }
            else
            {
                // 执行所有效果
                foreach (var effect in context.Template.effects)
                {
                    effect.OnTick(context, interval);
                }
            }
        }
        
        /// <summary>
        /// 更新计时器（由BuffManager调用）
        /// </summary>
        public bool UpdateTimer(float deltaTime)
        {
            if (!initialDelayPassed)
            {
                timer += deltaTime;
                if (timer >= initialDelay)
                {
                    initialDelayPassed = true;
                    timer = 0f;
                }
                return false;
            }
            
            timer += deltaTime;
            if (timer >= interval)
            {
                timer -= interval;
                return true;
            }
            return false;
        }
    }
}

