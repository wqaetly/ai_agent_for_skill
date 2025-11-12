using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 传送行为脚�?
    /// 功能概述：实现各种传送效果，包括瞬间传送、延迟传送、群体传送、双向传送等�?
    /// 支持传送条件检查、传送动画、传送限制、传送反馈等功能�?
    /// 适用于DOTA2中的传送技能，如闪烁、传送卷轴、自然之怒、时空断裂等传送类技能�?
    /// </summary>
    [Serializable]
    [ActionDisplayName("传�?)]
    public class TeleportAction : ISkillAction
    {
        [BoxGroup("Teleport Settings")]
        [LabelText("Teleport Type")]
        /// <summary>传送类型，决定传送的实现方式和特�?/summary>
        public TeleportType teleportType = TeleportType.Instant;

        [BoxGroup("Teleport Settings")]
        [LabelText("Cast Time")]
        [MinValue(0f)]
        [ShowIf("@teleportType != TeleportType.Instant")]
        /// <summary>施法时间，延迟传送的准备时间，单位为�?/summary>
        public float castTime = 3f;

        [BoxGroup("Teleport Settings")]
        [LabelText("Interruptible")]
        [ShowIf("@teleportType == TeleportType.Channeled")]
        /// <summary>可打断，true时传送过程可以被伤害或控制技能打�?/summary>
        public bool interruptible = true;

        [BoxGroup("Target Settings")]
        [LabelText("Target Selection")]
        /// <summary>目标选择方式，决定传送目的地的选择方法</summary>
        public TargetSelection targetSelection = TargetSelection.Position;

        [BoxGroup("Target Settings")]
        [LabelText("Target Position")]
        [ShowIf("@targetSelection == TargetSelection.Position")]
        /// <summary>目标位置，传送的目的地坐�?/summary>
        public Vector3 targetPosition = Vector3.forward * 10f;

        [BoxGroup("Target Settings")]
        [LabelText("Use World Position")]
        [ShowIf("@targetSelection == TargetSelection.Position")]
        /// <summary>使用世界坐标，true时目标位置为世界坐标，false时为相对坐标</summary>
        public bool useWorldPosition = false;

        [BoxGroup("Target Settings")]
        [LabelText("Max Range")]
        [MinValue(0f)]
        [ShowIf("@targetSelection != TargetSelection.Global")]
        /// <summary>最大传送距离，传送的距离限制</summary>
        public float maxRange = 1200f;

        [BoxGroup("Range Settings")]
        [LabelText("Min Range")]
        [MinValue(0f)]
        /// <summary>最小传送距离，防止超近距离传送的限制</summary>
        public float minRange = 0f;

        [BoxGroup("Range Settings")]
        [LabelText("Range Check Mode")]
        /// <summary>距离检查模式，决定如何计算和限制传送距�?/summary>
        public RangeCheckMode rangeCheckMode = RangeCheckMode.Direct;

        [BoxGroup("Validation Settings")]
        [LabelText("Check Landing Space")]
        /// <summary>检查落地空间，true时验证目标位置是否有足够空间</summary>
        public bool checkLandingSpace = true;

        [BoxGroup("Validation Settings")]
        [LabelText("Landing Radius")]
        [MinValue(0.1f)]
        [ShowIf("checkLandingSpace")]
        /// <summary>落地半径，检查落地空间时的单位碰撞半�?/summary>
        public float landingRadius = 1f;

        [BoxGroup("Validation Settings")]
        [LabelText("Avoid Obstacles")]
        /// <summary>避开障碍物，true时自动寻找附近可用的落地�?/summary>
        public bool avoidObstacles = true;

        [BoxGroup("Validation Settings")]
        [LabelText("Max Search Distance")]
        [MinValue(0f)]
        [ShowIf("avoidObstacles")]
        /// <summary>最大搜索距离，寻找替代落地点时的搜索范�?/summary>
        public float maxSearchDistance = 3f;

        [BoxGroup("Group Settings")]
        [LabelText("Affect Multiple Units")]
        /// <summary>影响多个单位，true时可以传送多个单�?/summary>
        public bool affectMultipleUnits = false;

        [BoxGroup("Group Settings")]
        [LabelText("Affected Units")]
        [ShowIf("affectMultipleUnits")]
        /// <summary>影响的单位类型，定义哪些类型的单位会被传�?/summary>
        public AffectedUnits affectedUnits = AffectedUnits.Allies;

        [BoxGroup("Group Settings")]
        [LabelText("Affect Radius")]
        [MinValue(0f)]
        [ShowIf("affectMultipleUnits")]
        /// <summary>影响半径，群体传送时的作用范�?/summary>
        public float affectRadius = 5f;

        [BoxGroup("Special Effects")]
        [LabelText("Leave Portal")]
        /// <summary>留下传送门，true时在原位置留下可使用的传送门</summary>
        public bool leavePortal = false;

        [BoxGroup("Special Effects")]
        [LabelText("Portal Duration")]
        [MinValue(0f)]
        [ShowIf("leavePortal")]
        /// <summary>传送门持续时间，传送门存在的时长，单位为秒</summary>
        public float portalDuration = 10f;

        [BoxGroup("Special Effects")]
        [LabelText("Bidirectional Portal")]
        [ShowIf("leavePortal")]
        /// <summary>双向传送门，true时传送门可以双向使用</summary>
        public bool bidirectionalPortal = false;

        [BoxGroup("Visual Settings")]
        [LabelText("Cast Effect")]
        /// <summary>施法特效，开始传送时的视觉效�?/summary>
        public GameObject castEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Teleport Out Effect")]
        /// <summary>传送离开特效，从原位置消失时的视觉效�?/summary>
        public GameObject teleportOutEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Teleport In Effect")]
        /// <summary>传送到达特效，在目标位置出现时的视觉效�?/summary>
        public GameObject teleportInEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Portal Effect")]
        [ShowIf("leavePortal")]
        /// <summary>传送门特效，传送门的持续视觉效�?/summary>
        public GameObject portalEffect;

        [BoxGroup("Audio Settings")]
        [LabelText("Cast Sound")]
        /// <summary>施法音效，开始传送时的音�?/summary>
        public AudioClip castSound;

        [BoxGroup("Audio Settings")]
        [LabelText("Teleport Sound")]
        /// <summary>传送音效，传送完成时的音�?/summary>
        public AudioClip teleportSound;

        /// <summary>原始位置，记录传送前的位�?/summary>
        private Vector3 originalPosition;
        /// <summary>实际目标位置，经过验证和调整后的最终传送位�?/summary>
        private Vector3 actualTargetPosition;
        /// <summary>传送开始时间，用于计算延迟传送的时间</summary>
        private float teleportStartTime;
        /// <summary>是否正在传送过程中</summary>
        private bool isTeleporting;
        /// <summary>传送门实例，生成的传送门GameObject引用</summary>
        private GameObject portalInstance;

        public override string GetActionName()
        {
            return "Teleport Action";
        }

        public override void OnEnter()
        {
            var casterTransform = GetCasterTransform();
            if (casterTransform != null)
            {
                originalPosition = casterTransform.position;
            }

            Debug.Log($"[TeleportAction] Starting {teleportType} teleport");

            // 计算目标位置
            if (!CalculateTargetPosition())
            {
                Debug.LogWarning("[TeleportAction] Invalid target position, aborting teleport");
                return;
            }

            // 验证传送条�?
            if (!ValidateTeleport())
            {
                Debug.LogWarning("[TeleportAction] Teleport validation failed, aborting");
                return;
            }

            // 开始传送过�?
            StartTeleport();
        }

        public override void OnTick(int relativeFrame)
        {
            if (!isTeleporting) return;

            float currentTime = Time.time;
            float elapsedTime = currentTime - teleportStartTime;

            switch (teleportType)
            {
                case TeleportType.Instant:
                    // 瞬间传送已在OnEnter中完�?
                    break;

                case TeleportType.Delayed:
                    if (elapsedTime >= castTime)
                    {
                        ExecuteTeleport();
                    }
                    else
                    {
                        // 显示延迟传送的进度
                        if (relativeFrame % 30 == 0)
                        {
                            float progress = elapsedTime / castTime;
                            Debug.Log($"[TeleportAction] Teleport progress: {progress:P0}");
                        }
                    }
                    break;

                case TeleportType.Channeled:
                    if (elapsedTime >= castTime)
                    {
                        ExecuteTeleport();
                    }
                    else
                    {
                        // 检查引导是否被打断
                        if (interruptible && CheckInterruption())
                        {
                            Debug.Log("[TeleportAction] Teleport interrupted!");
                            CancelTeleport();
                            return;
                        }
                    }
                    break;
            }
        }

        public override void OnExit()
        {
            if (isTeleporting)
            {
                // 如果传送还未完成，尝试完成或取�?
                if (teleportType == TeleportType.Instant)
                {
                    ExecuteTeleport();
                }
                else
                {
                    CancelTeleport();
                }
            }

            Debug.Log("[TeleportAction] Teleport action completed");
        }

        /// <summary>计算目标位置</summary>
        /// <returns>是否成功计算出有效目标位�?/returns>
        private bool CalculateTargetPosition()
        {
            Vector3 basePosition = originalPosition;

            switch (targetSelection)
            {
                case TargetSelection.Position:
                    if (useWorldPosition)
                    {
                        actualTargetPosition = targetPosition;
                    }
                    else
                    {
                        actualTargetPosition = basePosition + targetPosition;
                    }
                    break;

                case TargetSelection.RandomInRange:
                    Vector2 randomCircle = UnityEngine.Random.insideUnitCircle * maxRange;
                    actualTargetPosition = basePosition + new Vector3(randomCircle.x, 0f, randomCircle.y);
                    break;

                case TargetSelection.NearestAlly:
                case TargetSelection.NearestEnemy:
                    // 在实际项目中，这里会搜索最近的目标单位
                    actualTargetPosition = basePosition + Vector3.forward * 5f; // 模拟位置
                    break;

                case TargetSelection.Global:
                    actualTargetPosition = targetPosition; // 全局传送忽略距离限�?
                    break;

                default:
                    return false;
            }

            Debug.Log($"[TeleportAction] Target position calculated: {actualTargetPosition}");
            return true;
        }

        /// <summary>验证传送是否可�?/summary>
        /// <returns>传送是否有�?/returns>
        private bool ValidateTeleport()
        {
            float distance = Vector3.Distance(originalPosition, actualTargetPosition);

            // 距离检�?
            if (targetSelection != TargetSelection.Global)
            {
                if (distance < minRange)
                {
                    Debug.LogWarning($"[TeleportAction] Distance {distance:F1} below minimum {minRange}");
                    return false;
                }

                if (distance > maxRange)
                {
                    Debug.LogWarning($"[TeleportAction] Distance {distance:F1} exceeds maximum {maxRange}");
                    return false;
                }
            }

            // 落地空间检�?
            if (checkLandingSpace && !ValidateLandingSpace())
            {
                if (avoidObstacles)
                {
                    Vector3 adjustedPosition = FindAlternateLandingPosition();
                    if (adjustedPosition != Vector3.zero)
                    {
                        actualTargetPosition = adjustedPosition;
                        Debug.Log($"[TeleportAction] Adjusted target position to {actualTargetPosition}");
                    }
                    else
                    {
                        Debug.LogWarning("[TeleportAction] No suitable landing position found");
                        return false;
                    }
                }
                else
                {
                    return false;
                }
            }

            return true;
        }

        /// <summary>验证落地空间</summary>
        /// <returns>落地位置是否可用</returns>
        private bool ValidateLandingSpace()
        {
            // 在实际项目中，这里会进行碰撞检�?
            Collider[] overlapping = Physics.OverlapSphere(actualTargetPosition, landingRadius);
            bool hasObstacle = overlapping.Length > 0;

            Debug.Log($"[TeleportAction] Landing space validation: {(hasObstacle ? "BLOCKED" : "CLEAR")}");
            return !hasObstacle;
        }

        /// <summary>寻找替代落地位置</summary>
        /// <returns>可用的替代位置，如果没有找到则返回Vector3.zero</returns>
        private Vector3 FindAlternateLandingPosition()
        {
            int attempts = 8; // 尝试8个方�?
            float searchStep = maxSearchDistance / 3f;

            for (int ring = 1; ring <= 3; ring++)
            {
                float currentRadius = searchStep * ring;

                for (int i = 0; i < attempts; i++)
                {
                    float angle = (360f / attempts) * i;
                    Vector3 direction = new Vector3(Mathf.Cos(angle * Mathf.Deg2Rad), 0f, Mathf.Sin(angle * Mathf.Deg2Rad));
                    Vector3 testPosition = actualTargetPosition + direction * currentRadius;

                    if (Physics.OverlapSphere(testPosition, landingRadius).Length == 0)
                    {
                        Debug.Log($"[TeleportAction] Found alternate position at {testPosition}");
                        return testPosition;
                    }
                }
            }

            return Vector3.zero;
        }

        /// <summary>开始传送过�?/summary>
        private void StartTeleport()
        {
            isTeleporting = true;
            teleportStartTime = Time.time;

            // 播放施法特效
            if (castEffect != null)
            {
                UnityEngine.Object.Instantiate(castEffect, originalPosition, Quaternion.identity);
            }

            if (castSound != null)
            {
                Debug.Log("[TeleportAction] Playing cast sound");
            }

            if (teleportType == TeleportType.Instant)
            {
                ExecuteTeleport();
            }
            else
            {
                Debug.Log($"[TeleportAction] Channeling teleport for {castTime}s");
            }
        }

        /// <summary>执行传�?/summary>
        private void ExecuteTeleport()
        {
            if (!isTeleporting) return;

            Debug.Log($"[TeleportAction] Executing teleport from {originalPosition} to {actualTargetPosition}");

            // 播放传送离开特效
            if (teleportOutEffect != null)
            {
                UnityEngine.Object.Instantiate(teleportOutEffect, originalPosition, Quaternion.identity);
            }

            // 移动单位到目标位�?
            PerformTeleportation();

            // 播放传送到达特�?
            if (teleportInEffect != null)
            {
                UnityEngine.Object.Instantiate(teleportInEffect, actualTargetPosition, Quaternion.identity);
            }

            // 创建传送门
            if (leavePortal)
            {
                CreatePortal();
            }

            if (teleportSound != null)
            {
                Debug.Log("[TeleportAction] Playing teleport sound");
            }

            isTeleporting = false;
        }

        /// <summary>执行实际的传送操�?/summary>
        private void PerformTeleportation()
        {
            var casterTransform = GetCasterTransform();
            if (casterTransform != null)
            {
                casterTransform.position = actualTargetPosition;

                // 群体传�?
                if (affectMultipleUnits)
                {
                    TeleportNearbyUnits();
                }
            }
        }

        /// <summary>传送附近的单位</summary>
        private void TeleportNearbyUnits()
        {
            // 在实际项目中，这里会获取范围内的友军并传�?
            Debug.Log($"[TeleportAction] Group teleport - affecting {affectedUnits} within {affectRadius} units");
        }

        /// <summary>创建传送门</summary>
        private void CreatePortal()
        {
            if (portalEffect != null)
            {
                portalInstance = UnityEngine.Object.Instantiate(portalEffect, originalPosition, Quaternion.identity);
                Debug.Log($"[TeleportAction] Created portal at {originalPosition} for {portalDuration}s");

                // 设置传送门消失时间
                UnityEngine.Object.Destroy(portalInstance, portalDuration);
            }
        }

        /// <summary>取消传�?/summary>
        private void CancelTeleport()
        {
            if (!isTeleporting) return;

            Debug.Log("[TeleportAction] Teleport cancelled");
            isTeleporting = false;

            // 在实际项目中，这里可能会有取消传送的特效和音�?
        }

        /// <summary>检查传送是否被打断</summary>
        /// <returns>是否被打�?/returns>
        private bool CheckInterruption()
        {
            // 在实际项目中，这里会检查是否受到伤害或控制效果
            return UnityEngine.Random.value < 0.001f; // 很低的概率，仅作示例
        }

        /// <summary>
        /// 获取技能施法者的Transform
        /// 优先查找Player对象，其次查找带有SkillPlayer组件的对�?
        /// </summary>
        private Transform GetCasterTransform()
        {
            // 方案1：查找名为Player的GameObject（训练场标准设置�?
            GameObject playerObj = GameObject.Find("Player");
            if (playerObj != null)
            {
                return playerObj.transform;
            }

            // 方案2：查找带有SkillPlayer组件的对�?
            var skillPlayer = UnityEngine.Object.FindFirstObjectByType<SkillSystem.Runtime.SkillPlayer>();
            if (skillPlayer != null)
            {
                return skillPlayer.transform;
            }

            // 方案3：查找带有Player标签的对�?
            playerObj = GameObject.FindGameObjectWithTag("Player");
            if (playerObj != null)
            {
                return playerObj.transform;
            }

            Debug.LogWarning("[TeleportAction] 无法找到施法者对象，传送Action无法执行");
            return null;
        }
    }

    /// <summary>传送类型枚�?/summary>
    public enum TeleportType
    {
        Instant,    // 瞬间传�?
        Delayed,    // 延迟传�?
        Channeled   // 引导传�?
    }

    /// <summary>目标选择枚举</summary>
    public enum TargetSelection
    {
        Position,       // 指定位置
        RandomInRange,  // 范围内随�?
        NearestAlly,    // 最近友�?
        NearestEnemy,   // 最近敌�?
        Global          // 全局传�?
    }

    /// <summary>距离检查模式枚�?/summary>
    public enum RangeCheckMode
    {
        Direct,     // 直线距离
        Ground,     // 地面距离
        Pathfinding // 寻路距离
    }

    /// <summary>影响单位类型枚举</summary>
    [System.Flags]
    public enum AffectedUnits
    {
        None = 0,
        Allies = 1 << 0,    // 友军
        Enemies = 1 << 1,   // 敌军
        Self = 1 << 2,      // 自己
        All = ~0            // 全部
    }
}