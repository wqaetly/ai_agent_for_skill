using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 护盾行为脚本
    /// 功能概述：为目标单位提供各种类型的护盾保护，包括物理护盾、魔法护盾、吸收护盾等�?
    /// 支持护盾值设置、持续时间管理、护盾类型配置、破盾反馈等功能�?
    /// 适用于DOTA2中的防护技能，如魔法护盾、骨骼护甲、困兽之斗、林肯法球等护盾类技能�?
    /// </summary>
    [Serializable]
    [ActionDisplayName("护盾")]
    public class ShieldAction : ISkillAction
    {
        [BoxGroup("Shield Settings")]
        [LabelText("Shield Type")]
        /// <summary>护盾类型，决定护盾的防护机制和特�?/summary>
        public ShieldType shieldType = ShieldType.Absorption;

        [BoxGroup("Shield Settings")]
        [LabelText("Shield Amount")]
        [MinValue(0f)]
        /// <summary>护盾数值，护盾可以吸收的伤害总量或提供的防护数�?/summary>
        public float shieldAmount = 200f;

        [BoxGroup("Shield Settings")]
        [LabelText("Shield Duration")]
        [MinValue(0f)]
        [InfoBox("护盾持续时间�?表示直到被破坏为�?)]
        /// <summary>护盾持续时间，单位为秒，超时后护盾自动消�?/summary>
        public float shieldDuration = 15f;

        [BoxGroup("Damage Filter")]
        [LabelText("Block Physical Damage")]
        /// <summary>阻挡物理伤害，true时护盾可以防护物理伤�?/summary>
        public bool blockPhysicalDamage = true;

        [BoxGroup("Damage Filter")]
        [LabelText("Block Magical Damage")]
        /// <summary>阻挡魔法伤害，true时护盾可以防护魔法伤�?/summary>
        public bool blockMagicalDamage = true;

        [BoxGroup("Damage Filter")]
        [LabelText("Block Pure Damage")]
        /// <summary>阻挡纯净伤害，true时护盾可以防护纯净伤害</summary>
        public bool blockPureDamage = false;

        [BoxGroup("Advanced Settings")]
        [LabelText("Absorption Rate")]
        [Range(0f, 1f)]
        [ShowIf("@shieldType == ShieldType.Absorption")]
        /// <summary>吸收比例，吸收型护盾吸收伤害的百分比</summary>
        public float absorptionRate = 1f;

        [BoxGroup("Advanced Settings")]
        [LabelText("Damage Reduction")]
        [Range(0f, 1f)]
        [ShowIf("@shieldType == ShieldType.DamageReduction")]
        /// <summary>伤害减免比例，减伤型护盾降低伤害的百分比</summary>
        public float damageReduction = 0.5f;

        [BoxGroup("Advanced Settings")]
        [LabelText("Reflect Damage")]
        /// <summary>反射伤害，true时护盾会将部分伤害反射给攻击�?/summary>
        public bool reflectDamage = false;

        [BoxGroup("Advanced Settings")]
        [LabelText("Reflect Percentage")]
        [Range(0f, 2f)]
        [ShowIf("reflectDamage")]
        /// <summary>反射百分比，反射给攻击者的伤害比例</summary>
        public float reflectPercentage = 0.3f;

        [BoxGroup("Refresh Settings")]
        [LabelText("Refreshable")]
        /// <summary>可刷新，true时重复施加护盾会刷新而不是叠�?/summary>
        public bool refreshable = true;

        [BoxGroup("Refresh Settings")]
        [LabelText("Stackable")]
        [ShowIf("@refreshable == false")]
        /// <summary>可叠加，true时多个护盾可以同时存在并叠加效果</summary>
        public bool stackable = false;

        [BoxGroup("Refresh Settings")]
        [LabelText("Max Stacks")]
        [MinValue(1)]
        [ShowIf("stackable")]
        /// <summary>最大叠加层数，可叠加护盾的层数上限</summary>
        public int maxStacks = 3;

        [BoxGroup("Break Conditions")]
        [LabelText("Break on Spell Cast")]
        /// <summary>施法时破盾，true时目标施放技能时护盾消失</summary>
        public bool breakOnSpellCast = false;

        [BoxGroup("Break Conditions")]
        [LabelText("Break on Attack")]
        /// <summary>攻击时破盾，true时目标进行攻击时护盾消失</summary>
        public bool breakOnAttack = false;

        [BoxGroup("Break Conditions")]
        [LabelText("Break on Movement")]
        /// <summary>移动时破盾，true时目标移动时护盾消失</summary>
        public bool breakOnMovement = false;

        [BoxGroup("Visual Settings")]
        [LabelText("Shield Effect")]
        /// <summary>护盾视觉效果，护盾存在时的持续特�?/summary>
        public GameObject shieldEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Break Effect")]
        /// <summary>破盾特效，护盾被破坏时播放的视觉效果</summary>
        public GameObject breakEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Reflect Effect")]
        [ShowIf("reflectDamage")]
        /// <summary>反射特效，反射伤害时播放的视觉效�?/summary>
        public GameObject reflectEffect;

        [BoxGroup("Audio Settings")]
        [LabelText("Shield Apply Sound")]
        /// <summary>护盾施加音效，护盾生效时的音�?/summary>
        public AudioClip shieldApplySound;

        [BoxGroup("Audio Settings")]
        [LabelText("Shield Break Sound")]
        /// <summary>护盾破坏音效，护盾被破坏时的音频</summary>
        public AudioClip shieldBreakSound;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以为哪些单位施加护盾</summary>
        public TargetFilter targetFilter = TargetFilter.Ally;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(1)]
        /// <summary>最大目标数量，同时可以保护的单位数�?/summary>
        public int maxTargets = 1;

        /// <summary>护盾效果实例，生成的视觉效果引用</summary>
        private GameObject shieldEffectInstance;
        /// <summary>当前护盾剩余值，护盾还能吸收的伤害量</summary>
        private float currentShieldAmount;
        /// <summary>护盾结束时间，护盾消失的时间�?/summary>
        private float shieldEndTime;

        public override string GetActionName()
        {
            return "Shield Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[ShieldAction] Applying {shieldType} shield (Amount: {shieldAmount}, Duration: {shieldDuration}s)");

            ApplyShield();
            currentShieldAmount = shieldAmount;
            shieldEndTime = Time.time + shieldDuration;

            // 创建视觉效果
            CreateShieldEffect();

            // 播放音效
            if (shieldApplySound != null)
            {
                Debug.Log("[ShieldAction] Playing shield apply sound");
            }
        }

        public override void OnTick(int relativeFrame)
        {
            float currentTime = Time.time;

            // 检查护盾是否过�?
            if (shieldDuration > 0f && currentTime >= shieldEndTime)
            {
                Debug.Log("[ShieldAction] Shield expired due to timeout");
                RemoveShield();
                return;
            }

            // 检查护盾状�?
            if (relativeFrame % 30 == 0) // 每秒检查一�?
            {
                float remainingTime = shieldEndTime - currentTime;
                Debug.Log($"[ShieldAction] Shield status - Amount: {currentShieldAmount:F1}, Time: {remainingTime:F1}s");
            }

            // 监控破盾条件
            CheckBreakConditions();
        }

        public override void OnExit()
        {
            // 清理护盾效果（如果还存在�?
            if (shieldEffectInstance != null)
            {
                RemoveShield();
            }

            Debug.Log("[ShieldAction] Shield action completed");
        }

        /// <summary>应用护盾到目�?/summary>
        private void ApplyShield()
        {
            // 在实际项目中，这里会�?
            // 1. 获取目标单位
            // 2. 检查是否已有相同类型的护盾
            // 3. 根据刷新/叠加规则处理
            // 4. 注册伤害处理回调

            Debug.Log($"[ShieldAction] Shield properties:");
            Debug.Log($"  - Type: {shieldType}");
            Debug.Log($"  - Physical: {blockPhysicalDamage}, Magical: {blockMagicalDamage}, Pure: {blockPureDamage}");

            if (shieldType == ShieldType.Absorption)
            {
                Debug.Log($"  - Absorption Rate: {absorptionRate:P0}");
            }
            else if (shieldType == ShieldType.DamageReduction)
            {
                Debug.Log($"  - Damage Reduction: {damageReduction:P0}");
            }

            if (reflectDamage)
            {
                Debug.Log($"  - Reflects {reflectPercentage:P0} damage");
            }
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

                    // 将特效附加到目标
                    shieldEffectInstance.transform.SetParent(targetTransform, true);
                }
            }
        }

        /// <summary>移除护盾</summary>
        private void RemoveShield()
        {
            Debug.Log("[ShieldAction] Removing shield");

            // 移除视觉效果
            if (shieldEffectInstance != null)
            {
                UnityEngine.Object.Destroy(shieldEffectInstance);
                shieldEffectInstance = null;
            }

            // 在实际项目中，这里会注销伤害处理回调
        }

        /// <summary>护盾被破坏时的处�?/summary>
        private void OnShieldBroken()
        {
            Debug.Log("[ShieldAction] Shield broken!");

            // 播放破盾特效
            if (breakEffect != null)
            {
                var targetTransform = GetTargetTransform();
                if (targetTransform != null)
                {
                    UnityEngine.Object.Instantiate(breakEffect, targetTransform.position, Quaternion.identity);
                }
            }

            // 播放破盾音效
            if (shieldBreakSound != null)
            {
                Debug.Log("[ShieldAction] Playing shield break sound");
            }

            RemoveShield();
        }

        /// <summary>处理伤害吸收</summary>
        /// <param name="incomingDamage">incoming damage amount</param>
        /// <param name="damageType">damage type</param>
        /// <returns>实际受到的伤�?/returns>
        public float ProcessDamage(float incomingDamage, DamageType damageType)
        {
            // 检查护盾是否能阻挡这种伤害类型
            bool canBlock = false;
            switch (damageType)
            {
                case DamageType.Physical:
                    canBlock = blockPhysicalDamage;
                    break;
                case DamageType.Magical:
                    canBlock = blockMagicalDamage;
                    break;
                case DamageType.Pure:
                    canBlock = blockPureDamage;
                    break;
            }

            if (!canBlock)
            {
                return incomingDamage; // 护盾不能阻挡此类型伤�?
            }

            float actualDamage = incomingDamage;

            switch (shieldType)
            {
                case ShieldType.Absorption:
                    float absorbedDamage = Mathf.Min(incomingDamage * absorptionRate, currentShieldAmount);
                    currentShieldAmount -= absorbedDamage;
                    actualDamage = incomingDamage - absorbedDamage;
                    break;

                case ShieldType.DamageReduction:
                    actualDamage = incomingDamage * (1f - damageReduction);
                    break;

                case ShieldType.Block:
                    if (currentShieldAmount > 0)
                    {
                        actualDamage = 0f; // 完全阻挡
                        currentShieldAmount -= incomingDamage;
                    }
                    break;
            }

            // 反射伤害
            if (reflectDamage && actualDamage != incomingDamage)
            {
                float reflectedDamage = (incomingDamage - actualDamage) * reflectPercentage;
                Debug.Log($"[ShieldAction] Reflecting {reflectedDamage:F1} damage");

                if (reflectEffect != null)
                {
                    var targetTransform = GetTargetTransform();
                    if (targetTransform != null)
                    {
                        UnityEngine.Object.Instantiate(reflectEffect, targetTransform.position, Quaternion.identity);
                    }
                }
            }

            // 检查护盾是否被破坏
            if (currentShieldAmount <= 0f)
            {
                OnShieldBroken();
            }

            return actualDamage;
        }

        /// <summary>检查破盾条�?/summary>
        private void CheckBreakConditions()
        {
            // 在实际项目中，这里会检查各种破盾条�?
            // 目前仅为示例逻辑
            if (breakOnSpellCast || breakOnAttack || breakOnMovement)
            {
                // 模拟条件检�?
                if (UnityEngine.Random.value < 0.001f) // 很低的概率触发，仅作示例
                {
                    Debug.Log("[ShieldAction] Shield broken due to break condition");
                    OnShieldBroken();
                }
            }
        }

        /// <summary>获取目标Transform</summary>
        /// <returns>目标Transform引用</returns>
        private Transform GetTargetTransform()
        {
            return UnityEngine.Object.FindFirstObjectByType<Transform>();
        }
    }

    /// <summary>护盾类型枚举</summary>
    public enum ShieldType
    {
        Absorption,      // 吸收型护盾，直接吸收伤害
        DamageReduction, // 减伤型护盾，按比例减少伤�?
        Block           // 阻挡型护盾，完全阻挡一定次数的攻击
    }
}