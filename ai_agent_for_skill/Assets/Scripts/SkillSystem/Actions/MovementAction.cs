using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 移动行为脚本
    /// 功能概述：控制角色的位置移动，支持多种移动模式，包括线性移动、弧线移动、
    /// 自定义曲线移动和瞬间传送。可以配置移动速度、目标位置、朝向等参数。
    /// 适用于DOTA2中的位移技能，如闪烁、跳跃攻击、冲刺等技能。
    /// </summary>
    [Serializable]
    [ActionDisplayName("位移")]
    [ActionDescription("控制角色位移。支持4种移动类型：线性移动(Linear)直线前进、弧线移动(Arc)跳跃式移动、曲线移动(Curve)自定义轨迹、瞬移(Instant)瞬间传送。可配置移动速度、目标位置、相对/绝对坐标、面向方向等。常用于冲刺技能、闪现、跳跃攻击、位移突进等需要改变角色位置的技能。纯粹位移，不包含伤害和控制效果。")]
    public class MovementAction : ISkillAction
    {
        [BoxGroup("Movement Settings")]
        [LabelText("Movement Type")]
        /// <summary>移动类型，决定角色移动的轨迹模式（线性/弧线/曲线/瞬移）</summary>
        public MovementType movementType = MovementType.Linear;

        [BoxGroup("Movement Settings")]
        [LabelText("Movement Speed")]
        [MinValue(0f)]
        [ShowIf("@movementType != MovementType.Instant")]
        /// <summary>移动速度，单位每秒移动的距离，仅对非瞬移类型有效</summary>
        public float movementSpeed = 500f;

        [BoxGroup("Target Settings")]
        [LabelText("Target Position")]
        /// <summary>目标位置坐标，角色将移动到的最终位置</summary>
        public Vector3 targetPosition = Vector3.zero;

        [BoxGroup("Target Settings")]
        [LabelText("Use Relative Position")]
        [InfoBox("如果为true，目标位置相对于当前位置")]
        /// <summary>使用相对位置，true时目标位置相对于起始位置，false时为世界绝对位置</summary>
        public bool useRelativePosition = true;

        [BoxGroup("Arc Movement")]
        [LabelText("Arc Height")]
        [MinValue(0f)]
        [ShowIf("@movementType == MovementType.Arc")]
        /// <summary>弧线高度，弧线移动时轨迹的最高点相对于起始高度的偏移</summary>
        public float arcHeight = 2f;

        [BoxGroup("Curve Movement")]
        [LabelText("Movement Curve")]
        [ShowIf("@movementType == MovementType.Curve")]
        /// <summary>移动曲线，自定义移动速度随时间的变化曲线，用于创建复杂的移动效果</summary>
        public AnimationCurve movementCurve = AnimationCurve.EaseInOut(0f, 0f, 1f, 1f);

        [BoxGroup("Advanced Settings")]
        [LabelText("Face Movement Direction")]
        /// <summary>朝向移动方向，true时角色会自动转向移动的方向</summary>
        public bool faceMovementDirection = true;

        [BoxGroup("Advanced Settings")]
        [LabelText("Allow Movement Cancel")]
        [InfoBox("允许被其他行为打断移动")]
        /// <summary>允许移动取消，true时移动可以被其他技能或行为打断</summary>
        public bool allowMovementCancel = false;

        [BoxGroup("Advanced Settings")]
        [LabelText("Ignore Collision")]
        /// <summary>忽略碰撞，true时移动过程中不进行碰撞检测，可穿越障碍物</summary>
        public bool ignoreCollision = false;

        /// <summary>起始位置，记录移动开始时的世界坐标</summary>
        private Vector3 startPosition;
        /// <summary>实际目标位置，经过相对位置计算后的最终目标世界坐标</summary>
        private Vector3 actualTargetPosition;
        /// <summary>总移动距离，起始位置到目标位置的直线距离</summary>
        private float totalDistance;

        public override string GetActionName()
        {
            return "Movement Action";
        }

        public override void OnEnter()
        {
            var transform = UnityEngine.Object.FindFirstObjectByType<Transform>();
            if (transform != null)
            {
                startPosition = transform.position;

                // 计算实际目标位置
                if (useRelativePosition)
                {
                    actualTargetPosition = startPosition + targetPosition;
                }
                else
                {
                    actualTargetPosition = targetPosition;
                }

                totalDistance = Vector3.Distance(startPosition, actualTargetPosition);

                Debug.Log($"[MovementAction] Started {movementType} movement from {startPosition} to {actualTargetPosition}");

                // 瞬间传送
                if (movementType == MovementType.Instant)
                {
                    transform.position = actualTargetPosition;
                    if (faceMovementDirection)
                    {
                        Vector3 direction = (actualTargetPosition - startPosition).normalized;
                        if (direction != Vector3.zero)
                        {
                            transform.rotation = Quaternion.LookRotation(direction);
                        }
                    }
                }
            }
        }

        public override void OnTick(int relativeFrame)
        {
            if (movementType == MovementType.Instant) return;

            var transform = UnityEngine.Object.FindFirstObjectByType<Transform>();
            if (transform != null)
            {
                float progress = (float)relativeFrame / duration;
                progress = Mathf.Clamp01(progress);

                Vector3 currentPosition = CalculatePosition(progress);
                transform.position = currentPosition;

                // 朝向移动方向
                if (faceMovementDirection && relativeFrame > 0)
                {
                    Vector3 direction = (actualTargetPosition - startPosition).normalized;
                    if (direction != Vector3.zero)
                    {
                        transform.rotation = Quaternion.LookRotation(direction);
                    }
                }

                if (relativeFrame % 10 == 0)
                {
                    Debug.Log($"[MovementAction] Movement progress: {progress:P0}, Position: {currentPosition}");
                }
            }
        }

        public override void OnExit()
        {
            Debug.Log($"[MovementAction] Movement completed");
        }

        /// <summary>根据进度计算当前位置坐标</summary>
        /// <param name="progress">移动进度，0-1之间的值</param>
        /// <returns>计算出的当前位置坐标</returns>
        private Vector3 CalculatePosition(float progress)
        {
            switch (movementType)
            {
                case MovementType.Linear:
                    return Vector3.Lerp(startPosition, actualTargetPosition, progress);

                case MovementType.Arc:
                    Vector3 linearPos = Vector3.Lerp(startPosition, actualTargetPosition, progress);
                    float arcOffset = arcHeight * Mathf.Sin(progress * Mathf.PI);
                    return linearPos + Vector3.up * arcOffset;

                case MovementType.Curve:
                    float curveValue = movementCurve.Evaluate(progress);
                    return Vector3.Lerp(startPosition, actualTargetPosition, curveValue);

                default:
                    return startPosition;
            }
        }
    }

    /// <summary>移动类型枚举</summary>
    public enum MovementType
    {
        Linear,     // 线性移动
        Arc,        // 弧线移动（抛物线）
        Curve,      // 自定义曲线移动
        Instant     // 瞬间传送
    }
}