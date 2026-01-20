using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Effects
{
    /// <summary>
    /// 属性修改效果 - 修改目标的各种属性值
    /// </summary>
    [Serializable]
    [LabelText("属性修改")]
    public class AttributeModifierEffect : BuffEffectBase
    {
        [BoxGroup("Modifiers")]
        [LabelText("属性修改器列表")]
        [ListDrawerSettings(ShowIndexLabels = true)]
        public List<AttributeModifier> modifiers = new List<AttributeModifier>();
        
        [BoxGroup("Settings")]
        [LabelText("按层数缩放")]
        [InfoBox("true: 效果值 = 基础值 × 层数")]
        public bool scaleWithStacks = true;
        
        public AttributeModifierEffect()
        {
            effectName = "属性修改";
            description = "修改目标的属性值";
        }
        
        public override void OnApply(BuffContext context)
        {
            ApplyModifiers(context, context.CurrentStacks);
        }
        
        public override void OnRemove(BuffContext context)
        {
            RemoveModifiers(context);
        }
        
        public override void OnStackChange(BuffContext context, int oldStacks, int newStacks)
        {
            if (scaleWithStacks)
            {
                // 移除旧的修改并应用新的
                RemoveModifiers(context);
                ApplyModifiers(context, newStacks);
            }
        }
        
        private void ApplyModifiers(BuffContext context, int stacks)
        {
            float multiplier = scaleWithStacks ? stacks : 1;
            foreach (var modifier in modifiers)
            {
                float value = modifier.value * multiplier;
                Debug.Log($"[AttributeModifierEffect] Applying {modifier.attributeType}: {modifier.modifierType} {value}");
                // 实际项目中这里会调用角色属性系统的API
            }
        }
        
        private void RemoveModifiers(BuffContext context)
        {
            foreach (var modifier in modifiers)
            {
                Debug.Log($"[AttributeModifierEffect] Removing {modifier.attributeType} modifier");
                // 实际项目中这里会调用角色属性系统的API移除修改器
            }
        }
    }
    
    /// <summary>
    /// 属性修改器
    /// </summary>
    [Serializable]
    public struct AttributeModifier
    {
        [LabelText("属性类型")]
        public AttributeType attributeType;
        
        [LabelText("修改类型")]
        public ModifierType modifierType;
        
        [LabelText("数值")]
        public float value;
    }
    
    /// <summary>
    /// 属性类型枚举
    /// </summary>
    public enum AttributeType
    {
        [LabelText("生命值")] Health,
        [LabelText("最大生命值")] MaxHealth,
        [LabelText("法力值")] Mana,
        [LabelText("最大法力值")] MaxMana,
        [LabelText("攻击力")] AttackDamage,
        [LabelText("法术强度")] AbilityPower,
        [LabelText("护甲")] Armor,
        [LabelText("魔法抗性")] MagicResist,
        [LabelText("移动速度")] MovementSpeed,
        [LabelText("攻击速度")] AttackSpeed,
        [LabelText("暴击率")] CriticalChance,
        [LabelText("暴击伤害")] CriticalDamage,
        [LabelText("生命偷取")] LifeSteal,
        [LabelText("法术吸血")] SpellVamp,
        [LabelText("冷却缩减")] CooldownReduction,
        [LabelText("护盾强度")] ShieldStrength
    }
    
    /// <summary>
    /// 修改器类型
    /// </summary>
    public enum ModifierType
    {
        [LabelText("固定值")] Flat,
        [LabelText("百分比加成")] PercentAdd,
        [LabelText("百分比乘算")] PercentMult
    }
}

