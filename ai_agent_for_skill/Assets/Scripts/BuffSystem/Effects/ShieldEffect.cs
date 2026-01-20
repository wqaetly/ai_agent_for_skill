using System;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Effects
{
    /// <summary>
    /// 护盾效果 - 提供吸收伤害的护盾
    /// </summary>
    [Serializable]
    [LabelText("护盾")]
    public class ShieldEffect : BuffEffectBase
    {
        [BoxGroup("Shield Settings")]
        [LabelText("护盾值")]
        [MinValue(0)]
        public float shieldAmount = 100f;
        
        [BoxGroup("Shield Settings")]
        [LabelText("护盾类型")]
        public ShieldType shieldType = ShieldType.All;
        
        [BoxGroup("Shield Settings")]
        [LabelText("按层数叠加")]
        public bool stackable = false;
        
        [BoxGroup("Advanced")]
        [LabelText("吸收效率")]
        [Range(0, 2)]
        [InfoBox("1.0 = 100%吸收, 0.5 = 吸收50%伤害")]
        public float absorptionRate = 1f;
        
        [BoxGroup("Advanced")]
        [LabelText("护盾破碎效果")]
        public GameObject shieldBreakEffect;
        
        [BoxGroup("Advanced")]
        [LabelText("护盾破碎音效")]
        public AudioClip shieldBreakSound;
        
        private float currentShield;
        
        public ShieldEffect()
        {
            effectName = "护盾";
            description = "提供吸收伤害的护盾";
        }
        
        public override void OnApply(BuffContext context)
        {
            currentShield = shieldAmount;
            if (stackable)
            {
                currentShield *= context.CurrentStacks;
            }
            
            Debug.Log($"[Shield] Applied {currentShield} {shieldType} shield to {context.Target?.name}");
        }
        
        public override void OnRemove(BuffContext context)
        {
            Debug.Log($"[Shield] Removed shield from {context.Target?.name}");
        }
        
        public override void OnStackChange(BuffContext context, int oldStacks, int newStacks)
        {
            if (stackable)
            {
                float shieldPerStack = shieldAmount;
                currentShield = shieldPerStack * newStacks;
                Debug.Log($"[Shield] Shield updated to {currentShield}");
            }
        }
        
        /// <summary>
        /// 吸收伤害
        /// </summary>
        public float AbsorbDamage(float damage, DamageType damageType)
        {
            if (!CanAbsorb(damageType))
                return damage;
            
            float absorbedDamage = Mathf.Min(damage * absorptionRate, currentShield);
            currentShield -= absorbedDamage;
            
            if (currentShield <= 0)
            {
                OnShieldBreak();
            }
            
            return damage - absorbedDamage;
        }
        
        private bool CanAbsorb(DamageType damageType)
        {
            switch (shieldType)
            {
                case ShieldType.All:
                    return true;
                case ShieldType.Physical:
                    return damageType == DamageType.Physical;
                case ShieldType.Magical:
                    return damageType == DamageType.Magical;
                default:
                    return false;
            }
        }
        
        private void OnShieldBreak()
        {
            Debug.Log("[Shield] Shield broken!");
            // 播放破碎效果和音效
        }
    }
    
    /// <summary>
    /// 护盾类型
    /// </summary>
    public enum ShieldType
    {
        [LabelText("全能护盾")] All,
        [LabelText("物理护盾")] Physical,
        [LabelText("魔法护盾")] Magical
    }
}

