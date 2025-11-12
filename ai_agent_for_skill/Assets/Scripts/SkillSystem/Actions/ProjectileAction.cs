using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 投射物行为脚本
    /// 功能概述：创建和控制各种投射物，包括直线弹道、追踪弹道、抛物线弹道等。
    /// 支持投射物的生命周期管理、碰撞检测、命中效果触发等功能。
    /// 适用于DOTA2中的远程攻击和技能，如普通攻击弹道、魔法球、导弹等投射物技能。
    /// </summary>
    [Serializable]
    [ActionDisplayName("投射物")]
    public class ProjectileAction : ISkillAction
    {
        [BoxGroup("Projectile Settings")]
        [LabelText("Projectile Type")]
        /// <summary>投射物类型，决定投射物的飞行轨迹和行为模式</summary>
        public ProjectileType projectileType = ProjectileType.Linear;

        [BoxGroup("Projectile Settings")]
        [LabelText("Projectile Speed")]
        [MinValue(0f)]
        /// <summary>投射物飞行速度，单位每秒移动的距离</summary>
        public float projectileSpeed = 1000f;

        [BoxGroup("Projectile Settings")]
        [LabelText("Max Range")]
        [MinValue(0f)]
        /// <summary>投射物最大飞行距离，超过此距离后投射物将消失</summary>
        public float maxRange = 1000f;

        [BoxGroup("Visual Settings")]
        [LabelText("Projectile Prefab")]
        /// <summary>投射物预制体，投射物的视觉表现和物理碰撞体</summary>
        public GameObject projectilePrefab;

        [BoxGroup("Visual Settings")]
        [LabelText("Projectile Size")]
        [MinValue(0.1f)]
        /// <summary>投射物尺寸缩放，影响投射物的显示大小和碰撞范围</summary>
        public float projectileSize = 1f;

        [BoxGroup("Visual Settings")]
        [LabelText("Trail Effect")]
        /// <summary>拖尾特效，投射物飞行时的轨迹效果</summary>
        public GameObject trailEffect;

        [BoxGroup("Ballistic Settings")]
        [LabelText("Arc Height")]
        [MinValue(0f)]
        [ShowIf("@projectileType == ProjectileType.Arc")]
        /// <summary>弧线高度，抛物线投射物的最高点相对高度</summary>
        public float arcHeight = 5f;

        [BoxGroup("Tracking Settings")]
        [LabelText("Tracking Strength")]
        [Range(0f, 1f)]
        [ShowIf("@projectileType == ProjectileType.Homing")]
        /// <summary>追踪强度，决定追踪投射物的转向能力，1为完全追踪</summary>
        public float trackingStrength = 0.8f;

        [BoxGroup("Tracking Settings")]
        [LabelText("Max Turn Rate")]
        [MinValue(0f)]
        [ShowIf("@projectileType == ProjectileType.Homing")]
        /// <summary>最大转向速率，追踪投射物每秒最大转向角度</summary>
        public float maxTurnRate = 180f;

        [BoxGroup("Pierce Settings")]
        [LabelText("Pierce Count")]
        [MinValue(0)]
        /// <summary>穿透次数，投射物可以穿透的目标数量，0表示命中第一个目标后消失</summary>
        public int pierceCount = 0;

        [BoxGroup("Pierce Settings")]
        [LabelText("Pierce Damage Reduction")]
        [Range(0f, 1f)]
        [ShowIf("@pierceCount > 0")]
        /// <summary>穿透伤害衰减，每次穿透后伤害减少的比例</summary>
        public float pierceDamageReduction = 0.2f;

        [BoxGroup("Collision Settings")]
        [LabelText("Collision Radius")]
        [MinValue(0.1f)]
        /// <summary>碰撞半径，投射物的有效碰撞检测范围</summary>
        public float collisionRadius = 0.5f;

        [BoxGroup("Collision Settings")]
        [LabelText("Hit Effect")]
        /// <summary>命中特效，投射物击中目标时播放的粒子效果</summary>
        public GameObject hitEffect;

        [BoxGroup("Collision Settings")]
        [LabelText("Destroy on Hit")]
        /// <summary>命中时销毁，true时投射物命中后立即消失（不穿透）</summary>
        public bool destroyOnHit = true;

        [BoxGroup("Target Settings")]
        [LabelText("Launch Position")]
        /// <summary>发射位置偏移，相对于施法者的发射起点偏移</summary>
        public Vector3 launchPosition = Vector3.zero;

        [BoxGroup("Target Settings")]
        [LabelText("Target Position")]
        /// <summary>目标位置，投射物的飞行终点坐标</summary>
        public Vector3 targetPosition = Vector3.forward * 10f;

        [BoxGroup("Target Settings")]
        [LabelText("Use World Position")]
        /// <summary>使用世界坐标，true时目标位置为世界坐标，false时为相对坐标</summary>
        public bool useWorldPosition = false;

        /// <summary>最大旅行距离别名，用于Visualizer兼容</summary>
        public float maxTravelDistance => maxRange;

        /// <summary>命中伤害值，用于Visualizer兼容</summary>
        public float damageOnHit = 0f;

        /// <summary>投射物实例引用，用于跟踪和控制生成的投射物GameObject</summary>
        private GameObject projectileInstance;
        /// <summary>实际发射位置，经过计算后的世界坐标发射点</summary>
        private Vector3 actualLaunchPosition;
        /// <summary>实际目标位置，经过计算后的世界坐标目标点</summary>
        private Vector3 actualTargetPosition;
        /// <summary>已穿透次数，记录当前投射物已经穿透的目标数量</summary>
        private int currentPierceCount;

        public override string GetActionName()
        {
            return "Projectile Action";
        }

        public override void OnEnter()
        {
            // 计算发射位置和目标位置
            var casterTransform = UnityEngine.Object.FindFirstObjectByType<Transform>();
            if (casterTransform != null)
            {
                actualLaunchPosition = casterTransform.position + launchPosition;

                if (useWorldPosition)
                {
                    actualTargetPosition = targetPosition;
                }
                else
                {
                    actualTargetPosition = casterTransform.position + targetPosition;
                }
            }
            else
            {
                actualLaunchPosition = launchPosition;
                actualTargetPosition = targetPosition;
            }

            Debug.Log($"[ProjectileAction] Launching {projectileType} projectile from {actualLaunchPosition} to {actualTargetPosition}");
            CreateProjectile();
        }

        public override void OnTick(int relativeFrame)
        {
            // 更新投射物位置和状态
            if (projectileInstance != null)
            {
                UpdateProjectilePosition(relativeFrame);
                CheckCollisions();

                // 检查是否超出最大距离
                float currentDistance = Vector3.Distance(actualLaunchPosition, projectileInstance.transform.position);
                if (currentDistance >= maxRange)
                {
                    Debug.Log($"[ProjectileAction] Projectile reached max range ({maxRange}), destroying");
                    DestroyProjectile();
                }
            }
        }

        public override void OnExit()
        {
            // 确保投射物被正确清理
            if (projectileInstance != null)
            {
                DestroyProjectile();
            }
            Debug.Log($"[ProjectileAction] Projectile action completed");
        }

        /// <summary>创建投射物实例</summary>
        private void CreateProjectile()
        {
            if (projectilePrefab != null)
            {
                projectileInstance = UnityEngine.Object.Instantiate(projectilePrefab, actualLaunchPosition, Quaternion.identity);
                projectileInstance.transform.localScale = Vector3.one * projectileSize;

                // 设置初始朝向
                Vector3 direction = (actualTargetPosition - actualLaunchPosition).normalized;
                if (direction != Vector3.zero)
                {
                    projectileInstance.transform.rotation = Quaternion.LookRotation(direction);
                }

                // 创建拖尾效果
                if (trailEffect != null)
                {
                    UnityEngine.Object.Instantiate(trailEffect, projectileInstance.transform);
                }

                currentPierceCount = 0;
            }
            else
            {
                Debug.LogWarning("[ProjectileAction] No projectile prefab assigned!");
            }
        }

        /// <summary>更新投射物位置</summary>
        /// <param name="relativeFrame">相对帧数</param>
        private void UpdateProjectilePosition(int relativeFrame)
        {
            if (projectileInstance == null) return;

            float deltaTime = Time.fixedDeltaTime;
            Vector3 currentPosition = projectileInstance.transform.position;

            switch (projectileType)
            {
                case ProjectileType.Linear:
                    Vector3 direction = (actualTargetPosition - actualLaunchPosition).normalized;
                    Vector3 movement = direction * projectileSpeed * deltaTime;
                    projectileInstance.transform.position = currentPosition + movement;
                    break;

                case ProjectileType.Arc:
                    float progress = Vector3.Distance(actualLaunchPosition, currentPosition) /
                                   Vector3.Distance(actualLaunchPosition, actualTargetPosition);
                    progress = Mathf.Clamp01(progress);

                    Vector3 linearMovement = Vector3.MoveTowards(currentPosition, actualTargetPosition, projectileSpeed * deltaTime);
                    float arcOffset = arcHeight * Mathf.Sin(progress * Mathf.PI);
                    projectileInstance.transform.position = linearMovement + Vector3.up * arcOffset;
                    break;

                case ProjectileType.Homing:
                    // 追踪逻辑需要动态目标，这里使用固定目标作为示例
                    Vector3 toTarget = (actualTargetPosition - currentPosition).normalized;
                    Vector3 forward = projectileInstance.transform.forward;

                    Vector3 newDirection = Vector3.Slerp(forward, toTarget, trackingStrength * deltaTime);
                    projectileInstance.transform.rotation = Quaternion.LookRotation(newDirection);
                    projectileInstance.transform.position = currentPosition + newDirection * projectileSpeed * deltaTime;
                    break;
            }
        }

        /// <summary>检查碰撞</summary>
        private void CheckCollisions()
        {
            if (projectileInstance == null) return;

            // 在实际项目中，这里会执行真正的碰撞检测
            // 目前只是模拟检查是否到达目标位置
            float distanceToTarget = Vector3.Distance(projectileInstance.transform.position, actualTargetPosition);
            if (distanceToTarget <= collisionRadius)
            {
                Debug.Log($"[ProjectileAction] Projectile hit target at {actualTargetPosition}");
                OnHitTarget();
            }
        }

        /// <summary>命中目标时的处理</summary>
        private void OnHitTarget()
        {
            // 播放命中特效
            if (hitEffect != null && projectileInstance != null)
            {
                UnityEngine.Object.Instantiate(hitEffect, projectileInstance.transform.position, Quaternion.identity);
            }

            // 处理穿透逻辑
            if (pierceCount > 0 && currentPierceCount < pierceCount)
            {
                currentPierceCount++;
                Debug.Log($"[ProjectileAction] Projectile pierced target ({currentPierceCount}/{pierceCount})");
                // 在实际项目中，这里会寻找下一个目标
            }
            else if (destroyOnHit)
            {
                DestroyProjectile();
            }
        }

        /// <summary>销毁投射物</summary>
        private void DestroyProjectile()
        {
            if (projectileInstance != null)
            {
                UnityEngine.Object.Destroy(projectileInstance);
                projectileInstance = null;
            }
        }
    }

    /// <summary>投射物类型枚举</summary>
    public enum ProjectileType
    {
        Linear,     // 直线投射物
        Arc,        // 弧线投射物（抛物线）
        Homing      // 追踪投射物
    }
}