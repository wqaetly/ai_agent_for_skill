using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 控制行为脚本
    /// 功能概述：对目标单位施加各种控制效果，包括眩晕、沉默、定身、减速、恐惧等�?
    /// 支持控制强度调节、持续时间管理、免疫检测、控制层级等功能�?
    /// 适用于DOTA2中的控制技能，如雷击、石化凝视、寒冬诅咒、恶魔赦免等控制类技能�?
    /// </summary>
    [Serializable]
    [ActionDisplayName("控制效果")]
    [ActionDescription("对目标施加控制效果，支持8种控制类型：眩晕(Stun)使目标无法行动、沉�?Silence)禁止施法、定�?Root)禁止移动、减�?Slow)降低移动速度、恐�?Fear)强制逃跑、魅�?Charm)控制敌人、缴�?Disable)禁用攻击和技能、放�?击飞(Banish)使目标无敌且无法行动。可配置持续时间、控制强度、免疫穿透、叠加行为等。常用于眩晕技能、击飞效果、沉默法术、减速debuff等各类控制技能�?)]
    public class ControlAction : ISkillAction
    {
        [BoxGroup("Control Settings")]
        [LabelText("Control Type")]
        /// <summary>控制类型，决定施加的控制效果种类</summary>
        public ControlType controlType = ControlType.Stun;

        [BoxGroup("Control Settings")]
        [LabelText("Control Duration")]
        [MinValue(0f)]
        /// <summary>控制持续时间，单位为秒，控制效果的作用时�?/summary>
        public float controlDuration = 2f;

        [BoxGroup("Control Settings")]
        [LabelText("Control Strength")]
        [Range(0f, 1f)]
        [ShowIf("@controlType == ControlType.Slow || controlType == ControlType.Silence")]
        /// <summary>控制强度，部分控制效果的强度系数（如减速的减速比例）</summary>
        public float controlStrength = 0.5f;

        [BoxGroup("Stun Settings")]
        [LabelText("Allow Actions During Stun")]
        [ShowIf("@controlType == ControlType.Stun")]
        /// <summary>眩晕期间允许行动，false时完全无法行动，true时允许部分行�?/summary>
        public bool allowActionsDuringStun = false;

        [BoxGroup("Fear Settings")]
        [LabelText("Fear Direction")]
        [ShowIf("@controlType == ControlType.Fear")]
        /// <summary>恐惧方向，恐惧效果中单位移动的方�?/summary>
        public FearDirection fearDirection = FearDirection.AwayFromCaster;

        [BoxGroup("Fear Settings")]
        [LabelText("Fear Movement Speed")]
        [Range(0f, 2f)]
        [ShowIf("@controlType == ControlType.Fear")]
        /// <summary>恐惧移动速度，恐惧状态下的移动速度倍数</summary>
        public float fearMovementSpeed = 1.5f;

        [BoxGroup("Charm Settings")]
        [LabelText("Charm Behavior")]
        [ShowIf("@controlType == ControlType.Charm")]
        /// <summary>魅惑行为，被魅惑时的行为模式</summary>
        public CharmBehavior charmBehavior = CharmBehavior.AttackAllies;

        [BoxGroup("Disable Settings")]
        [LabelText("Disabled Abilities")]
        [EnumToggleButtons]
        [ShowIf("@controlType == ControlType.Disable")]
        /// <summary>禁用能力类型，定义哪些能力被禁用</summary>
        public DisabledAbilities disabledAbilities = DisabledAbilities.Attacks | DisabledAbilities.Spells;

        [BoxGroup("Dispel Settings")]
        [LabelText("Dispel Resistance")]
        [Range(0f, 1f)]
        /// <summary>驱散抗性，抵抗被驱散的概率</summary>
        public float dispelResistance = 0f;

        [BoxGroup("Dispel Settings")]
        [LabelText("Dispel Priority")]
        /// <summary>驱散优先级，决定在驱散时的处理顺�?/summary>
        public DispelPriority dispelPriority = DispelPriority.Normal;

        [BoxGroup("Stack Settings")]
        [LabelText("Stackable")]
        /// <summary>可叠加，true时相同类型的控制效果可以叠加</summary>
        public bool stackable = false;

        [BoxGroup("Stack Settings")]
        [LabelText("Stack Behavior")]
        [ShowIf("stackable")]
        /// <summary>叠加行为，定义多个相同控制的叠加方式</summary>
        public StackBehavior stackBehavior = StackBehavior.RefreshDuration;

        [BoxGroup("Stack Settings")]
        [LabelText("Max Stacks")]
        [MinValue(1)]
        [ShowIf("@stackable && stackBehavior == StackBehavior.IncreaseStacks")]
        /// <summary>最大叠加层数，允许的最大叠加数�?/summary>
        public int maxStacks = 3;

        [BoxGroup("Immunity Settings")]
        [LabelText("Bypass Magic Immunity")]
        /// <summary>穿透魔法免疫，true时可以对魔法免疫单位生效</summary>
        public bool bypassMagicImmunity = false;

        [BoxGroup("Immunity Settings")]
        [LabelText("Bypass Control Immunity")]
        /// <summary>穿透控制免疫，true时可以对控制免疫单位生效</summary>
        public bool bypassControlImmunity = false;

        [BoxGroup("Visual Settings")]
        [LabelText("Control Effect")]
        /// <summary>控制特效，控制期间的持续视觉效果</summary>
        public GameObject controlEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Apply Effect")]
        /// <summary>施加特效，控制生效时的瞬间视觉效�?/summary>
        public GameObject applyEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("End Effect")]
        /// <summary>结束特效，控制结束时的视觉效�?/summary>
        public GameObject endEffect;

        [BoxGroup("Audio Settings")]
        [LabelText("Control Apply Sound")]
        /// <summary>控制施加音效，控制生效时的音�?/summary>
        public AudioClip controlApplySound;

        [BoxGroup("Audio Settings")]
        [LabelText("Control Loop Sound")]
        /// <summary>控制循环音效，控制持续期间的背景音频</summary>
        public AudioClip controlLoopSound;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定可以控制哪些类型的单位</summary>
        public TargetFilter targetFilter = TargetFilter.Enemy;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(1)]
        /// <summary>最大目标数量，同时可以控制的单位数�?/summary>
        public int maxTargets = 1;

        [BoxGroup("Target Settings")]
        [LabelText("Affect Buildings")]
        /// <summary>影响建筑，true时控制效果可以作用于建筑单位</summary>
        public bool affectBuildings = false;

        /// <summary>控制特效实例，持续特效的GameObject引用</summary>
        private GameObject controlEffectInstance;
        /// <summary>控制结束时间，控制效果消失的时间�?/summary>
        private float controlEndTime;
        /// <summary>控制是否处于激活状�?/summary>
        private bool isControlActive;

        public override string GetActionName()
        {
            return "Control Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[ControlAction] Applying {controlType} control for {controlDuration}s");

            if (ApplyControl())
            {
                controlEndTime = Time.time + controlDuration;
                isControlActive = true;

                CreateControlEffect();
                PlayApplyEffects();
            }
        }

        public override void OnTick(int relativeFrame)
        {
            if (!isControlActive) return;

            float currentTime = Time.time;

            // 检查控制是否结�?
            if (currentTime >= controlEndTime)
            {
                Debug.Log($"[ControlAction] {controlType} control expired");
                RemoveControl();
                return;
            }

            // 更新控制状�?
            UpdateControlEffect(relativeFrame);

            // 状态监�?
            if (relativeFrame % 30 == 0) // 每秒输出一�?
            {
                float remainingTime = controlEndTime - currentTime;
                Debug.Log($"[ControlAction] {controlType} active, remaining: {remainingTime:F1}s");
            }
        }

        public override void OnExit()
        {
            if (isControlActive)
            {
                RemoveControl();
            }
            Debug.Log($"[ControlAction] Control action completed");
        }

        /// <summary>应用控制效果到目�?/summary>
        /// <returns>是否成功应用控制</returns>
        private bool ApplyControl()
        {
            // 在实际项目中，这里会�?
            // 1. 获取目标单位
            // 2. 检查免疫状�?
            // 3. 检查抗�?
            // 4. 应用具体的控制效�?

            Debug.Log($"[ControlAction] Checking control application:");
            Debug.Log($"  - Type: {controlType}");
            Debug.Log($"  - Duration: {controlDuration}s");
            Debug.Log($"  - Bypass Magic Immunity: {bypassMagicImmunity}");
            Debug.Log($"  - Bypass Control Immunity: {bypassControlImmunity}");

            // 模拟免疫检�?
            if (!bypassMagicImmunity && CheckMagicImmunity())
            {
                Debug.Log("[ControlAction] Target is magic immune, control blocked");
                return false;
            }

            if (!bypassControlImmunity && CheckControlImmunity())
            {
                Debug.Log("[ControlAction] Target is control immune, control blocked");
                return false;
            }

            // 应用具体控制效果
            ApplySpecificControl();
            return true;
        }

        /// <summary>应用具体的控制效�?/summary>
        private void ApplySpecificControl()
        {
            switch (controlType)
            {
                case ControlType.Stun:
                    Debug.Log($"[ControlAction] Applying stun (Allow actions: {allowActionsDuringStun})");
                    break;

                case ControlType.Silence:
                    Debug.Log($"[ControlAction] Applying silence (Strength: {controlStrength:P0})");
                    break;

                case ControlType.Root:
                    Debug.Log("[ControlAction] Applying root - movement disabled");
                    break;

                case ControlType.Slow:
                    Debug.Log($"[ControlAction] Applying slow (Strength: {controlStrength:P0})");
                    break;

                case ControlType.Fear:
                    Debug.Log($"[ControlAction] Applying fear (Direction: {fearDirection}, Speed: {fearMovementSpeed:P0})");
                    break;

                case ControlType.Charm:
                    Debug.Log($"[ControlAction] Applying charm (Behavior: {charmBehavior})");
                    break;

                case ControlType.Disable:
                    Debug.Log($"[ControlAction] Applying disable (Abilities: {disabledAbilities})");
                    break;

                case ControlType.Banish:
                    Debug.Log("[ControlAction] Applying banish - target becomes untargetable");
                    break;
            }
        }

        /// <summary>更新控制效果</summary>
        /// <param name="relativeFrame">相对帧数</param>
        private void UpdateControlEffect(int relativeFrame)
        {
            switch (controlType)
            {
                case ControlType.Fear:
                    // 恐惧状态的移动逻辑
                    UpdateFearMovement();
                    break;

                case ControlType.Slow:
                    // 减速效果的持续应用
                    ApplySlowEffect();
                    break;

                // 其他控制类型的更新逻辑...
            }
        }

        /// <summary>更新恐惧移动</summary>
        private void UpdateFearMovement()
        {
            // 在实际项目中，这里会控制单位朝指定方向移�?
            Vector3 moveDirection = CalculateFearDirection();
            Debug.Log($"[ControlAction] Fear movement direction: {moveDirection}");
        }

        /// <summary>计算恐惧方向</summary>
        /// <returns>恐惧移动方向</returns>
        private Vector3 CalculateFearDirection()
        {
            switch (fearDirection)
            {
                case FearDirection.AwayFromCaster:
                    // 计算远离施法者的方向
                    var casterPos = Vector3.zero; // 获取施法者位�?
                    var targetPos = Vector3.zero; // 获取目标位置
                    return (targetPos - casterPos).normalized;

                case FearDirection.Random:
                    return UnityEngine.Random.onUnitSphere;

                case FearDirection.TowardsBase:
                    // 朝向基地方向
                    return Vector3.back; // 示例方向

                default:
                    return Vector3.zero;
            }
        }

        /// <summary>应用减速效�?/summary>
        private void ApplySlowEffect()
        {
            // 在实际项目中，这里会持续应用移动速度减少
            float slowedSpeed = 1f - controlStrength;
            Debug.Log($"[ControlAction] Applying slow - speed multiplier: {slowedSpeed:P0}");
        }

        /// <summary>创建控制视觉效果</summary>
        private void CreateControlEffect()
        {
            if (controlEffect != null)
            {
                var targetTransform = GetTargetTransform();
                if (targetTransform != null)
                {
                    controlEffectInstance = UnityEngine.Object.Instantiate(controlEffect, targetTransform.position, Quaternion.identity);
                    controlEffectInstance.transform.SetParent(targetTransform, true);
                }
            }
        }

        /// <summary>播放应用效果</summary>
        private void PlayApplyEffects()
        {
            var targetTransform = GetTargetTransform();
            if (targetTransform != null && applyEffect != null)
            {
                UnityEngine.Object.Instantiate(applyEffect, targetTransform.position, Quaternion.identity);
            }

            if (controlApplySound != null)
            {
                Debug.Log("[ControlAction] Playing control apply sound");
            }
        }

        /// <summary>移除控制效果</summary>
        private void RemoveControl()
        {
            if (!isControlActive) return;

            isControlActive = false;

            Debug.Log($"[ControlAction] Removing {controlType} control");

            // 移除视觉效果
            if (controlEffectInstance != null)
            {
                UnityEngine.Object.Destroy(controlEffectInstance);
                controlEffectInstance = null;
            }

            // 播放结束效果
            if (endEffect != null)
            {
                var targetTransform = GetTargetTransform();
                if (targetTransform != null)
                {
                    UnityEngine.Object.Instantiate(endEffect, targetTransform.position, Quaternion.identity);
                }
            }

            // 在实际项目中，这里会恢复目标的正常状�?
        }

        /// <summary>检查魔法免�?/summary>
        /// <returns>是否具有魔法免疫</returns>
        private bool CheckMagicImmunity()
        {
            // 模拟魔法免疫检�?
            return UnityEngine.Random.value < 0.1f; // 10%概率免疫
        }

        /// <summary>检查控制免�?/summary>
        /// <returns>是否具有控制免疫</returns>
        private bool CheckControlImmunity()
        {
            // 模拟控制免疫检�?
            return UnityEngine.Random.value < 0.05f; // 5%概率免疫
        }

        /// <summary>获取目标Transform</summary>
        /// <returns>目标Transform引用</returns>
        private Transform GetTargetTransform()
        {
            return UnityEngine.Object.FindFirstObjectByType<Transform>();
        }
    }

    /// <summary>控制类型枚举</summary>
    public enum ControlType
    {
        Stun,       // 眩晕
        Silence,    // 沉默
        Root,       // 定身
        Slow,       // 减�?
        Fear,       // 恐惧
        Charm,      // 魅惑
        Disable,    // 缴械
        Banish      // 放�?
    }

    /// <summary>恐惧方向枚举</summary>
    public enum FearDirection
    {
        AwayFromCaster, // 远离施法�?
        Random,         // 随机方向
        TowardsBase     // 朝向基地
    }

    /// <summary>魅惑行为枚举</summary>
    public enum CharmBehavior
    {
        AttackAllies,   // 攻击队友
        FollowCaster,   // 跟随施法�?
        Idle            // 无法行动
    }

    /// <summary>禁用能力类型枚举</summary>
    [System.Flags]
    public enum DisabledAbilities
    {
        None = 0,
        Attacks = 1 << 0,   // 攻击
        Spells = 1 << 1,    // 技�?
        Items = 1 << 2,     // 物品
        All = ~0            // 全部
    }

    /// <summary>驱散优先级枚�?/summary>
    public enum DispelPriority
    {
        Low,        // 低优先级
        Normal,     // 普通优先级
        High        // 高优先级
    }

    /// <summary>叠加行为枚举</summary>
    public enum StackBehavior
    {
        RefreshDuration,    // 刷新持续时间
        IncreaseStacks,     // 增加叠加层数
        IncreaseStrength    // 增加效果强度
    }
}