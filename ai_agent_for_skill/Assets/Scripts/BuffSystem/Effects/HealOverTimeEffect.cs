using System;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Effects
{
    /// <summary>
    /// 持续治疗效果 (HOT) - 周期性恢复生命值
    /// </summary>
    [Serializable]
    [LabelText("持续治疗(HOT)")]
    public class HealOverTimeEffect : BuffEffectBase
    {
        [BoxGroup("Heal Settings")]
        [LabelText("每跳治疗量")]
        [MinValue(0)]
        public float healPerTick = 15f;
        
        [BoxGroup("Heal Settings")]
        [LabelText("跳动间隔(秒)")]
        [MinValue(0.1f)]
        public float tickInterval = 1f;
        
        [BoxGroup("Heal Settings")]
        [LabelText("按层数缩放")]
        public bool scaleWithStacks = true;
        
        [BoxGroup("Advanced")]
        [LabelText("可暴击")]
        public bool canCrit = false;
        
        [BoxGroup("Advanced")]
        [LabelText("受治疗效果加成")]
        public bool affectedByHealingBonus = true;
        
        [BoxGroup("Advanced")]
        [LabelText("超量转护盾")]
        [InfoBox("溢出的治疗量转化为护盾")]
        public bool overhealToShield = false;
        
        [BoxGroup("Advanced")]
        [LabelText("护盾转化率")]
        [ShowIf("overhealToShield")]
        [Range(0, 1)]
        public float shieldConversionRate = 0.5f;
        
        private float tickTimer = 0f;
        
        public HealOverTimeEffect()
        {
            effectName = "持续治疗";
            description = "周期性恢复生命值";
        }
        
        public override void OnApply(BuffContext context)
        {
            tickTimer = 0f;
        }
        
        public override void OnTick(BuffContext context, float deltaTime)
        {
            tickTimer += deltaTime;
            if (tickTimer >= tickInterval)
            {
                tickTimer -= tickInterval;
                Heal(context);
            }
        }
        
        private void Heal(BuffContext context)
        {
            float heal = healPerTick;
            if (scaleWithStacks)
            {
                heal *= context.CurrentStacks;
            }
            
            Debug.Log($"[HOT] {context.Template.buffName} heals {context.Target?.name} for {heal}");
            
            // 实际项目中这里会调用治疗系统的API
            // HealSystem.Heal(context.Source, context.Target, heal, ...);
        }
    }
}

