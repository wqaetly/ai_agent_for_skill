using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 属性缩放护盾行为脚本
    /// 功能概述：提供基于多种角色属性（法术强度、当前/最大生命值等）动态计算的护盾值。
    /// 支持护盾值随技能等级缩放，可配置多个属性的缩放系数。
    /// 适用于复杂的护盾计算公式，如"基础护盾 + 40%法强 + 10%当前生命值"。
    /// 典型应用：赛恩W技能灵魂熔炉、塞拉斯W技能等需要多属性缩放的护盾技能。
    /// 护盾计算公式：基础护盾(随等级) + (法强 × 法强系数) + (生命值 × 生命值系数(随等级))
    /// </summary>
    [Serializable]
    [ActionDisplayName("属性缩放护盾")]
    public class AttributeScaledShieldAction : ISkillAction
    {
        [BoxGroup("Shield Settings")]
        [LabelText("Base Shield Amount")]
        [MinValue(0f)]
        [InfoBox("基础护盾值")]
        /// <summary>基础护盾值，技能的原始护盾数值</summary>
        public float baseShieldAmount = 60f;

        [BoxGroup("Shield Settings")]
        [LabelText("Shield Duration")]
        [MinValue(0f)]
        [InfoBox("护盾持续时间（秒），0表示永久直到被破坏")]
        /// <summary>护盾持续时间，单位为秒，超时后护盾自动消失</summary>
        public float shieldDuration = 6f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Scale with Level")]
        /// <summary>是否随技能等级缩放基础护盾值</summary>
        public bool scaleWithLevel = true;

        [BoxGroup("Scaling Settings")]
        [LabelText("Shield Per Level")]
        [MinValue(0f)]
        [ShowIf("scaleWithLevel")]
        [InfoBox("每级增加的基础护盾值")]
        /// <summary>每技能等级增加的基础护盾值</summary>
        public float shieldPerLevel = 15f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Spell Power Ratio")]
        [MinValue(0f)]
        [InfoBox("法术强度缩放比例，0.4表示40%法强")]
        /// <summary>法术强度缩放比例，决定法强对护盾值的影响</summary>
        public float spellPowerRatio = 0.4f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Health Ratio")]
        [MinValue(0f)]
        [InfoBox("生命值缩放基础比例，0.08表示8%生命值")]
        /// <summary>生命值缩放基础比例</summary>
        public float healthRatio = 0.08f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Health Ratio Per Level")]
        [MinValue(0f)]
        [ShowIf("scaleWithLevel")]
        [InfoBox("每级增加的生命值缩放比例，0.02表示每级+2%")]
        /// <summary>每技能等级增加的生命值缩放比例</summary>
        public float healthRatioPerLevel = 0.02f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Use Current Health")]
        [InfoBox("true=基于当前生命值，false=基于最大生命值")]
        /// <summary>使用当前生命值还是最大生命值进行计算</summary>
        public bool useCurrentHealth = true;

        [BoxGroup("Shield Type")]
        [LabelText("Shield Type")]
        /// <summary>护盾类型，决定护盾的防护机制</summary>
        public ShieldType shieldType = ShieldType.Absorption;

        [BoxGroup("Damage Filter")]
        [LabelText("Block Physical Damage")]
        /// <summary>阻挡物理伤害</summary>
        public bool blockPhysicalDamage = true;

        [BoxGroup("Damage Filter")]
        [LabelText("Block Magical Damage")]
        /// <summary>阻挡魔法伤害</summary>
        public bool blockMagicalDamage = true;

        [BoxGroup("Damage Filter")]
        [LabelText("Block Pure Damage")]
        /// <summary>阻挡纯净伤害</summary>
        public bool blockPureDamage = false;

        [BoxGroup("Advanced Settings")]
        [LabelText("Refreshable")]
        /// <summary>可刷新，true时重复施加护盾会刷新而不是叠加</summary>
        public bool refreshable = true;

        [BoxGroup("Advanced Settings")]
        [LabelText("Break on Spell Cast")]
        /// <summary>施法时破盾，true时目标施放技能时护盾消失</summary>
        public bool breakOnSpellCast = false;

        [BoxGroup("Advanced Settings")]
        [LabelText("Break on Attack")]
        /// <summary>攻击时破盾，true时目标进行攻击时护盾消失</summary>
        public bool breakOnAttack = false;

        [BoxGroup("Advanced Settings")]
        [LabelText("Break on Movement")]
        /// <summary>移动时破盾，true时目标移动时护盾消失</summary>
        public bool breakOnMovement = false;

        [BoxGroup("Visual Settings")]
        [LabelText("Shield Effect")]
        /// <summary>护盾视觉效果，护盾存在时的持续特效</summary>
        public GameObject shieldEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Break Effect")]
        /// <summary>破盾特效，护盾被破坏时播放的视觉效果</summary>
        public GameObject breakEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Effect Color")]
        /// <summary>护盾特效颜色</summary>
        public Color effectColor = new Color(0.5f, 0.8f, 1f, 0.6f);

        [BoxGroup("Audio Settings")]
        [LabelText("Shield Apply Sound")]
        /// <summary>护盾施加音效</summary>
        public AudioClip shieldApplySound;

        [BoxGroup("Audio Settings")]
        [LabelText("Shield Break Sound")]
        /// <summary>护盾破坏音效</summary>
        public AudioClip shieldBreakSound;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以为哪些单位施加护盾</summary>
        public TargetFilter targetFilter = TargetFilter.Self;

        /// <summary>护盾效果实例</summary>
        private GameObject shieldEffectInstance;
        /// <summary>计算出的护盾值</summary>
        private float calculatedShieldAmount;
        /// <summary>护盾结束时间</summary>
        private float shieldEndTime;

        public override string GetActionName()
        {
            return "Attribute Scaled Shield Action";
        }

        public override void OnEnter()
        {
            calculatedShieldAmount = CalculateShieldAmount();

            Debug.Log($"[AttributeScaledShieldAction] Applying shield (Amount: {calculatedShieldAmount:F1}, Duration: {shieldDuration}s)");
            Debug.Log($"[AttributeScaledShieldAction] Shield type: {shieldType}");

            ApplyShield();
            shieldEndTime = Time.time + shieldDuration;

            CreateShieldEffect();

            if (shieldApplySound != null)
            {
                Debug.Log("[AttributeScaledShieldAction] Playing shield apply sound");
            }
        }

        public override void OnTick(int relativeFrame)
        {
            float currentTime = Time.time;

            // 检查护盾是否过期
            if (shieldDuration > 0f && currentTime >= shieldEndTime)
            {
                Debug.Log("[AttributeScaledShieldAction] Shield expired due to timeout");
                RemoveShield();
                return;
            }

            // 定期输出护盾状态
            if (relativeFrame % 30 == 0)
            {
                float remainingTime = shieldEndTime - currentTime;
                Debug.Log($"[AttributeScaledShieldAction] Shield remaining: {remainingTime:F1}s");
            }

            CheckBreakConditions();
        }

        public override void OnExit()
        {
            if (shieldEffectInstance != null)
            {
                RemoveShield();
            }

            Debug.Log("[AttributeScaledShieldAction] Shield action completed");
        }

        /// <summary>计算最终护盾值</summary>
        /// <returns>计算后的护盾值</returns>
        private float CalculateShieldAmount()
        {
            int skillLevel = GetSkillLevel();

            // 基础护盾值（含等级缩放）
            float shieldAmount = baseShieldAmount;
            if (scaleWithLevel)
            {
                shieldAmount += shieldPerLevel * (skillLevel - 1);
            }

            Debug.Log($"[AttributeScaledShieldAction] Base shield (Level {skillLevel}): {shieldAmount:F1}");

            // 法强缩放
            if (spellPowerRatio > 0f)
            {
                float spellPower = GetSpellPower();
                float spScaledValue = spellPower * spellPowerRatio;
                shieldAmount += spScaledValue;
                Debug.Log($"[AttributeScaledShieldAction] + Spell Power: {spellPower:F1} × {spellPowerRatio:F2} = {spScaledValue:F1}");
            }

            // 生命值缩放（含等级缩放）
            float finalHealthRatio = healthRatio;
            if (scaleWithLevel)
            {
                finalHealthRatio += healthRatioPerLevel * (skillLevel - 1);
            }

            if (finalHealthRatio > 0f)
            {
                float healthValue = useCurrentHealth ? GetCurrentHealth() : GetMaxHealth();
                float healthScaledValue = healthValue * finalHealthRatio;
                shieldAmount += healthScaledValue;
                Debug.Log($"[AttributeScaledShieldAction] + {(useCurrentHealth ? "Current" : "Max")} Health: {healthValue:F1} × {finalHealthRatio:F2} = {healthScaledValue:F1}");
            }

            Debug.Log($"[AttributeScaledShieldAction] Total shield: {shieldAmount:F1}");
            return shieldAmount;
        }

        /// <summary>应用护盾到目标</summary>
        private void ApplyShield()
        {
            // 在实际项目中，这里会：
            // 1. 获取目标单位
            // 2. 检查是否已有相同类型的护盾
            // 3. 根据刷新规则处理
            // 4. 注册伤害处理回调

            Debug.Log($"[AttributeScaledShieldAction] Shield properties:");
            Debug.Log($"  - Shield Amount: {calculatedShieldAmount:F1}");
            Debug.Log($"  - Type: {shieldType}");
            Debug.Log($"  - Physical: {blockPhysicalDamage}, Magical: {blockMagicalDamage}, Pure: {blockPureDamage}");
            Debug.Log($"  - Refreshable: {refreshable}");
        }

        /// <summary>创建护盾视觉效果</summary>
        private void CreateShieldEffect()
        {
            if (shieldEffect != null)
            {
                var targetTransform = GetTargetTransform();
                if (targetTransform != null)
                {
                    shieldEffectInstance = UnityEngine.Object.Instantiate(shieldEffect, targetTransform.position, Quaternion.identity);
                    shieldEffectInstance.transform.SetParent(targetTransform, true);

                    // 应用颜色
                    var renderer = shieldEffectInstance.GetComponent<Renderer>();
                    if (renderer != null)
                    {
                        renderer.material.color = effectColor;
                    }
                }
            }
        }

        /// <summary>移除护盾</summary>
        private void RemoveShield()
        {
            Debug.Log("[AttributeScaledShieldAction] Removing shield");

            if (shieldEffectInstance != null)
            {
                UnityEngine.Object.Destroy(shieldEffectInstance);
                shieldEffectInstance = null;
            }
        }

        /// <summary>护盾被破坏时的处理</summary>
        private void OnShieldBroken()
        {
            Debug.Log("[AttributeScaledShieldAction] Shield broken!");

            if (breakEffect != null)
            {
                var targetTransform = GetTargetTransform();
                if (targetTransform != null)
                {
                    UnityEngine.Object.Instantiate(breakEffect, targetTransform.position, Quaternion.identity);
                }
            }

            if (shieldBreakSound != null)
            {
                Debug.Log("[AttributeScaledShieldAction] Playing shield break sound");
            }

            RemoveShield();
        }

        /// <summary>检查破盾条件</summary>
        private void CheckBreakConditions()
        {
            // 在实际项目中，这里会检查各种破盾条件
            if (breakOnSpellCast || breakOnAttack || breakOnMovement)
            {
                // 占位逻辑
            }
        }

        /// <summary>获取目标Transform（模拟）</summary>
        private Transform GetTargetTransform()
        {
            return UnityEngine.Object.FindFirstObjectByType<Transform>();
        }

        /// <summary>获取技能等级（模拟）</summary>
        private int GetSkillLevel()
        {
            return 1; // 模拟技能等级1
        }

        /// <summary>获取法术强度（模拟）</summary>
        private float GetSpellPower()
        {
            return 100f; // 模拟100法强
        }

        /// <summary>获取当前生命值（模拟）</summary>
        private float GetCurrentHealth()
        {
            return 1500f; // 模拟当前生命值
        }

        /// <summary>获取最大生命值（模拟）</summary>
        private float GetMaxHealth()
        {
            return 2000f; // 模拟最大生命值
        }
    }
}
