using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 属性缩放伤害行为脚本
    /// 功能概述：造成基于多种角色属性（攻击力、法强、生命值等）缩放的伤害。
    /// 支持灵活配置多个属性缩放系数，可以区分总攻击力和额外攻击力。
    /// 适用于复杂的伤害计算公式，如"基础伤害 + 130%额外攻击力 + 80%法强"。
    /// 典型应用：泰达米尔E技能、瑞文R技能等需要多属性缩放的技能。
    /// 伤害计算公式：基础伤害(随等级) + Σ(属性值 × 缩放系数)
    /// </summary>
    [Serializable]
    [ActionDisplayName("属性缩放伤害")]
    public class AttributeScaledDamageAction : ISkillAction
    {
        [BoxGroup("Damage Settings")]
        [LabelText("Base Damage")]
        [MinValue(0f)]
        [InfoBox("基础伤害值")]
        /// <summary>基础伤害值，技能的原始伤害数值</summary>
        public float baseDamage = 75f;

        [BoxGroup("Damage Settings")]
        [LabelText("Damage Type")]
        /// <summary>伤害类型，决定伤害如何被防御属性减免</summary>
        public DamageType damageType = DamageType.Physical;

        [BoxGroup("Damage Settings")]
        [LabelText("Damage Variance")]
        [Range(0f, 0.5f)]
        [InfoBox("伤害浮动范围，0.1表示±10%的伤害浮动")]
        /// <summary>伤害浮动系数，产生随机伤害变化</summary>
        public float damageVariance = 0f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Scale with Level")]
        /// <summary>是否随技能等级缩放基础伤害</summary>
        public bool scaleWithLevel = true;

        [BoxGroup("Scaling Settings")]
        [LabelText("Damage Per Level")]
        [MinValue(0f)]
        [ShowIf("scaleWithLevel")]
        [InfoBox("每级增加的基础伤害")]
        /// <summary>每技能等级增加的基础伤害值</summary>
        public float damagePerLevel = 30f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Attribute Scalings")]
        [InfoBox("属性缩放配置，可以添加多个不同属性的缩放")]
        /// <summary>属性缩放数组，定义伤害如何基于角色属性缩放</summary>
        public AttributeScaling[] attributeScalings = new AttributeScaling[]
        {
            new AttributeScaling { attributeType = ScalingAttributeType.BonusAttackDamage, scalingRatio = 1.3f },
            new AttributeScaling { attributeType = ScalingAttributeType.SpellPower, scalingRatio = 0.8f }
        };

        [BoxGroup("Critical Settings")]
        [LabelText("Can Critical")]
        /// <summary>是否可以暴击</summary>
        public bool canCritical = true;

        [BoxGroup("Critical Settings")]
        [LabelText("Use Caster Crit Chance")]
        [ShowIf("canCritical")]
        /// <summary>使用施法者的暴击率，false时使用下面的固定暴击率</summary>
        public bool useCasterCritChance = true;

        [BoxGroup("Critical Settings")]
        [LabelText("Fixed Critical Chance")]
        [Range(0f, 1f)]
        [ShowIf("@canCritical && !useCasterCritChance")]
        /// <summary>固定暴击率，仅在不使用施法者暴击率时有效</summary>
        public float fixedCriticalChance = 0f;

        [BoxGroup("Critical Settings")]
        [LabelText("Critical Multiplier")]
        [MinValue(1f)]
        [ShowIf("canCritical")]
        /// <summary>暴击倍数，暴击时伤害的放大倍数</summary>
        public float criticalMultiplier = 2f;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以攻击哪些单位</summary>
        public TargetFilter targetFilter = TargetFilter.Enemy;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(1)]
        /// <summary>最大目标数量，AOE技能可以命中的最大单位数</summary>
        public int maxTargets = 5;

        [BoxGroup("Target Settings")]
        [LabelText("Damage Radius")]
        [MinValue(0f)]
        [InfoBox("伤害半径，0表示单体伤害")]
        /// <summary>伤害半径，0表示单体，大于0表示范围伤害</summary>
        public float damageRadius = 3f;

        [BoxGroup("Visual Settings")]
        [LabelText("Damage Effect")]
        /// <summary>伤害特效，命中目标时的视觉效果</summary>
        public GameObject damageEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Critical Effect")]
        [ShowIf("canCritical")]
        /// <summary>暴击特效，暴击时的额外视觉效果</summary>
        public GameObject criticalEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Effect Color")]
        /// <summary>特效颜色</summary>
        public Color effectColor = new Color(1f, 0.5f, 0f, 1f);

        [BoxGroup("Audio Settings")]
        [LabelText("Hit Sound")]
        /// <summary>命中音效</summary>
        public AudioClip hitSound;

        [BoxGroup("Audio Settings")]
        [LabelText("Critical Sound")]
        [ShowIf("canCritical")]
        /// <summary>暴击音效</summary>
        public AudioClip criticalSound;

        public override string GetActionName()
        {
            return "Attribute Scaled Damage Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[AttributeScaledDamageAction] Starting damage calculation");
            ExecuteDamage();
        }

        public override void OnTick(int relativeFrame)
        {
            // 伤害通常在OnEnter执行，这里留空
        }

        public override void OnExit()
        {
            Debug.Log($"[AttributeScaledDamageAction] Damage action completed");
        }

        /// <summary>执行伤害计算和应用</summary>
        private void ExecuteDamage()
        {
            float finalDamage = CalculateDamage();
            bool isCritical = RollCritical();

            if (isCritical)
            {
                finalDamage *= criticalMultiplier;
                Debug.Log($"[AttributeScaledDamageAction] CRITICAL HIT! Damage: {finalDamage:F1}");
            }
            else
            {
                Debug.Log($"[AttributeScaledDamageAction] Normal hit. Damage: {finalDamage:F1}");
            }

            // 应用伤害浮动
            if (damageVariance > 0f)
            {
                float variance = UnityEngine.Random.Range(-damageVariance, damageVariance);
                finalDamage *= (1f + variance);
            }

            ApplyDamageToTargets(finalDamage, isCritical);
        }

        /// <summary>计算最终伤害值</summary>
        /// <returns>计算后的伤害值</returns>
        private float CalculateDamage()
        {
            int skillLevel = GetSkillLevel();

            // 基础伤害（含等级缩放）
            float damage = baseDamage;
            if (scaleWithLevel)
            {
                damage += damagePerLevel * (skillLevel - 1);
            }

            Debug.Log($"[AttributeScaledDamageAction] Base damage (Level {skillLevel}): {damage:F1}");

            // 属性缩放加成
            if (attributeScalings != null && attributeScalings.Length > 0)
            {
                foreach (var scaling in attributeScalings)
                {
                    float attributeValue = GetAttributeValue(scaling.attributeType);
                    float scaledValue = attributeValue * scaling.scalingRatio;
                    damage += scaledValue;

                    Debug.Log($"[AttributeScaledDamageAction] + {scaling.attributeType}: {attributeValue:F1} × {scaling.scalingRatio:F2} = {scaledValue:F1}");
                }
            }

            Debug.Log($"[AttributeScaledDamageAction] Total damage: {damage:F1}");
            return damage;
        }

        /// <summary>判断是否暴击</summary>
        /// <returns>是否暴击</returns>
        private bool RollCritical()
        {
            if (!canCritical) return false;

            float critChance = useCasterCritChance ? GetCasterCriticalChance() : fixedCriticalChance;
            return UnityEngine.Random.value < critChance;
        }

        /// <summary>对目标应用伤害</summary>
        /// <param name="damage">伤害值</param>
        /// <param name="isCritical">是否暴击</param>
        private void ApplyDamageToTargets(float damage, bool isCritical)
        {
            Debug.Log($"[AttributeScaledDamageAction] Applying {damage:F1} {damageType} damage to targets (Radius: {damageRadius})");
            Debug.Log($"[AttributeScaledDamageAction] Max targets: {maxTargets}, Filter: {targetFilter}");

            // 在实际项目中，这里会：
            // 1. 在damageRadius范围内查找符合targetFilter的目标
            // 2. 对每个目标应用伤害
            // 3. 触发伤害事件（用于怒气生成等）
            // 4. 播放特效和音效

            PlayEffects(isCritical);
        }

        /// <summary>播放特效和音效</summary>
        /// <param name="isCritical">是否暴击</param>
        private void PlayEffects(bool isCritical)
        {
            // 播放视觉特效
            GameObject effectToPlay = isCritical && criticalEffect != null ? criticalEffect : damageEffect;
            if (effectToPlay != null)
            {
                Debug.Log($"[AttributeScaledDamageAction] Playing {(isCritical ? "critical" : "normal")} effect");
            }

            // 播放音效
            AudioClip soundToPlay = isCritical && criticalSound != null ? criticalSound : hitSound;
            if (soundToPlay != null)
            {
                Debug.Log($"[AttributeScaledDamageAction] Playing {(isCritical ? "critical" : "hit")} sound");
            }
        }

        /// <summary>获取属性值</summary>
        /// <param name="attributeType">属性类型</param>
        /// <returns>属性数值</returns>
        private float GetAttributeValue(ScalingAttributeType attributeType)
        {
            // 模拟数据
            switch (attributeType)
            {
                case ScalingAttributeType.TotalAttackDamage:
                    return 150f; // 模拟：基础100 + 装备50

                case ScalingAttributeType.BonusAttackDamage:
                    return 50f; // 模拟：装备提供的额外攻击力

                case ScalingAttributeType.SpellPower:
                    return 100f; // 模拟法术强度

                case ScalingAttributeType.MaxHealth:
                    return 2000f; // 模拟最大生命值

                case ScalingAttributeType.CurrentHealth:
                    return 1500f; // 模拟当前生命值

                case ScalingAttributeType.MissingHealth:
                    return 500f; // 模拟已损失生命值

                case ScalingAttributeType.Armor:
                    return 80f; // 模拟护甲

                case ScalingAttributeType.MagicResist:
                    return 50f; // 模拟魔抗

                default:
                    return 0f;
            }
        }

        /// <summary>获取技能等级（模拟）</summary>
        /// <returns>技能等级</returns>
        private int GetSkillLevel()
        {
            return 1; // 模拟技能等级，实际应从技能系统获取
        }

        /// <summary>获取施法者暴击率（模拟）</summary>
        /// <returns>暴击率</returns>
        private float GetCasterCriticalChance()
        {
            return 0.3f; // 模拟30%暴击率
        }
    }

    /// <summary>属性缩放配置结构</summary>
    [System.Serializable]
    public struct AttributeScaling
    {
        [LabelText("Attribute Type")]
        /// <summary>属性类型</summary>
        public ScalingAttributeType attributeType;

        [LabelText("Scaling Ratio")]
        [InfoBox("缩放比例，1.3表示130%，0.8表示80%")]
        /// <summary>缩放比例，属性对伤害的影响系数</summary>
        public float scalingRatio;
    }

    /// <summary>可用于伤害缩放的属性类型</summary>
    public enum ScalingAttributeType
    {
        TotalAttackDamage,      // 总攻击力（基础+额外）
        BonusAttackDamage,      // 额外攻击力（仅装备/符文提供的）
        SpellPower,             // 法术强度
        MaxHealth,              // 最大生命值
        CurrentHealth,          // 当前生命值
        MissingHealth,          // 已损失生命值
        Armor,                  // 护甲
        MagicResist,            // 魔法抗性
        MovementSpeed,          // 移动速度
        AttackSpeed             // 攻击速度
    }
}
