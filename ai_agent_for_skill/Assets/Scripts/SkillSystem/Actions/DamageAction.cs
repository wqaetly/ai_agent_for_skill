using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 伤害行为脚本
    /// 功能概述：对目标造成指定类型和数值的伤害，支持物理、魔法、纯净三种伤害类型�?
    /// 以及暴击、吸血、法术吸血等特殊效果。可以配置伤害范围、目标筛选等参数�?
    /// 适用于DOTA2中的各种攻击技能，如普通攻击、技能伤害等�?
    /// </summary>
    [Serializable]
    [ActionDisplayName("伤害")]
    [ActionDescription("对目标造成伤害。支持物理伤害、魔法伤害、纯粹伤害三种类型，可配置基础伤害值、伤害浮动、暴击率、暴击倍数、生命偷取、法术吸血等效果。支持溅射伤害、穿透护甲、真实伤害等特性。常用于攻击技能、法术伤害、dot持续伤害等各类造成伤害的技能。不包含控制效果，纯粹用于扣血�?)]
    public class DamageAction : ISkillAction
    {
        [BoxGroup("Damage Settings")]
        [LabelText("Base Damage")]
        [MinValue(0)]
        /// <summary>基础伤害值，技能造成的原始伤害数�?/summary>
        public float baseDamage = 100f;

        [BoxGroup("Damage Settings")]
        [LabelText("Damage Type")]
        /// <summary>伤害类型，决定伤害如何被防御属性减免（物理/魔法/纯净�?/summary>
        public DamageType damageType = DamageType.Physical;

        [BoxGroup("Damage Settings")]
        [LabelText("Damage Variance")]
        [Range(0f, 0.5f)]
        [InfoBox("伤害浮动范围�?.2表示±20%的伤害浮�?)]
        /// <summary>伤害浮动系数，用于产生随机伤害变化，增加战斗的不确定�?/summary>
        public float damageVariance = 0.1f;

        [BoxGroup("Critical Settings")]
        [LabelText("Critical Chance")]
        [Range(0f, 1f)]
        /// <summary>暴击概率�?-1之间的值，决定造成暴击的几�?/summary>
        public float criticalChance = 0f;

        [BoxGroup("Critical Settings")]
        [LabelText("Critical Multiplier")]
        [MinValue(1f)]
        /// <summary>暴击倍数，暴击时伤害的放大倍数，通常�?倍或更高</summary>
        public float criticalMultiplier = 2f;

        [BoxGroup("Special Effects")]
        [LabelText("Life Steal Percentage")]
        [Range(0f, 1f)]
        /// <summary>生命偷取百分比，物理伤害转换为生命值回复的比例</summary>
        public float lifeStealPercentage = 0f;

        [BoxGroup("Special Effects")]
        [LabelText("Spell Vamp Percentage")]
        [Range(0f, 1f)]
        /// <summary>法术吸血百分比，魔法伤害转换为生命值回复的比例</summary>
        public float spellVampPercentage = 0f;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以对哪些单位造成伤害（敌�?友军/自己/所有）</summary>
        public TargetFilter targetFilter = TargetFilter.Enemy;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(1)]
        /// <summary>最大目标数量，限制单次伤害行为能够影响的目标数量上�?/summary>
        public int maxTargets = 1;

        [BoxGroup("Target Settings")]
        [LabelText("Damage Radius")]
        [MinValue(0f)]
        /// <summary>伤害半径�?表示单体伤害，大�?表示范围伤害的作用半�?/summary>
        public float damageRadius = 0f;

        /// <summary>伤害别名，用于Visualizer兼容</summary>
        public float damage => baseDamage;

        /// <summary>每次伤害值（用于持续伤害�?/summary>
        public float damagePerTick = 0f;

        /// <summary>持续时间，用于持续伤害效�?/summary>
        public float duration = 0f;

        public override string GetActionName()
        {
            return "Damage Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[DamageAction] Preparing to deal {baseDamage} {damageType} damage");
            // 在实际项目中，这里会获取目标并计算最终伤�?
        }

        public override void OnTick(int relativeFrame)
        {
            // 伤害通常在第一帧执行，但可以支持持续伤�?
            if (relativeFrame == 0)
            {
                ExecuteDamage();
            }
        }

        public override void OnExit()
        {
            Debug.Log($"[DamageAction] Damage action completed");
        }

        /// <summary>执行伤害计算和应用的核心逻辑</summary>
        private void ExecuteDamage()
        {
            // 计算最终伤害�?
            float finalDamage = baseDamage;

            // 添加伤害浮动
            if (damageVariance > 0)
            {
                float variance = UnityEngine.Random.Range(-damageVariance, damageVariance);
                finalDamage *= (1f + variance);
            }

            // 判断暴击
            bool isCritical = UnityEngine.Random.value < criticalChance;
            if (isCritical)
            {
                finalDamage *= criticalMultiplier;
                Debug.Log($"[DamageAction] Critical hit! Damage: {finalDamage:F1}");
            }
            else
            {
                Debug.Log($"[DamageAction] Normal hit. Damage: {finalDamage:F1}");
            }

            // 生命偷取计算
            if (lifeStealPercentage > 0 && damageType == DamageType.Physical)
            {
                float healAmount = finalDamage * lifeStealPercentage;
                Debug.Log($"[DamageAction] Life steal healing: {healAmount:F1}");
            }

            // 法术吸血计算
            if (spellVampPercentage > 0 && damageType == DamageType.Magical)
            {
                float healAmount = finalDamage * spellVampPercentage;
                Debug.Log($"[DamageAction] Spell vamp healing: {healAmount:F1}");
            }
        }
    }

    /// <summary>伤害类型枚举</summary>
    public enum DamageType
    {
        Physical,   // 物理伤害，受护甲减免
        Magical,    // 魔法伤害，受魔法抗性减�?
        Pure        // 纯净伤害，无视防�?
    }

    /// <summary>目标筛选器枚举</summary>
    public enum TargetFilter
    {
        Enemy,      // 敌人
        Ally,       // 友军
        Self,       // 自己
        All         // 所有单�?
    }
}