using System;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Effects
{
    /// <summary>
    /// 持续伤害效果 (DOT) - 周期性造成伤害
    /// </summary>
    [Serializable]
    [LabelText("持续伤害(DOT)")]
    public class DamageOverTimeEffect : BuffEffectBase
    {
        [BoxGroup("Damage Settings")]
        [LabelText("伤害类型")]
        public DamageType damageType = DamageType.Magical;
        
        [BoxGroup("Damage Settings")]
        [LabelText("每跳伤害")]
        [MinValue(0)]
        public float damagePerTick = 10f;
        
        [BoxGroup("Damage Settings")]
        [LabelText("跳动间隔(秒)")]
        [MinValue(0.1f)]
        public float tickInterval = 1f;
        
        [BoxGroup("Damage Settings")]
        [LabelText("按层数缩放")]
        public bool scaleWithStacks = true;
        
        [BoxGroup("Advanced")]
        [LabelText("可暴击")]
        public bool canCrit = false;
        
        [BoxGroup("Advanced")]
        [LabelText("应用生命偷取")]
        public bool applyLifeSteal = false;
        
        [BoxGroup("Advanced")]
        [LabelText("无视护甲百分比")]
        [Range(0, 1)]
        public float armorPenetration = 0f;
        
        private float tickTimer = 0f;
        
        public DamageOverTimeEffect()
        {
            effectName = "持续伤害";
            description = "周期性造成伤害";
        }
        
        public override void OnApply(BuffContext context)
        {
            tickTimer = 0f;
            // 可选：施加时立即造成一次伤害
            // DealDamage(context);
        }
        
        public override void OnTick(BuffContext context, float deltaTime)
        {
            tickTimer += deltaTime;
            if (tickTimer >= tickInterval)
            {
                tickTimer -= tickInterval;
                DealDamage(context);
            }
        }
        
        private void DealDamage(BuffContext context)
        {
            float damage = damagePerTick;
            if (scaleWithStacks)
            {
                damage *= context.CurrentStacks;
            }
            
            Debug.Log($"[DOT] {context.Template.buffName} deals {damage} {damageType} damage to {context.Target?.name}");
            
            // 实际项目中这里会调用伤害系统的API
            // DamageSystem.DealDamage(context.Source, context.Target, damage, damageType, ...);
        }
    }
    
    /// <summary>
    /// 伤害类型
    /// </summary>
    public enum DamageType
    {
        [LabelText("物理")] Physical,
        [LabelText("魔法")] Magical,
        [LabelText("真实")] True,
        [LabelText("纯粹")] Pure
    }
}

