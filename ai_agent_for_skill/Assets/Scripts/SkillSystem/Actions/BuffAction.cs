using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 增益/减益效果行为脚本
    /// 功能概述：为目标单位添加持续性的状态效果，包括属性加成、减益效果、特殊状态等�?
    /// 支持可叠加的Buff系统，提供图标显示、持续时间管理、刷新机制等功能�?
    /// 适用于DOTA2中的各种Buff和Debuff，如力量加成、减速、眩晕、隐身等状态�?
    /// </summary>
    [Serializable]
    [ActionDisplayName("增益效果")]
    public class BuffAction : ISkillAction
    {
        [BoxGroup("Buff Settings")]
        [LabelText("Buff Type")]
        /// <summary>Buff类型，决定是增益效果还是减益效果</summary>
        public BuffType buffType = BuffType.Buff;

        [BoxGroup("Buff Settings")]
        [LabelText("Buff ID")]
        [InfoBox("用于识别和管理Buff的唯一标识�?)]
        /// <summary>Buff唯一标识符，用于区分不同类型的Buff，相同ID的Buff可能会覆盖或叠加</summary>
        public string buffId = "buff_example";

        [BoxGroup("Buff Settings")]
        [LabelText("Stack Type")]
        /// <summary>叠加类型，决定相同Buff的叠加行为（不叠�?刷新时间/增加层数�?/summary>
        public StackType stackType = StackType.Refresh;

        [BoxGroup("Buff Settings")]
        [LabelText("Max Stacks")]
        [MinValue(1)]
        [ShowIf("@stackType == StackType.Stack")]
        /// <summary>最大叠加层数，仅在叠加类型为Stack时有�?/summary>
        public int maxStacks = 5;

        [BoxGroup("Duration Settings")]
        [LabelText("Buff Duration (Seconds)")]
        [MinValue(0f)]
        [InfoBox("Buff持续时间�?表示永久效果")]
        /// <summary>Buff持续时间，单位为秒，0表示永久持续直到被主动移�?/summary>
        public float buffDuration = 10f;

        /// <summary>持续时间别名，用于Visualizer兼容</summary>
        public float durationSeconds => buffDuration;

        [BoxGroup("Duration Settings")]
        [LabelText("Is Permanent")]
        /// <summary>是否为永久效果，true时忽略持续时间，直到被主动移�?/summary>
        public bool isPermanent = false;

        [BoxGroup("Visual Settings")]
        [LabelText("Buff Icon")]
        /// <summary>Buff图标，用于在UI中显示该效果的视觉标�?/summary>
        public Sprite buffIcon;

        [BoxGroup("Visual Settings")]
        [LabelText("Buff Name")]
        /// <summary>Buff显示名称，在UI中显示给玩家的可读名�?/summary>
        public string buffName = "Example Buff";

        [BoxGroup("Visual Settings")]
        [LabelText("Buff Description")]
        [TextArea(2, 4)]
        /// <summary>Buff描述文本，详细说明该Buff的效果和作用</summary>
        public string buffDescription = "This is an example buff effect.";

        [BoxGroup("Effect Settings")]
        [LabelText("Attribute Modifiers")]
        [InfoBox("属性修正值，可以修改目标的各项属�?)]
        /// <summary>属性修正器数组，定义该Buff对目标各项属性的影响</summary>
        public AttributeModifier[] attributeModifiers = new AttributeModifier[0];

        [BoxGroup("Effect Settings")]
        [LabelText("Special Effects")]
        /// <summary>特殊效果类型，定义该Buff具有的特殊功能（如眩晕、隐身等�?/summary>
        public SpecialEffect specialEffects = SpecialEffect.None;

        [BoxGroup("Effect Settings")]
        [LabelText("Damage Per Second")]
        [MinValue(0f)]
        /// <summary>每秒伤害值（用于持续伤害Buff�?/summary>
        public float damagePerSecond = 0f;

        [BoxGroup("Effect Settings")]
        [LabelText("Heal Per Second")]
        [MinValue(0f)]
        /// <summary>每秒治疗值（用于持续治疗Buff�?/summary>
        public float healPerSecond = 0f;

        [BoxGroup("Effect Settings")]
        [LabelText("Move Speed Modifier")]
        /// <summary>移动速度修正�?/summary>
        public float moveSpeedModifier = 0f;

        [BoxGroup("Effect Settings")]
        [LabelText("Attack Speed Modifier")]
        /// <summary>攻击速度修正�?/summary>
        public float attackSpeedModifier = 0f;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以对哪些单位施加此Buff</summary>
        public TargetFilter targetFilter = TargetFilter.Self;

        [BoxGroup("Target Settings")]
        [LabelText("Apply to Multiple Targets")]
        /// <summary>是否应用到多个目标，true时可以同时为多个目标添加Buff</summary>
        public bool applyToMultipleTargets = false;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(1)]
        [ShowIf("applyToMultipleTargets")]
        /// <summary>最大目标数量，仅在应用到多个目标时有效</summary>
        public int maxTargets = 1;

        public override string GetActionName()
        {
            return "Buff Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[BuffAction] Applying {buffType} '{buffName}' (ID: {buffId})");
            ApplyBuff();
        }

        public override void OnTick(int relativeFrame)
        {
            // Buff通常在应用后自动管理，这里可以添加特殊的每帧更新逻辑
            if (relativeFrame % 30 == 0) // 每秒输出一次状�?
            {
                Debug.Log($"[BuffAction] Buff '{buffName}' is active (Frame: {relativeFrame})");
            }
        }

        public override void OnExit()
        {
            Debug.Log($"[BuffAction] Buff action completed for '{buffName}'");
        }

        /// <summary>应用Buff效果到目标的核心逻辑</summary>
        private void ApplyBuff()
        {
            // 在实际项目中，这里会�?
            // 1. 获取目标单位
            // 2. 检查Buff叠加规则
            // 3. 应用属性修�?
            // 4. 启动持续时间计时�?
            // 5. 更新UI显示

            Debug.Log($"[BuffAction] Buff Details:");
            Debug.Log($"  - Type: {buffType}");
            Debug.Log($"  - Duration: {(isPermanent ? "Permanent" : $"{buffDuration}s")}");
            Debug.Log($"  - Stack Type: {stackType}");

            if (attributeModifiers.Length > 0)
            {
                Debug.Log($"  - Attribute Modifiers: {attributeModifiers.Length} modifiers");
                foreach (var modifier in attributeModifiers)
                {
                    Debug.Log($"    * {modifier.attributeType}: {modifier.modifierType} {modifier.value}");
                }
            }

            if (specialEffects != SpecialEffect.None)
            {
                Debug.Log($"  - Special Effects: {specialEffects}");
            }
        }
    }

    /// <summary>Buff类型枚举</summary>
    public enum BuffType
    {
        Buff,       // 增益效果
        Debuff,     // 减益效果
        Positive,   // 增益（用于Visualizer�?
        Negative,   // 减益（用于Visualizer�?
        Neutral     // 中性（用于Visualizer�?
    }

    /// <summary>叠加类型枚举</summary>
    public enum StackType
    {
        None,       // 不叠加，新的覆盖旧的
        Refresh,    // 刷新持续时间
        Stack       // 增加叠加层数
    }

    /// <summary>特殊效果枚举</summary>
    [System.Flags]
    public enum SpecialEffect
    {
        None = 0,
        Stun = 1 << 0,          // 眩晕
        Silence = 1 << 1,       // 沉默
        Slow = 1 << 2,          // 减�?
        Root = 1 << 3,          // 定身
        Invisibility = 1 << 4,  // 隐身
        MagicImmune = 1 << 5,   // 魔法免疫
        Invulnerable = 1 << 6   // 无敌
    }

    /// <summary>属性修正器结构</summary>
    [System.Serializable]
    public struct AttributeModifier
    {
        [LabelText("Attribute Type")]
        /// <summary>属性类型，指定要修改的属�?/summary>
        public AttributeType attributeType;

        [LabelText("Modifier Type")]
        /// <summary>修正器类型，决定是百分比还是固定数值修�?/summary>
        public ModifierType modifierType;

        [LabelText("Value")]
        /// <summary>修正数值，具体的增减数�?/summary>
        public float value;
    }

    /// <summary>属性类型枚�?/summary>
    public enum AttributeType
    {
        Health,         // 生命�?
        Mana,          // 法力�?
        Damage,        // 攻击�?
        Armor,         // 护甲
        MagicResist,   // 魔法抗�?
        MovementSpeed, // 移动速度
        AttackSpeed,   // 攻击速度
        CriticalChance // 暴击几率
    }

    /// <summary>修正器类型枚�?/summary>
    public enum ModifierType
    {
        Flat,       // 固定数�?
        Percentage  // 百分�?
    }
}