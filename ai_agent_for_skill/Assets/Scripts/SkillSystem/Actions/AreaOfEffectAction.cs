using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 范围效果行为脚本
    /// 功能概述：在指定区域内产生各种效果，包括伤害、治疗、Buff施加等�?
    /// 支持多种形状的作用区域（圆形、矩形、扇形、环形），以及渐变效果和持续作用�?
    /// 适用于DOTA2中的AOE技能，如地震、暴雪、火墙、光环效果等区域性技能�?
    /// </summary>
    [Serializable]
    [ActionDisplayName("区域效果")]
    public class AreaOfEffectAction : ISkillAction
    {
        [BoxGroup("Area Settings")]
        [LabelText("Area Shape")]
        /// <summary>作用区域形状，决定AOE效果的几何形�?/summary>
        public AreaShape areaShape = AreaShape.Circle;

        [BoxGroup("Area Settings")]
        [LabelText("Area Size")]
        [MinValue(0f)]
        /// <summary>区域大小，对于圆形是半径，对于矩形是边长，对于扇形是半径</summary>
        public float areaSize = 5f;

        [BoxGroup("Area Settings")]
        [LabelText("Inner Radius")]
        [MinValue(0f)]
        [ShowIf("@areaShape == AreaShape.Ring")]
        /// <summary>内圈半径，仅环形区域使用，定义环形的内部空洞大小</summary>
        public float innerRadius = 2f;

        [BoxGroup("Area Settings")]
        [LabelText("Area Angle")]
        [Range(0f, 360f)]
        [ShowIf("@areaShape == AreaShape.Sector")]
        /// <summary>扇形角度，仅扇形区域使用，定义扇形的开口角�?/summary>
        public float areaAngle = 90f;

        [BoxGroup("Position Settings")]
        [LabelText("Center Position")]
        /// <summary>中心位置，AOE效果的中心点坐标</summary>
        public Vector3 centerPosition = Vector3.zero;

        [BoxGroup("Position Settings")]
        [LabelText("Use Relative Position")]
        /// <summary>使用相对位置，true时中心位置相对于施法者，false时为世界坐标</summary>
        public bool useRelativePosition = true;

        [BoxGroup("Position Settings")]
        [LabelText("Follow Caster")]
        /// <summary>跟随施法者，true时AOE区域会跟随施法者移�?/summary>
        public bool followCaster = false;

        [BoxGroup("Effect Settings")]
        [LabelText("Effect Type")]
        /// <summary>效果类型，定义AOE区域内产生的效果种类</summary>
        public AOEEffectType effectType = AOEEffectType.Damage;

        [BoxGroup("Effect Settings")]
        [LabelText("Effect Value")]
        [MinValue(0f)]
        /// <summary>效果数值，根据效果类型可能是伤害值、治疗量�?/summary>
        public float effectValue = 100f;

        [BoxGroup("Effect Settings")]
        [LabelText("Effect Interval")]
        [MinValue(0f)]
        [InfoBox("效果触发间隔�?表示只触发一�?)]
        /// <summary>效果间隔时间，单位为秒，决定AOE效果的触发频�?/summary>
        public float effectInterval = 1f;

        /// <summary>跳动频率别名，用于Visualizer兼容</summary>
        public float tickRate => effectInterval > 0f ? 1f / effectInterval : 0f;

        /// <summary>每次跳动伤害，用于Visualizer兼容</summary>
        public float damagePerTick => effectValue;

        /// <summary>范围半径别名，用于Visualizer兼容</summary>
        public float radius => areaSize;

        [BoxGroup("Falloff Settings")]
        [LabelText("Use Distance Falloff")]
        /// <summary>使用距离衰减，true时效果强度会随距离中心的距离而衰�?/summary>
        public bool useDistanceFalloff = false;

        [BoxGroup("Falloff Settings")]
        [LabelText("Falloff Curve")]
        [ShowIf("useDistanceFalloff")]
        /// <summary>衰减曲线，定义效果强度随距离变化的曲�?/summary>
        public AnimationCurve falloffCurve = AnimationCurve.Linear(0f, 1f, 1f, 0f);

        [BoxGroup("Visual Settings")]
        [LabelText("Area Visual Effect")]
        /// <summary>区域视觉效果，显示AOE范围的粒子特效或地面标记</summary>
        public GameObject areaVisualEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Ongoing Effect")]
        /// <summary>持续视觉效果，在AOE持续期间播放的特�?/summary>
        public GameObject ongoingEffect;

        [BoxGroup("Target Settings")]
        [LabelText("Target Filter")]
        /// <summary>目标筛选器，决定AOE效果影响哪些类型的单�?/summary>
        public TargetFilter targetFilter = TargetFilter.Enemy;

        [BoxGroup("Target Settings")]
        [LabelText("Max Targets")]
        [MinValue(0)]
        [InfoBox("最大影响目标数�?表示无限�?)]
        /// <summary>最大目标数量，限制AOE效果同时影响的单位数�?/summary>
        public int maxTargets = 0;

        [BoxGroup("Target Settings")]
        [LabelText("Ignore Caster")]
        /// <summary>忽略施法者，true时AOE效果不会影响施法者自�?/summary>
        public bool ignoreCaster = true;

        /// <summary>影响施法者别名，用于Visualizer兼容</summary>
        public bool affectsCaster => !ignoreCaster;

        /// <summary>实际中心位置，经过计算后的世界坐标中心点</summary>
        private Vector3 actualCenterPosition;
        /// <summary>区域视觉效果实例，生成的视觉效果GameObject引用</summary>
        private GameObject areaEffectInstance;
        /// <summary>持续效果实例，生成的持续特效GameObject引用</summary>
        private GameObject ongoingEffectInstance;
        /// <summary>下次效果触发时间，用于控制效果间�?/summary>
        private float nextEffectTime;

        public override string GetActionName()
        {
            return "Area of Effect Action";
        }

        public override void OnEnter()
        {
            // 计算实际中心位置
            var casterTransform = UnityEngine.Object.FindFirstObjectByType<Transform>();
            if (useRelativePosition && casterTransform != null)
            {
                actualCenterPosition = casterTransform.position + centerPosition;
            }
            else
            {
                actualCenterPosition = centerPosition;
            }

            Debug.Log($"[AOEAction] Creating {areaShape} AOE at {actualCenterPosition} with size {areaSize}");

            CreateVisualEffects();
            nextEffectTime = 0f; // 立即触发第一次效�?
        }

        public override void OnTick(int relativeFrame)
        {
            float currentTime = relativeFrame * Time.fixedDeltaTime;

            // 跟随施法�?
            if (followCaster)
            {
                var casterTransform = UnityEngine.Object.FindFirstObjectByType<Transform>();
                if (casterTransform != null)
                {
                    actualCenterPosition = casterTransform.position + centerPosition;
                    UpdateEffectPositions();
                }
            }

            // 检查是否需要触发效�?
            if (currentTime >= nextEffectTime)
            {
                ApplyAreaEffect();

                if (effectInterval > 0f)
                {
                    nextEffectTime = currentTime + effectInterval;
                }
                else
                {
                    nextEffectTime = float.MaxValue; // 只触发一�?
                }
            }
        }

        public override void OnExit()
        {
            CleanupVisualEffects();
            Debug.Log($"[AOEAction] AOE effect ended");
        }

        /// <summary>创建视觉效果</summary>
        private void CreateVisualEffects()
        {
            // 创建区域标记效果
            if (areaVisualEffect != null)
            {
                areaEffectInstance = UnityEngine.Object.Instantiate(areaVisualEffect, actualCenterPosition, Quaternion.identity);
                // 根据区域大小调整特效缩放
                areaEffectInstance.transform.localScale = Vector3.one * areaSize;
            }

            // 创建持续效果
            if (ongoingEffect != null)
            {
                ongoingEffectInstance = UnityEngine.Object.Instantiate(ongoingEffect, actualCenterPosition, Quaternion.identity);
            }
        }

        /// <summary>更新效果位置（用于跟随移动）</summary>
        private void UpdateEffectPositions()
        {
            if (areaEffectInstance != null)
            {
                areaEffectInstance.transform.position = actualCenterPosition;
            }

            if (ongoingEffectInstance != null)
            {
                ongoingEffectInstance.transform.position = actualCenterPosition;
            }
        }

        /// <summary>清理视觉效果</summary>
        private void CleanupVisualEffects()
        {
            if (areaEffectInstance != null)
            {
                UnityEngine.Object.Destroy(areaEffectInstance);
                areaEffectInstance = null;
            }

            if (ongoingEffectInstance != null)
            {
                UnityEngine.Object.Destroy(ongoingEffectInstance);
                ongoingEffectInstance = null;
            }
        }

        /// <summary>应用区域效果</summary>
        private void ApplyAreaEffect()
        {
            Debug.Log($"[AOEAction] Applying {effectType} effect (Value: {effectValue}) in {areaShape} area");

            // 在实际项目中，这里会�?
            // 1. 获取区域内的所有目�?
            // 2. 根据目标筛选器过滤目标
            // 3. 应用距离衰减（如果启用）
            // 4. 对每个有效目标应用效�?

            // 模拟获取区域内目标的过程
            var targets = GetTargetsInArea();
            Debug.Log($"[AOEAction] Found {targets.Length} potential targets in area");

            foreach (var target in targets)
            {
                float distance = Vector3.Distance(target.position, actualCenterPosition);
                float effectMultiplier = 1f;

                // 计算距离衰减
                if (useDistanceFalloff)
                {
                    float normalizedDistance = distance / areaSize;
                    effectMultiplier = falloffCurve.Evaluate(normalizedDistance);
                }

                float finalEffectValue = effectValue * effectMultiplier;

                Debug.Log($"[AOEAction] Applying {finalEffectValue} {effectType} to target at distance {distance:F1}");
            }
        }

        /// <summary>获取区域内的目标（模拟实现）</summary>
        /// <returns>区域内的目标数组</returns>
        private Transform[] GetTargetsInArea()
        {
            // 在实际项目中，这里会根据区域形状进行精确的碰撞检�?
            // 目前返回模拟数据
            return new Transform[0];
        }

        /// <summary>检查点是否在指定形状的区域�?/summary>
        /// <param name="point">要检查的�?/param>
        /// <returns>是否在区域内</returns>
        private bool IsPointInArea(Vector3 point)
        {
            Vector3 offset = point - actualCenterPosition;
            float distance = offset.magnitude;

            switch (areaShape)
            {
                case AreaShape.Circle:
                    return distance <= areaSize;

                case AreaShape.Rectangle:
                    return Mathf.Abs(offset.x) <= areaSize && Mathf.Abs(offset.z) <= areaSize;

                case AreaShape.Sector:
                    if (distance > areaSize) return false;
                    float angle = Vector3.Angle(Vector3.forward, offset);
                    return angle <= areaAngle / 2f;

                case AreaShape.Ring:
                    return distance >= innerRadius && distance <= areaSize;

                default:
                    return false;
            }
        }
    }

    /// <summary>区域形状枚举</summary>
    public enum AreaShape
    {
        Circle,     // 圆形
        Rectangle,  // 矩形
        Sector,     // 扇形
        Ring        // 环形
    }

    /// <summary>AOE效果类型枚举</summary>
    public enum AOEEffectType
    {
        Damage,     // 伤害
        Healing,    // 治疗
        Buff,       // 增益效果
        Debuff      // 减益效果
    }
}