using System;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Triggers
{
    /// <summary>
    /// 阈值触发器 - 当资源值达到特定阈值时触发
    /// </summary>
    [Serializable]
    [LabelText("阈值触发")]
    public class ThresholdTrigger : BuffTriggerBase
    {
        [BoxGroup("Threshold")]
        [LabelText("资源类型")]
        public ResourceType resourceType = ResourceType.Health;
        
        [BoxGroup("Threshold")]
        [LabelText("阈值类型")]
        public ThresholdType thresholdType = ThresholdType.Below;
        
        [BoxGroup("Threshold")]
        [LabelText("阈值(百分比)")]
        [Range(0, 1)]
        public float thresholdPercent = 0.3f;
        
        [BoxGroup("Threshold")]
        [LabelText("仅触发一次")]
        [InfoBox("跨越阈值后只触发一次，需要恢复后再次跨越才能再次触发")]
        public bool onlyOnce = true;
        
        [BoxGroup("Effect")]
        [LabelText("触发时执行的效果索引列表")]
        public int effectIndex = -1;
        
        private bool wasTriggered = false;
        private bool wasAboveThreshold = true;
        
        public ThresholdTrigger()
        {
            triggerName = "阈值触发";
            description = "当资源值达到特定阈值时触发";
        }
        
        public override void Initialize(BuffContext context)
        {
            base.Initialize(context);
            wasTriggered = false;
            wasAboveThreshold = true; // 假设初始时高于阈值
        }
        
        public override bool ShouldTrigger(BuffContext context, TriggerEventArgs args)
        {
            if (!base.ShouldTrigger(context, args))
                return false;
            
            if (args.EventType != TriggerEventType.OnHealthChange &&
                args.EventType != TriggerEventType.OnManaChange)
                return false;
            
            // 在实际实现中，这里需要从目标获取当前资源百分比
            // float currentPercent = GetCurrentResourcePercent(context);
            
            return !wasTriggered || !onlyOnce;
        }
        
        public override void Execute(BuffContext context, TriggerEventArgs args)
        {
            base.Execute(context, args);
            wasTriggered = true;
            
            Debug.Log($"[ThresholdTrigger] {resourceType} reached {thresholdType} {thresholdPercent:P0}");
            
            if (effectIndex >= 0 && effectIndex < context.Template.effects.Count)
            {
                context.Template.effects[effectIndex].OnTick(context, 0);
            }
        }
        
        /// <summary>
        /// 检查阈值状态（由BuffManager调用）
        /// </summary>
        public bool CheckThreshold(float currentPercent)
        {
            bool isBelowThreshold = currentPercent < thresholdPercent;
            bool isAboveThreshold = currentPercent >= thresholdPercent;
            
            bool shouldTrigger = false;
            
            switch (thresholdType)
            {
                case ThresholdType.Below:
                    // 从高于阈值变为低于阈值时触发
                    shouldTrigger = wasAboveThreshold && isBelowThreshold;
                    break;
                case ThresholdType.Above:
                    // 从低于阈值变为高于阈值时触发
                    shouldTrigger = !wasAboveThreshold && isAboveThreshold;
                    break;
                case ThresholdType.Cross:
                    // 任意方向跨越阈值时触发
                    shouldTrigger = (wasAboveThreshold && isBelowThreshold) || 
                                   (!wasAboveThreshold && isAboveThreshold);
                    break;
            }
            
            wasAboveThreshold = isAboveThreshold;
            
            if (shouldTrigger && onlyOnce && wasTriggered)
            {
                return false;
            }
            
            return shouldTrigger;
        }
        
        /// <summary>
        /// 重置触发状态
        /// </summary>
        public void ResetTrigger()
        {
            wasTriggered = false;
        }
    }
    
    /// <summary>
    /// 资源类型
    /// </summary>
    public enum ResourceType
    {
        [LabelText("生命值")] Health,
        [LabelText("法力值")] Mana,
        [LabelText("能量")] Energy,
        [LabelText("怒气")] Rage,
        [LabelText("护盾")] Shield
    }
    
    /// <summary>
    /// 阈值类型
    /// </summary>
    public enum ThresholdType
    {
        [LabelText("低于阈值")] Below,
        [LabelText("高于阈值")] Above,
        [LabelText("跨越阈值")] Cross
    }
}

