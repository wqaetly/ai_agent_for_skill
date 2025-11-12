using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 资源行为脚本
    /// 功能概述：管理和操作各种游戏资源，包括生命值、法力值、金币、经验值等。
    /// 支持资源消耗、恢复、转换、分享、偷取等多种操作模式。
    /// 适用于DOTA2中的资源相关技能，如法力燃烧、吸血光环、黄金法则、经验汲取等资源操作技能。
    /// </summary>
    [Serializable]
    [ActionDisplayName("资源操作")]
    public class ResourceAction : ISkillAction
    {
        [BoxGroup("Resource Settings")]
        [LabelText("Resource Type")]
        /// <summary>资源类型，指定要操作的资源种类</summary>
        public ResourceType resourceType = ResourceType.Health;

        [BoxGroup("Resource Settings")]
        [LabelText("Operation Type")]
        /// <summary>操作类型，定义对资源执行的操作方式</summary>
        public OperationType operationType = OperationType.Restore;

        [BoxGroup("Value Settings")]
        [LabelText("Base Amount")]
        [MinValue(0f)]
        /// <summary>基础数值，资源操作的原始数值</summary>
        public float baseAmount = 100f;

        [BoxGroup("Value Settings")]
        [LabelText("Amount Type")]
        /// <summary>数值类型，决定是固定数值还是百分比</summary>
        public AmountType amountType = AmountType.Fixed;

        [BoxGroup("Value Settings")]
        [LabelText("Percentage")]
        [Range(0f, 1f)]
        [ShowIf("@amountType == AmountType.Percentage")]
        /// <summary>百分比数值，当使用百分比模式时的比例值</summary>
        public float percentage = 0.5f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Scale with Level")]
        /// <summary>随等级缩放，true时效果会根据施法者等级调整</summary>
        public bool scaleWithLevel = false;

        [BoxGroup("Scaling Settings")]
        [LabelText("Level Scaling")]
        [MinValue(0f)]
        [ShowIf("scaleWithLevel")]
        /// <summary>等级缩放系数，每级增加的效果倍数</summary>
        public float levelScaling = 0.1f;

        [BoxGroup("Scaling Settings")]
        [LabelText("Scale with Attribute")]
        /// <summary>随属性缩放，true时效果会根据指定属性调整</summary>
        public bool scaleWithAttribute = false;

        [BoxGroup("Scaling Settings")]
        [LabelText("Scaling Attribute")]
        [ShowIf("scaleWithAttribute")]
        /// <summary>缩放属性类型，用于缩放计算的属性</summary>
        public AttributeType scalingAttribute = AttributeType.Damage;

        [BoxGroup("Scaling Settings")]
        [LabelText("Attribute Ratio")]
        [Range(0f, 5f)]
        [ShowIf("scaleWithAttribute")]
        /// <summary>属性缩放比例，属性对效果的影响比例</summary>
        public float attributeRatio = 1f;

        [BoxGroup("Transfer Settings")]
        [LabelText("Transfer Mode")]
        [ShowIf("@operationType == OperationType.Transfer || operationType == OperationType.Steal")]
        /// <summary>转移模式，定义资源转移的方式和规则</summary>
        public TransferMode transferMode = TransferMode.Direct;

        [BoxGroup("Transfer Settings")]
        [LabelText("Transfer Efficiency")]
        [Range(0f, 2f)]
        [ShowIf("@(operationType == OperationType.Transfer || operationType == OperationType.Steal) && transferMode != TransferMode.Burn")]
        /// <summary>转移效率，资源转移时的转换比例</summary>
        public float transferEfficiency = 1f;

        [BoxGroup("Limit Settings")]
        [LabelText("Respect Maximum")]
        /// <summary>遵守最大值限制，true时不会超过资源的最大值</summary>
        public bool respectMaximum = true;

        [BoxGroup("Limit Settings")]
        [LabelText("Allow Overdraft")]
        [ShowIf("@operationType == OperationType.Consume")]
        /// <summary>允许透支，true时可以消耗超过当前拥有量的资源</summary>
        public bool allowOverdraft = false;

        [BoxGroup("Limit Settings")]
        [LabelText("Overdraft Penalty")]
        [ShowIf("@allowOverdraft && operationType == OperationType.Consume")]
        /// <summary>透支惩罚类型，透支时的额外惩罚效果</summary>
        public OverdraftPenalty overdraftPenalty = OverdraftPenalty.Damage;

        [BoxGroup("Duration Settings")]
        [LabelText("Apply Over Time")]
        /// <summary>持续应用，true时资源操作会在持续时间内分次执行</summary>
        public bool applyOverTime = false;

        [BoxGroup("Duration Settings")]
        [LabelText("Application Interval")]
        [MinValue(0.1f)]
        [ShowIf("applyOverTime")]
        /// <summary>应用间隔，持续操作时每次应用的时间间隔</summary>
        public float applicationInterval = 1f;

        [BoxGroup("Visual Settings")]
        [LabelText("Resource Effect")]
        /// <summary>资源特效，资源操作时的视觉效果</summary>
        public GameObject resourceEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Continuous Effect")]
        [ShowIf("applyOverTime")]
        /// <summary>持续特效，持续操作期间的视觉效果</summary>
        public GameObject continuousEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Effect Color")]
        /// <summary>特效颜色，根据资源类型自定义特效颜色</summary>
        public Color effectColor = Color.white;

        [BoxGroup("Audio Settings")]
        [LabelText("Operation Sound")]
        /// <summary>操作音效，执行资源操作时的音频</summary>
        public AudioClip operationSound;

        [BoxGroup("Audio Settings")]
        [LabelText("Success Sound")]
        /// <summary>成功音效，操作成功时的音频反馈</summary>
        public AudioClip successSound;

        [BoxGroup("Audio Settings")]
        [LabelText("Failure Sound")]
        /// <summary>失败音效，操作失败时的音频反馈</summary>
        public AudioClip failureSound;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以操作哪些单位的资源</summary>
        public TargetFilter targetFilter = TargetFilter.Self;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(1)]
        /// <summary>最大目标数量，同时可以影响的单位数量</summary>
        public int maxTargets = 1;

        [BoxGroup("Target Settings")]
        [LabelText("Require Line of Sight")]
        /// <summary>需要视线，true时只能对可见目标执行操作</summary>
        public bool requireLineOfSight = false;

        /// <summary>下次应用时间，控制持续操作的时间间隔</summary>
        private float nextApplicationTime;
        /// <summary>持续特效实例，生成的持续特效GameObject引用</summary>
        private GameObject continuousEffectInstance;
        /// <summary>总应用次数，记录持续操作已执行的次数</summary>
        private int totalApplications;

        public override string GetActionName()
        {
            return "Resource Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[ResourceAction] {operationType} {resourceType} - Base: {baseAmount}");

            if (applyOverTime)
            {
                nextApplicationTime = 0f;
                totalApplications = 0;

                // 创建持续特效
                if (continuousEffect != null)
                {
                    var targetTransform = GetTargetTransform();
                    if (targetTransform != null)
                    {
                        continuousEffectInstance = UnityEngine.Object.Instantiate(continuousEffect, targetTransform.position, Quaternion.identity);
                    }
                }
            }
            else
            {
                // 立即执行操作
                ExecuteResourceOperation();
            }
        }

        public override void OnTick(int relativeFrame)
        {
            if (applyOverTime)
            {
                float currentTime = relativeFrame * Time.fixedDeltaTime;

                if (currentTime >= nextApplicationTime)
                {
                    ExecuteResourceOperation();
                    nextApplicationTime = currentTime + applicationInterval;
                    totalApplications++;
                }
            }
        }

        public override void OnExit()
        {
            // 清理持续特效
            if (continuousEffectInstance != null)
            {
                UnityEngine.Object.Destroy(continuousEffectInstance);
                continuousEffectInstance = null;
            }

            if (applyOverTime)
            {
                Debug.Log($"[ResourceAction] Completed {totalApplications} resource applications");
            }
            else
            {
                Debug.Log($"[ResourceAction] Resource action completed");
            }
        }

        /// <summary>执行资源操作</summary>
        private void ExecuteResourceOperation()
        {
            float finalAmount = CalculateFinalAmount();
            bool operationSuccess = false;

            Debug.Log($"[ResourceAction] Executing {operationType} on {resourceType}: {finalAmount:F1}");

            switch (operationType)
            {
                case OperationType.Restore:
                    operationSuccess = RestoreResource(finalAmount);
                    break;

                case OperationType.Consume:
                    operationSuccess = ConsumeResource(finalAmount);
                    break;

                case OperationType.Transfer:
                    operationSuccess = TransferResource(finalAmount);
                    break;

                case OperationType.Steal:
                    operationSuccess = StealResource(finalAmount);
                    break;

                case OperationType.Share:
                    operationSuccess = ShareResource(finalAmount);
                    break;

                case OperationType.Convert:
                    operationSuccess = ConvertResource(finalAmount);
                    break;
            }

            // 播放效果和音效
            PlayResourceEffects(operationSuccess);
        }

        /// <summary>计算最终作用数值</summary>
        /// <returns>经过各种加成后的最终数值</returns>
        private float CalculateFinalAmount()
        {
            float amount = baseAmount;

            // 百分比计算
            if (amountType == AmountType.Percentage)
            {
                float targetMaxResource = GetTargetMaxResource();
                amount = targetMaxResource * percentage;
            }

            // 等级缩放
            if (scaleWithLevel)
            {
                int casterLevel = GetCasterLevel();
                amount += baseAmount * levelScaling * casterLevel;
            }

            // 属性缩放
            if (scaleWithAttribute)
            {
                float attributeValue = GetCasterAttribute(scalingAttribute);
                amount += attributeValue * attributeRatio;
            }

            return amount;
        }

        /// <summary>恢复资源</summary>
        /// <param name="amount">恢复数量</param>
        /// <returns>操作是否成功</returns>
        private bool RestoreResource(float amount)
        {
            // 在实际项目中，这里会获取目标单位并恢复对应资源
            float currentResource = GetCurrentResource();
            float maxResource = GetTargetMaxResource();

            float actualRestore = amount;
            if (respectMaximum)
            {
                actualRestore = Mathf.Min(amount, maxResource - currentResource);
            }

            if (actualRestore > 0f)
            {
                Debug.Log($"[ResourceAction] Restored {actualRestore:F1} {resourceType} (was {currentResource:F1})");
                return true;
            }

            return false;
        }

        /// <summary>消耗资源</summary>
        /// <param name="amount">消耗数量</param>
        /// <returns>操作是否成功</returns>
        private bool ConsumeResource(float amount)
        {
            float currentResource = GetCurrentResource();

            if (currentResource >= amount)
            {
                Debug.Log($"[ResourceAction] Consumed {amount:F1} {resourceType} (remaining: {currentResource - amount:F1})");
                return true;
            }
            else if (allowOverdraft)
            {
                float overdraftAmount = amount - currentResource;
                Debug.Log($"[ResourceAction] Overdrafted {overdraftAmount:F1} {resourceType}");
                ApplyOverdraftPenalty(overdraftAmount);
                return true;
            }

            Debug.LogWarning($"[ResourceAction] Insufficient {resourceType} (need {amount:F1}, have {currentResource:F1})");
            return false;
        }

        /// <summary>转移资源</summary>
        /// <param name="amount">转移数量</param>
        /// <returns>操作是否成功</returns>
        private bool TransferResource(float amount)
        {
            switch (transferMode)
            {
                case TransferMode.Direct:
                    Debug.Log($"[ResourceAction] Direct transfer: {amount:F1} {resourceType}");
                    break;

                case TransferMode.Efficient:
                    float transferredAmount = amount * transferEfficiency;
                    Debug.Log($"[ResourceAction] Efficient transfer: {amount:F1} -> {transferredAmount:F1} {resourceType}");
                    break;

                case TransferMode.Burn:
                    Debug.Log($"[ResourceAction] Burning {amount:F1} {resourceType} (no transfer)");
                    break;
            }

            return true;
        }

        /// <summary>偷取资源</summary>
        /// <param name="amount">偷取数量</param>
        /// <returns>操作是否成功</returns>
        private bool StealResource(float amount)
        {
            float targetResource = GetCurrentResource();
            float actualSteal = Mathf.Min(amount, targetResource);
            float gainedAmount = actualSteal * transferEfficiency;

            Debug.Log($"[ResourceAction] Stole {actualSteal:F1} {resourceType}, gained {gainedAmount:F1}");
            return actualSteal > 0f;
        }

        /// <summary>分享资源</summary>
        /// <param name="amount">分享数量</param>
        /// <returns>操作是否成功</returns>
        private bool ShareResource(float amount)
        {
            Debug.Log($"[ResourceAction] Sharing {amount:F1} {resourceType} among {maxTargets} targets");
            float perTargetAmount = amount / maxTargets;
            Debug.Log($"[ResourceAction] Each target receives {perTargetAmount:F1} {resourceType}");
            return true;
        }

        /// <summary>转换资源</summary>
        /// <param name="amount">转换数量</param>
        /// <returns>操作是否成功</returns>
        private bool ConvertResource(float amount)
        {
            // 例如：生命值转换为法力值，或金币转换为经验值
            Debug.Log($"[ResourceAction] Converting {amount:F1} {resourceType} to other resource type");
            float convertedAmount = amount * transferEfficiency;
            Debug.Log($"[ResourceAction] Conversion result: {convertedAmount:F1}");
            return true;
        }

        /// <summary>应用透支惩罚</summary>
        /// <param name="overdraftAmount">透支数量</param>
        private void ApplyOverdraftPenalty(float overdraftAmount)
        {
            switch (overdraftPenalty)
            {
                case OverdraftPenalty.Damage:
                    Debug.Log($"[ResourceAction] Overdraft damage: {overdraftAmount:F1}");
                    break;

                case OverdraftPenalty.Stun:
                    Debug.Log($"[ResourceAction] Overdraft stun applied");
                    break;

                case OverdraftPenalty.Debuff:
                    Debug.Log($"[ResourceAction] Overdraft debuff applied");
                    break;
            }
        }

        /// <summary>播放资源效果</summary>
        /// <param name="success">操作是否成功</param>
        private void PlayResourceEffects(bool success)
        {
            // 播放视觉效果
            if (resourceEffect != null)
            {
                var targetTransform = GetTargetTransform();
                if (targetTransform != null)
                {
                    var effect = UnityEngine.Object.Instantiate(resourceEffect, targetTransform.position, Quaternion.identity);

                    // 应用颜色
                    var particleSystem = effect.GetComponent<ParticleSystem>();
                    if (particleSystem != null)
                    {
                        var main = particleSystem.main;
                        main.startColor = effectColor;
                    }
                }
            }

            // 播放音效
            AudioClip soundToPlay = null;
            if (success && successSound != null)
                soundToPlay = successSound;
            else if (!success && failureSound != null)
                soundToPlay = failureSound;
            else if (operationSound != null)
                soundToPlay = operationSound;

            if (soundToPlay != null)
            {
                Debug.Log($"[ResourceAction] Playing {(success ? "success" : "failure")} sound");
            }
        }

        /// <summary>获取目标Transform</summary>
        /// <returns>目标Transform引用</returns>
        private Transform GetTargetTransform()
        {
            return UnityEngine.Object.FindFirstObjectByType<Transform>();
        }

        /// <summary>获取当前资源数量（模拟）</summary>
        /// <returns>当前资源数量</returns>
        private float GetCurrentResource()
        {
            // 模拟数据
            switch (resourceType)
            {
                case ResourceType.Health: return 750f;
                case ResourceType.Mana: return 400f;
                case ResourceType.Rage: return 85f;
                case ResourceType.Gold: return 1250f;
                case ResourceType.Experience: return 2800f;
                default: return 100f;
            }
        }

        /// <summary>获取最大资源数量（模拟）</summary>
        /// <returns>最大资源数量</returns>
        private float GetTargetMaxResource()
        {
            // 模拟数据
            switch (resourceType)
            {
                case ResourceType.Health: return 1000f;
                case ResourceType.Mana: return 500f;
                case ResourceType.Rage: return 100f;
                case ResourceType.Gold: return 999999f;
                case ResourceType.Experience: return 999999f;
                default: return 100f;
            }
        }

        /// <summary>获取施法者等级（模拟）</summary>
        /// <returns>施法者等级</returns>
        private int GetCasterLevel()
        {
            return 15; // 模拟等级
        }

        /// <summary>获取施法者属性（模拟）</summary>
        /// <param name="attribute">属性类型</param>
        /// <returns>属性数值</returns>
        private float GetCasterAttribute(AttributeType attribute)
        {
            // 模拟属性数据
            switch (attribute)
            {
                case AttributeType.Damage: return 120f;
                case AttributeType.Health: return 1000f;
                case AttributeType.Mana: return 500f;
                default: return 100f;
            }
        }
    }

    /// <summary>资源类型枚举</summary>
    public enum ResourceType
    {
        Health,     // 生命值
        Mana,       // 法力值
        Rage,       // 怒气值
        Gold,       // 金币
        Experience  // 经验值
    }

    /// <summary>操作类型枚举</summary>
    public enum OperationType
    {
        Restore,    // 恢复
        Consume,    // 消耗
        Transfer,   // 转移
        Steal,      // 偷取
        Share,      // 分享
        Convert     // 转换
    }

    /// <summary>数值类型枚举</summary>
    public enum AmountType
    {
        Fixed,      // 固定数值
        Percentage  // 百分比
    }

    /// <summary>转移模式枚举</summary>
    public enum TransferMode
    {
        Direct,     // 直接转移
        Efficient,  // 高效转移（有转换比例）
        Burn        // 燃烧（只消耗不转移）
    }

    /// <summary>透支惩罚枚举</summary>
    public enum OverdraftPenalty
    {
        None,       // 无惩罚
        Damage,     // 造成伤害
        Stun,       // 眩晕
        Debuff      // 减益效果
    }
}