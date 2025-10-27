using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 治疗行为脚本
    /// 功能概述：为目标单位恢复生命值或法力值，支持瞬间治疗和持续治疗两种模式。
    /// 可以配置治疗数值、治疗类型、过量治疗转换、治疗加成等参数。
    /// 适用于DOTA2中的各种恢复技能，如治疗术、回血药剂、生命汲取、魔法恢复等。
    /// </summary>
    [Serializable]
    [ActionDisplayName("治疗")]
    [ActionCategory("Support")]
    public class HealAction : ISkillAction
    {
        [BoxGroup("Heal Settings")]
        [LabelText("Heal Type")]
        /// <summary>治疗类型，决定恢复的资源类型（生命值/法力值/两者）</summary>
        public HealType healType = HealType.Health;

        [BoxGroup("Heal Settings")]
        [LabelText("Base Heal Amount")]
        [MinValue(0f)]
        /// <summary>基础治疗量，治疗技能的原始恢复数值</summary>
        public float baseHealAmount = 150f;

        [BoxGroup("Heal Settings")]
        [LabelText("Heal Mode")]
        /// <summary>治疗模式，决定是瞬间恢复还是持续恢复</summary>
        public HealMode healMode = HealMode.Instant;

        [BoxGroup("Heal Settings")]
        [LabelText("Heal Per Second")]
        [MinValue(0f)]
        [ShowIf("@healMode == HealMode.OverTime")]
        /// <summary>每秒治疗量，持续治疗模式下每秒恢复的数值</summary>
        public float healPerSecond = 25f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Scale with Caster Level")]
        /// <summary>根据施法者等级缩放，true时治疗量会受施法者等级影响</summary>
        public bool scaleWithCasterLevel = false;

        [BoxGroup("Scaling Settings")]
        [LabelText("Level Scaling Factor")]
        [MinValue(0f)]
        [ShowIf("scaleWithCasterLevel")]
        /// <summary>等级缩放系数，每级增加的治疗量倍数</summary>
        public float levelScalingFactor = 0.1f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Scale with Spell Power")]
        /// <summary>根据法术强度缩放，true时治疗量会受法术强度影响</summary>
        public bool scaleWithSpellPower = true;

        [BoxGroup("Scaling Settings")]
        [LabelText("Spell Power Ratio")]
        [Range(0f, 2f)]
        [ShowIf("scaleWithSpellPower")]
        /// <summary>法术强度系数，法术强度对治疗量的影响比例</summary>
        public float spellPowerRatio = 1f;

        [BoxGroup("Overheal Settings")]
        [LabelText("Allow Overheal")]
        /// <summary>允许过量治疗，true时可以治疗超过最大生命值的部分</summary>
        public bool allowOverheal = false;

        [BoxGroup("Overheal Settings")]
        [LabelText("Overheal Shield Duration")]
        [MinValue(0f)]
        [ShowIf("allowOverheal")]
        /// <summary>过量治疗护盾持续时间，过量治疗转换为临时护盾的持续时间</summary>
        public float overhealShieldDuration = 10f;

        [BoxGroup("Overheal Settings")]
        [LabelText("Overheal Conversion Rate")]
        [Range(0f, 1f)]
        [ShowIf("allowOverheal")]
        /// <summary>过量治疗转换率，过量部分转换为护盾的比例</summary>
        public float overhealConversionRate = 0.5f;

        [BoxGroup("Visual Settings")]
        [LabelText("Heal Effect")]
        /// <summary>治疗特效，播放在目标身上的治疗视觉效果</summary>
        public GameObject healEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Continuous Effect")]
        [ShowIf("@healMode == HealMode.OverTime")]
        /// <summary>持续治疗特效，持续治疗期间播放的视觉效果</summary>
        public GameObject continuousEffect;

        [BoxGroup("Audio Settings")]
        [LabelText("Heal Sound")]
        /// <summary>治疗音效，播放治疗时的音频效果</summary>
        public AudioClip healSound;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以治疗哪些类型的单位</summary>
        public TargetFilter targetFilter = TargetFilter.Ally;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(1)]
        /// <summary>最大目标数量，同时可以治疗的单位数量上限</summary>
        public int maxTargets = 1;

        [BoxGroup("Target Settings")]
        [LabelText("Prioritize Low Health")]
        /// <summary>优先低生命值目标，true时优先选择生命值较低的目标进行治疗</summary>
        public bool prioritizeLowHealth = true;

        /// <summary>持续治疗剩余时间，记录持续治疗模式的剩余时间</summary>
        private float remainingHealTime;
        /// <summary>下次治疗时间，控制持续治疗的间隔</summary>
        private float nextHealTick;
        /// <summary>持续效果实例，生成的持续特效引用</summary>
        private GameObject continuousEffectInstance;

        public override string GetActionName()
        {
            return "Heal Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[HealAction] Starting {healType} {healMode} heal (Base: {baseHealAmount})");

            if (healMode == HealMode.Instant)
            {
                // 瞬间治疗
                ApplyInstantHeal();
            }
            else
            {
                // 持续治疗初始化
                remainingHealTime = duration * Time.fixedDeltaTime;
                nextHealTick = 0f;

                if (continuousEffect != null)
                {
                    var targetTransform = GetTargetTransform();
                    if (targetTransform != null)
                    {
                        continuousEffectInstance = UnityEngine.Object.Instantiate(continuousEffect, targetTransform.position, Quaternion.identity);
                    }
                }
            }
        }

        public override void OnTick(int relativeFrame)
        {
            if (healMode == HealMode.OverTime)
            {
                float currentTime = relativeFrame * Time.fixedDeltaTime;

                if (currentTime >= nextHealTick && remainingHealTime > 0f)
                {
                    ApplyHealTick();
                    nextHealTick = currentTime + 1f; // 每秒治疗一次
                    remainingHealTime -= 1f;
                }
            }
        }

        public override void OnExit()
        {
            // 清理持续效果
            if (continuousEffectInstance != null)
            {
                UnityEngine.Object.Destroy(continuousEffectInstance);
                continuousEffectInstance = null;
            }

            Debug.Log($"[HealAction] Heal action completed");
        }

        /// <summary>应用瞬间治疗</summary>
        private void ApplyInstantHeal()
        {
            float finalHealAmount = CalculateFinalHealAmount();

            Debug.Log($"[HealAction] Applying instant {healType} heal: {finalHealAmount:F1}");

            // 播放治疗特效
            PlayHealEffects();

            // 在实际项目中，这里会：
            // 1. 获取目标单位
            // 2. 恢复对应的资源（生命值/法力值）
            // 3. 处理过量治疗逻辑
            // 4. 更新UI显示

            if (allowOverheal)
            {
                float overhealAmount = CalculateOverhealAmount(finalHealAmount);
                if (overhealAmount > 0)
                {
                    float shieldAmount = overhealAmount * overhealConversionRate;
                    Debug.Log($"[HealAction] Creating overheal shield: {shieldAmount:F1} for {overhealShieldDuration}s");
                }
            }
        }

        /// <summary>应用持续治疗的单次治疗</summary>
        private void ApplyHealTick()
        {
            float healAmount = healPerSecond;

            if (scaleWithSpellPower)
            {
                // 模拟法术强度加成
                float spellPower = 100f; // 模拟数值
                healAmount += spellPower * spellPowerRatio;
            }

            Debug.Log($"[HealAction] Heal tick: {healAmount:F1} {healType}");
        }

        /// <summary>计算最终治疗量</summary>
        /// <returns>经过各种加成后的最终治疗数值</returns>
        private float CalculateFinalHealAmount()
        {
            float finalAmount = baseHealAmount;

            // 等级缩放
            if (scaleWithCasterLevel)
            {
                int casterLevel = 10; // 模拟等级数据
                finalAmount += baseHealAmount * levelScalingFactor * casterLevel;
            }

            // 法术强度缩放
            if (scaleWithSpellPower)
            {
                float spellPower = 150f; // 模拟法术强度数据
                finalAmount += spellPower * spellPowerRatio;
            }

            return finalAmount;
        }

        /// <summary>计算过量治疗数值</summary>
        /// <param name="healAmount">治疗数值</param>
        /// <returns>过量治疗的数值</returns>
        private float CalculateOverhealAmount(float healAmount)
        {
            // 在实际项目中，这里会获取目标的当前生命值和最大生命值
            float currentHealth = 800f; // 模拟当前生命值
            float maxHealth = 1000f;    // 模拟最大生命值

            float availableHealth = maxHealth - currentHealth;
            if (healAmount > availableHealth)
            {
                return healAmount - availableHealth;
            }

            return 0f;
        }

        /// <summary>播放治疗效果</summary>
        private void PlayHealEffects()
        {
            var targetTransform = GetTargetTransform();
            if (targetTransform != null)
            {
                // 播放视觉效果
                if (healEffect != null)
                {
                    UnityEngine.Object.Instantiate(healEffect, targetTransform.position, Quaternion.identity);
                }

                // 播放音效
                if (healSound != null)
                {
                    // AudioSource.PlayClipAtPoint(healSound, targetTransform.position);
                    Debug.Log($"[HealAction] Playing heal sound at {targetTransform.position}");
                }
            }
        }

        /// <summary>获取目标Transform（模拟实现）</summary>
        /// <returns>目标Transform引用</returns>
        private Transform GetTargetTransform()
        {
            // 在实际项目中，这里会根据目标筛选器获取实际目标
            return UnityEngine.Object.FindFirstObjectByType<Transform>();
        }
    }

    /// <summary>治疗类型枚举</summary>
    public enum HealType
    {
        Health,     // 生命值
        Mana,       // 法力值
        Both        // 同时恢复生命值和法力值
    }

    /// <summary>治疗模式枚举</summary>
    public enum HealMode
    {
        Instant,    // 瞬间治疗
        OverTime    // 持续治疗
    }
}