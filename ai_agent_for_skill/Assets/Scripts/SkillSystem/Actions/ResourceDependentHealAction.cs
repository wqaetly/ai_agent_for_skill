using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 基于资源消耗的治疗行为脚本
    /// 功能概述：消耗指定资源（怒气、法力等），并根据消耗的资源量计算治疗量�?
    /// 支持技能等级缩放、法术强度加成，适用�?消耗X资源回复Y生命"类型的技能�?
    /// 典型应用：泰达米尔的Q技能（消耗怒气回血）、吸血术（消耗法力按比例回血）等�?
    /// 治疗量计算公式：(基础�?+ 基础法强系数 * 法强) + (每资源�?+ 每资源法强系�?* 法强) * 消耗资源量
    /// </summary>
    [Serializable]
    [ActionDisplayName("资源依赖治疗")]
    public class ResourceDependentHealAction : ISkillAction
    {
        [BoxGroup("Resource Settings")]
        [LabelText("Resource Type")]
        [InfoBox("要消耗的资源类型")]
        /// <summary>资源类型，指定要消耗哪种资源（怒气、法力等�?/summary>
        public ResourceType resourceType = ResourceType.Rage;

        [BoxGroup("Resource Settings")]
        [LabelText("Consume Mode")]
        /// <summary>消耗模式，决定消耗所有资源还是固定数�?/summary>
        public ConsumeMode consumeMode = ConsumeMode.All;

        [BoxGroup("Resource Settings")]
        [LabelText("Fixed Amount")]
        [MinValue(0f)]
        [ShowIf("@consumeMode == ConsumeMode.Fixed")]
        /// <summary>固定消耗量，当模式为Fixed时消耗的资源数量</summary>
        public float fixedConsumeAmount = 50f;

        [BoxGroup("Heal Settings")]
        [LabelText("Heal Type")]
        /// <summary>治疗类型，决定恢复生命值还是法力�?/summary>
        public HealType healType = HealType.Health;

        [BoxGroup("Heal Settings")]
        [LabelText("Base Heal")]
        [MinValue(0f)]
        [InfoBox("基础治疗量（不依赖资源消耗）")]
        /// <summary>基础治疗量，不受消耗资源量影响的固定治疗�?/summary>
        public float baseHeal = 30f;

        [BoxGroup("Heal Settings")]
        [LabelText("Per Resource Heal")]
        [MinValue(0f)]
        [InfoBox("每单位消耗资源的治疗�?)]
        /// <summary>每资源治疗量，每消�?点资源额外增加的治疗�?/summary>
        public float perResourceHeal = 0.5f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Scale with Level")]
        /// <summary>随等级缩放，true时治疗量会根据技能等级调�?/summary>
        public bool scaleWithLevel = true;

        [BoxGroup("Scaling Settings")]
        [LabelText("Base Heal Per Level")]
        [MinValue(0f)]
        [ShowIf("scaleWithLevel")]
        [InfoBox("每级基础治疗量增加�?)]
        /// <summary>每级基础治疗增量，技能每提升1级，基础治疗增加的数�?/summary>
        public float baseHealPerLevel = 10f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Per Resource Heal Per Level")]
        [MinValue(0f)]
        [ShowIf("scaleWithLevel")]
        [InfoBox("每级每资源治疗量增加�?)]
        /// <summary>每级每资源治疗增量，技能每提升1级，每资源治疗增加的数�?/summary>
        public float perResourceHealPerLevel = 0.45f;

        [BoxGroup("Spell Power Settings")]
        [LabelText("Base Spell Power Ratio")]
        [Range(0f, 5f)]
        [InfoBox("基础治疗的法强系数（例如0.3表示30%法强�?)]
        /// <summary>基础法强系数，法术强度对基础治疗量的影响比例</summary>
        public float baseSpellPowerRatio = 0.3f;

        [BoxGroup("Spell Power Settings")]
        [LabelText("Per Resource Spell Power Ratio")]
        [Range(0f, 1f)]
        [InfoBox("每资源治疗的法强系数（例�?.012表示1.2%法强�?)]
        /// <summary>每资源法强系数，法术强度对每资源治疗量的影响比例</summary>
        public float perResourceSpellPowerRatio = 0.012f;

        [BoxGroup("Visual Settings")]
        [LabelText("Heal Effect")]
        /// <summary>治疗特效，播放在目标身上的治疗视觉效�?/summary>
        public GameObject healEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Resource Consume Effect")]
        /// <summary>资源消耗特效，消耗资源时的视觉效�?/summary>
        public GameObject resourceConsumeEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Effect Color")]
        /// <summary>特效颜色，自定义治疗和消耗特效的颜色</summary>
        public Color effectColor = new Color(1f, 0.3f, 0.3f, 1f); // 红色（怒气主题�?

        [BoxGroup("Audio Settings")]
        [LabelText("Heal Sound")]
        /// <summary>治疗音效，播放治疗时的音�?/summary>
        public AudioClip healSound;

        [BoxGroup("Audio Settings")]
        [LabelText("Resource Consume Sound")]
        /// <summary>资源消耗音效，消耗资源时的音�?/summary>
        public AudioClip resourceConsumeSound;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以治疗哪些单�?/summary>
        public TargetFilter targetFilter = TargetFilter.Self;

        /// <summary>实际消耗的资源量，用于记录本次技能消耗了多少资源</summary>
        private float actualConsumedResource;

        public override string GetActionName()
        {
            return "Resource Dependent Heal Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[ResourceDependentHealAction] Starting resource-dependent heal");

            // 1. 计算并消耗资�?
            actualConsumedResource = ConsumeResource();

            if (actualConsumedResource <= 0f)
            {
                Debug.LogWarning($"[ResourceDependentHealAction] No resource to consume, heal cancelled");
                return;
            }

            // 2. 计算治疗�?
            float finalHealAmount = CalculateHealAmount(actualConsumedResource);

            // 3. 应用治疗
            ApplyHeal(finalHealAmount);

            // 4. 播放效果
            PlayEffects();
        }

        public override void OnTick(int relativeFrame)
        {
            // 这是一个瞬间效果，不需要每帧更�?
        }

        public override void OnExit()
        {
            Debug.Log($"[ResourceDependentHealAction] Heal action completed");
        }

        /// <summary>消耗资�?/summary>
        /// <returns>实际消耗的资源�?/returns>
        private float ConsumeResource()
        {
            float currentResource = GetCurrentResource();
            float consumeAmount = 0f;

            switch (consumeMode)
            {
                case ConsumeMode.All:
                    consumeAmount = currentResource;
                    break;

                case ConsumeMode.Fixed:
                    consumeAmount = Mathf.Min(fixedConsumeAmount, currentResource);
                    break;
            }

            Debug.Log($"[ResourceDependentHealAction] Consuming {consumeAmount:F1} {resourceType} (had {currentResource:F1})");

            // 播放资源消耗音�?
            if (resourceConsumeSound != null)
            {
                Debug.Log($"[ResourceDependentHealAction] Playing resource consume sound");
            }

            return consumeAmount;
        }

        /// <summary>计算治疗�?/summary>
        /// <param name="consumedResource">消耗的资源�?/param>
        /// <returns>最终治疗数�?/returns>
        private float CalculateHealAmount(float consumedResource)
        {
            float spellPower = GetSpellPower();
            int skillLevel = GetSkillLevel();

            // 基础治疗量计�?
            float finalBaseHeal = baseHeal;
            if (scaleWithLevel)
            {
                finalBaseHeal += baseHealPerLevel * (skillLevel - 1);
            }
            finalBaseHeal += spellPower * baseSpellPowerRatio;

            // 每资源治疗量计算
            float finalPerResourceHeal = perResourceHeal;
            if (scaleWithLevel)
            {
                finalPerResourceHeal += perResourceHealPerLevel * (skillLevel - 1);
            }
            finalPerResourceHeal += spellPower * perResourceSpellPowerRatio;

            // 总治疗量
            float totalHeal = finalBaseHeal + (finalPerResourceHeal * consumedResource);

            Debug.Log($"[ResourceDependentHealAction] Heal Calculation:");
            Debug.Log($"  - Skill Level: {skillLevel}");
            Debug.Log($"  - Spell Power: {spellPower:F1}");
            Debug.Log($"  - Base Heal: {finalBaseHeal:F1}");
            Debug.Log($"  - Per Resource Heal: {finalPerResourceHeal:F3}");
            Debug.Log($"  - Consumed Resource: {consumedResource:F1}");
            Debug.Log($"  - Total Heal: {totalHeal:F1}");

            return totalHeal;
        }

        /// <summary>应用治疗效果</summary>
        /// <param name="healAmount">治疗数�?/param>
        private void ApplyHeal(float healAmount)
        {
            Debug.Log($"[ResourceDependentHealAction] Applying {healAmount:F1} {healType} heal to target");

            // 在实际项目中，这里会�?
            // 1. 获取目标单位
            // 2. 恢复对应的资源（生命�?法力值）
            // 3. 检查最大值限�?
            // 4. 更新UI显示

            // 播放治疗音效
            if (healSound != null)
            {
                Debug.Log($"[ResourceDependentHealAction] Playing heal sound");
            }
        }

        /// <summary>播放特效</summary>
        private void PlayEffects()
        {
            var targetTransform = GetTargetTransform();
            if (targetTransform == null) return;

            // 播放治疗特效
            if (healEffect != null)
            {
                var effect = UnityEngine.Object.Instantiate(healEffect, targetTransform.position, Quaternion.identity);
                var particleSystem = effect.GetComponent<ParticleSystem>();
                if (particleSystem != null)
                {
                    var main = particleSystem.main;
                    main.startColor = effectColor;
                }
            }

            // 播放资源消耗特�?
            if (resourceConsumeEffect != null)
            {
                UnityEngine.Object.Instantiate(resourceConsumeEffect, targetTransform.position, Quaternion.identity);
            }
        }

        /// <summary>获取当前资源量（模拟�?/summary>
        /// <returns>当前资源数�?/returns>
        private float GetCurrentResource()
        {
            // 模拟数据
            switch (resourceType)
            {
                case ResourceType.Rage: return 100f; // 满怒气
                case ResourceType.Mana: return 400f;
                case ResourceType.Health: return 750f;
                default: return 0f;
            }
        }

        /// <summary>获取法术强度（模拟）</summary>
        /// <returns>法术强度数�?/returns>
        private float GetSpellPower()
        {
            return 100f; // 模拟法术强度
        }

        /// <summary>获取技能等级（模拟�?/summary>
        /// <returns>技能等�?/returns>
        private int GetSkillLevel()
        {
            return 1; // 模拟技能等级，实际应从技能系统获�?
        }

        /// <summary>获取目标Transform（模拟）</summary>
        /// <returns>目标Transform引用</returns>
        private Transform GetTargetTransform()
        {
            return UnityEngine.Object.FindFirstObjectByType<Transform>();
        }
    }

    /// <summary>资源消耗模式枚�?/summary>
    public enum ConsumeMode
    {
        All,    // 消耗所有资�?
        Fixed   // 消耗固定数�?
    }
}
