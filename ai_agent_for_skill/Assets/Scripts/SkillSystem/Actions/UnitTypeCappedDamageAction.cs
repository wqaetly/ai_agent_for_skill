using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 单位类型伤害上限行为脚本
    /// 功能概述：造成基于属性缩放的伤害，并对特定单位类型应用伤害上限。
    /// 支持对不同单位类型（英雄、小兵、野怪等）设置独立的伤害上限值。
    /// 适用于需要区分对英雄和非英雄单位伤害的技能，防止对小兵/野怪造成过高伤害。
    /// 典型应用：赛恩W引爆、塞拉斯被动等对非英雄单位有伤害上限的技能。
    /// 伤害计算公式：min(基础伤害 + 属性缩放, 单位类型伤害上限)
    /// </summary>
    [Serializable]
    [ActionDisplayName("单位类型伤害上限")]
    public class UnitTypeCappedDamageAction : ISkillAction
    {
        [BoxGroup("Damage Settings")]
        [LabelText("Base Damage")]
        [MinValue(0f)]
        [InfoBox("基础伤害值")]
        /// <summary>基础伤害值，技能的原始伤害数值</summary>
        public float baseDamage = 40f;

        [BoxGroup("Damage Settings")]
        [LabelText("Damage Type")]
        /// <summary>伤害类型，决定伤害如何被防御属性减免</summary>
        public DamageType damageType = DamageType.Magical;

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
        public float damagePerLevel = 25f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Spell Power Ratio")]
        [MinValue(0f)]
        [InfoBox("法术强度缩放比例，0.4表示40%法强")]
        /// <summary>法术强度缩放比例</summary>
        public float spellPowerRatio = 0.4f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Max Health Ratio")]
        [MinValue(0f)]
        [InfoBox("最大生命值缩放比例，0.14表示14%最大生命")]
        /// <summary>最大生命值缩放比例（施法者的最大生命值）</summary>
        public float maxHealthRatio = 0.14f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Use Target Max Health")]
        [InfoBox("true=使用目标最大生命，false=使用施法者最大生命")]
        /// <summary>使用目标的最大生命值还是施法者的最大生命值</summary>
        public bool useTargetMaxHealth = false;

        [BoxGroup("Damage Cap Settings")]
        [LabelText("Damage Caps")]
        [InfoBox("为不同单位类型配置伤害上限，未配置的单位类型无伤害上限")]
        [ListDrawerSettings(ShowIndexLabels = true, ListElementLabelName = "GetCapLabel")]
        /// <summary>单位类型伤害上限配置数组</summary>
        public UnitTypeDamageCap[] damageCaps = new UnitTypeDamageCap[]
        {
            new UnitTypeDamageCap { unitType = UnitType.Minion, damageCap = 400f },
            new UnitTypeDamageCap { unitType = UnitType.Monster, damageCap = 400f }
        };

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以攻击哪些单位</summary>
        public TargetFilter targetFilter = TargetFilter.Enemy;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(1)]
        /// <summary>最大目标数量，AOE技能可以命中的最大单位数</summary>
        public int maxTargets = 10;

        [BoxGroup("Target Settings")]
        [LabelText("Damage Radius")]
        [MinValue(0f)]
        [InfoBox("伤害半径，0表示单体伤害")]
        /// <summary>伤害半径，0表示单体，大于0表示范围伤害</summary>
        public float damageRadius = 5f;

        [BoxGroup("Visual Settings")]
        [LabelText("Damage Effect")]
        /// <summary>伤害特效，命中目标时的视觉效果</summary>
        public GameObject damageEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Capped Damage Effect")]
        [InfoBox("伤害被上限限制时的特殊视觉效果（可选）")]
        /// <summary>伤害达到上限时的特殊视觉效果</summary>
        public GameObject cappedDamageEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Effect Color")]
        /// <summary>特效颜色</summary>
        public Color effectColor = new Color(1f, 0.3f, 0f, 1f);

        [BoxGroup("Audio Settings")]
        [LabelText("Hit Sound")]
        /// <summary>命中音效</summary>
        public AudioClip hitSound;

        [BoxGroup("Audio Settings")]
        [LabelText("Capped Hit Sound")]
        /// <summary>伤害达到上限时的特殊音效</summary>
        public AudioClip cappedHitSound;

        public override string GetActionName()
        {
            return "Unit Type Capped Damage Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[UnitTypeCappedDamageAction] Starting damage calculation");
            ExecuteDamage();
        }

        public override void OnTick(int relativeFrame)
        {
            // 伤害通常在OnEnter执行，这里留空
        }

        public override void OnExit()
        {
            Debug.Log($"[UnitTypeCappedDamageAction] Damage action completed");
        }

        /// <summary>执行伤害计算和应用</summary>
        private void ExecuteDamage()
        {
            float baseDamageValue = CalculateBaseDamage();
            Debug.Log($"[UnitTypeCappedDamageAction] Base calculated damage: {baseDamageValue:F1}");

            ApplyDamageToTargets(baseDamageValue);
        }

        /// <summary>计算基础伤害值（不含上限）</summary>
        /// <returns>计算后的伤害值</returns>
        private float CalculateBaseDamage()
        {
            int skillLevel = GetSkillLevel();

            // 基础伤害（含等级缩放）
            float damage = baseDamage;
            if (scaleWithLevel)
            {
                damage += damagePerLevel * (skillLevel - 1);
            }

            Debug.Log($"[UnitTypeCappedDamageAction] Base damage (Level {skillLevel}): {damage:F1}");

            // 法强缩放
            if (spellPowerRatio > 0f)
            {
                float spellPower = GetSpellPower();
                float spScaledValue = spellPower * spellPowerRatio;
                damage += spScaledValue;
                Debug.Log($"[UnitTypeCappedDamageAction] + Spell Power: {spellPower:F1} × {spellPowerRatio:F2} = {spScaledValue:F1}");
            }

            // 最大生命值缩放
            if (maxHealthRatio > 0f)
            {
                float maxHealth = useTargetMaxHealth ? GetTargetMaxHealth() : GetCasterMaxHealth();
                float healthScaledValue = maxHealth * maxHealthRatio;
                damage += healthScaledValue;
                Debug.Log($"[UnitTypeCappedDamageAction] + {(useTargetMaxHealth ? "Target" : "Caster")} Max Health: {maxHealth:F1} × {maxHealthRatio:F2} = {healthScaledValue:F1}");
            }

            Debug.Log($"[UnitTypeCappedDamageAction] Total uncapped damage: {damage:F1}");
            return damage;
        }

        /// <summary>对目标应用伤害（考虑单位类型上限）</summary>
        /// <param name="baseDamageValue">基础伤害值</param>
        private void ApplyDamageToTargets(float baseDamageValue)
        {
            Debug.Log($"[UnitTypeCappedDamageAction] Applying {damageType} damage to targets (Radius: {damageRadius})");
            Debug.Log($"[UnitTypeCappedDamageAction] Max targets: {maxTargets}, Filter: {targetFilter}");

            // 在实际项目中，这里会：
            // 1. 在damageRadius范围内查找符合targetFilter的目标
            // 2. 对每个目标根据单位类型应用伤害上限
            // 3. 应用最终伤害
            // 4. 播放对应的特效和音效

            // 模拟对不同单位类型应用伤害
            SimulateDamageApplication(baseDamageValue, UnitType.Hero);
            SimulateDamageApplication(baseDamageValue, UnitType.Minion);
            SimulateDamageApplication(baseDamageValue, UnitType.Monster);
        }

        /// <summary>模拟对特定单位类型应用伤害</summary>
        /// <param name="baseDamageValue">基础伤害值</param>
        /// <param name="unitType">单位类型</param>
        private void SimulateDamageApplication(float baseDamageValue, UnitType unitType)
        {
            float finalDamage = ApplyDamageCap(baseDamageValue, unitType);
            bool isCapped = finalDamage < baseDamageValue;

            Debug.Log($"[UnitTypeCappedDamageAction] {unitType}: {baseDamageValue:F1} → {finalDamage:F1} {(isCapped ? "(CAPPED)" : "")}");

            PlayEffects(isCapped);
        }

        /// <summary>应用单位类型伤害上限</summary>
        /// <param name="damage">原始伤害值</param>
        /// <param name="unitType">单位类型</param>
        /// <returns>应用上限后的伤害值</returns>
        private float ApplyDamageCap(float damage, UnitType unitType)
        {
            if (damageCaps == null || damageCaps.Length == 0)
            {
                return damage;
            }

            foreach (var cap in damageCaps)
            {
                if (cap.unitType == unitType && cap.damageCap > 0f)
                {
                    return Mathf.Min(damage, cap.damageCap);
                }
            }

            return damage; // 未配置上限的单位类型，返回原始伤害
        }

        /// <summary>播放特效和音效</summary>
        /// <param name="isCapped">是否触发了伤害上限</param>
        private void PlayEffects(bool isCapped)
        {
            // 播放视觉特效
            GameObject effectToPlay = isCapped && cappedDamageEffect != null ? cappedDamageEffect : damageEffect;
            if (effectToPlay != null)
            {
                Debug.Log($"[UnitTypeCappedDamageAction] Playing {(isCapped ? "capped" : "normal")} damage effect");
            }

            // 播放音效
            AudioClip soundToPlay = isCapped && cappedHitSound != null ? cappedHitSound : hitSound;
            if (soundToPlay != null)
            {
                Debug.Log($"[UnitTypeCappedDamageAction] Playing {(isCapped ? "capped" : "normal")} hit sound");
            }
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

        /// <summary>获取施法者最大生命值（模拟）</summary>
        private float GetCasterMaxHealth()
        {
            return 2000f; // 模拟施法者2000最大生命
        }

        /// <summary>获取目标最大生命值（模拟）</summary>
        private float GetTargetMaxHealth()
        {
            return 1500f; // 模拟目标1500最大生命
        }
    }

    /// <summary>单位类型伤害上限配置结构</summary>
    [System.Serializable]
    public struct UnitTypeDamageCap
    {
        [LabelText("Unit Type")]
        /// <summary>单位类型</summary>
        public UnitType unitType;

        [LabelText("Damage Cap")]
        [MinValue(0f)]
        [InfoBox("伤害上限，0表示无上限")]
        /// <summary>伤害上限值，超过此值的伤害将被限制</summary>
        public float damageCap;

        /// <summary>用于Odin列表显示的标签</summary>
        public string GetCapLabel()
        {
            return $"{unitType} (Cap: {damageCap})";
        }
    }

    /// <summary>单位类型枚举</summary>
    public enum UnitType
    {
        Hero,       // 英雄
        Minion,     // 小兵
        Monster,    // 野怪（中立生物）
        Building,   // 建筑
        Ward        // 守卫/眼
    }
}
