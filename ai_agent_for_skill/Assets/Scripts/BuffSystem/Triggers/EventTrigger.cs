using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Triggers
{
    /// <summary>
    /// 事件触发器 - 响应特定游戏事件
    /// </summary>
    [Serializable]
    [LabelText("事件触发")]
    public class EventTrigger : BuffTriggerBase
    {
        [BoxGroup("Event")]
        [LabelText("监听事件类型")]
        [EnumToggleButtons]
        public TriggerEventType eventType = TriggerEventType.OnDamageTaken;
        
        [BoxGroup("Condition")]
        [LabelText("最小触发值")]
        [InfoBox("例如：受到伤害至少X点才触发")]
        public float minValue = 0f;
        
        [BoxGroup("Condition")]
        [LabelText("最大触发值")]
        [InfoBox("0表示无上限")]
        public float maxValue = 0f;
        
        [BoxGroup("Condition")]
        [LabelText("触发概率")]
        [Range(0, 1)]
        public float triggerChance = 1f;
        
        [BoxGroup("Condition")]
        [LabelText("冷却时间(秒)")]
        [MinValue(0)]
        public float cooldown = 0f;
        
        [BoxGroup("Effect")]
        [LabelText("触发时执行的效果索引列表")]
        [InfoBox("留空表示执行所有效果")]
        public List<int> effectIndices = new List<int>();
        
        private float cooldownTimer = 0f;
        
        public EventTrigger()
        {
            triggerName = "事件触发";
            description = "响应特定游戏事件";
        }
        
        public override void Initialize(BuffContext context)
        {
            base.Initialize(context);
            cooldownTimer = 0f;
        }
        
        public override bool ShouldTrigger(BuffContext context, TriggerEventArgs args)
        {
            if (!base.ShouldTrigger(context, args))
                return false;
            
            // 检查事件类型
            if (args.EventType != eventType)
                return false;
            
            // 检查冷却
            if (cooldownTimer > 0)
                return false;
            
            // 检查数值条件
            float value = GetEventValue(args);
            if (minValue > 0 && value < minValue)
                return false;
            if (maxValue > 0 && value > maxValue)
                return false;
            
            // 检查概率
            if (triggerChance < 1f && UnityEngine.Random.value > triggerChance)
                return false;
            
            return true;
        }
        
        public override void Execute(BuffContext context, TriggerEventArgs args)
        {
            base.Execute(context, args);
            
            // 开始冷却
            cooldownTimer = cooldown;
            
            Debug.Log($"[EventTrigger] Event {eventType} triggered");
            
            // 执行效果
            if (effectIndices.Count > 0)
            {
                foreach (int index in effectIndices)
                {
                    if (index >= 0 && index < context.Template.effects.Count)
                    {
                        context.Template.effects[index].OnTick(context, 0);
                    }
                }
            }
            else
            {
                foreach (var effect in context.Template.effects)
                {
                    effect.OnTick(context, 0);
                }
            }
        }
        
        /// <summary>
        /// 更新冷却（由BuffManager调用）
        /// </summary>
        public void UpdateCooldown(float deltaTime)
        {
            if (cooldownTimer > 0)
            {
                cooldownTimer -= deltaTime;
            }
        }
        
        private float GetEventValue(TriggerEventArgs args)
        {
            // 使用统一的 Value 属性
            return args.Value;
        }
    }
}

