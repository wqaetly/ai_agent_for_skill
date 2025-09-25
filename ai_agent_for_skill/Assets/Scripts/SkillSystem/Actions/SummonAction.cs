using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 召唤行为脚本
    /// 功能概述：在指定位置召唤各种单位、建筑或临时物体，包括召唤生物、陷阱、图腾等。
    /// 支持召唤物的生命周期管理、属性继承、AI行为控制、数量限制等功能。
    /// 适用于DOTA2中的召唤类技能，如召唤狼、先知树人、影魔分身、守卫等召唤物技能。
    /// </summary>
    [Serializable]
    public class SummonAction : ISkillAction
    {
        [BoxGroup("Summon Settings")]
        [LabelText("Summon Type")]
        /// <summary>召唤物类型，决定召唤的是单位、建筑还是其他类型的物体</summary>
        public SummonType summonType = SummonType.Creature;

        [BoxGroup("Summon Settings")]
        [LabelText("Summon Prefab")]
        /// <summary>召唤物预制体，要召唤的GameObject模板</summary>
        public GameObject summonPrefab;

        [BoxGroup("Summon Settings")]
        [LabelText("Summon Count")]
        [MinValue(1)]
        /// <summary>召唤数量，一次召唤创建的单位数量</summary>
        public int summonCount = 1;

        [BoxGroup("Summon Settings")]
        [LabelText("Max Summons")]
        [MinValue(0)]
        [InfoBox("最大召唤物数量限制，0表示无限制")]
        /// <summary>最大召唤数量，召唤者同时拥有的召唤物数量上限</summary>
        public int maxSummons = 5;

        [BoxGroup("Position Settings")]
        [LabelText("Summon Positions")]
        /// <summary>召唤位置数组，定义每个召唤物的相对位置偏移</summary>
        public Vector3[] summonPositions = new Vector3[] { Vector3.zero };

        [BoxGroup("Position Settings")]
        [LabelText("Use Random Positions")]
        /// <summary>使用随机位置，true时在指定范围内随机生成召唤位置</summary>
        public bool useRandomPositions = false;

        [BoxGroup("Position Settings")]
        [LabelText("Random Range")]
        [MinValue(0f)]
        [ShowIf("useRandomPositions")]
        /// <summary>随机范围半径，随机位置生成的范围大小</summary>
        public float randomRange = 3f;

        [BoxGroup("Position Settings")]
        [LabelText("Check Ground")]
        /// <summary>检测地面，true时召唤物会自动调整到地面高度</summary>
        public bool checkGround = true;

        [BoxGroup("Lifetime Settings")]
        [LabelText("Lifetime Mode")]
        /// <summary>生存时间模式，决定召唤物的生命周期管理方式</summary>
        public LifetimeMode lifetimeMode = LifetimeMode.Timed;

        [BoxGroup("Lifetime Settings")]
        [LabelText("Lifetime Duration")]
        [MinValue(0f)]
        [ShowIf("@lifetimeMode == LifetimeMode.Timed")]
        /// <summary>生存时间，召唤物的存在时间，单位为秒</summary>
        public float lifetimeDuration = 30f;

        [BoxGroup("Lifetime Settings")]
        [LabelText("Health Points")]
        [MinValue(1f)]
        [ShowIf("@lifetimeMode == LifetimeMode.Health")]
        /// <summary>生命值，召唤物的最大生命值，受到伤害时会减少</summary>
        public float healthPoints = 100f;

        [BoxGroup("Inheritance Settings")]
        [LabelText("Inherit Caster Stats")]
        /// <summary>继承召唤者属性，true时召唤物会继承部分召唤者的属性</summary>
        public bool inheritCasterStats = false;

        [BoxGroup("Inheritance Settings")]
        [LabelText("Damage Inheritance")]
        [Range(0f, 2f)]
        [ShowIf("inheritCasterStats")]
        /// <summary>攻击力继承比例，召唤物继承召唤者攻击力的百分比</summary>
        public float damageInheritance = 0.5f;

        [BoxGroup("Inheritance Settings")]
        [LabelText("Health Inheritance")]
        [Range(0f, 2f)]
        [ShowIf("inheritCasterStats")]
        /// <summary>生命值继承比例，召唤物继承召唤者生命值的百分比</summary>
        public float healthInheritance = 0.3f;

        [BoxGroup("Behavior Settings")]
        [LabelText("AI Behavior")]
        /// <summary>AI行为模式，决定召唤物的自动行为模式</summary>
        public AIBehavior aiBehavior = AIBehavior.FollowCaster;

        [BoxGroup("Behavior Settings")]
        [LabelText("Attack Range")]
        [MinValue(0f)]
        /// <summary>攻击范围，召唤物的攻击距离</summary>
        public float attackRange = 5f;

        [BoxGroup("Behavior Settings")]
        [LabelText("Follow Distance")]
        [MinValue(0f)]
        [ShowIf("@aiBehavior == AIBehavior.FollowCaster")]
        /// <summary>跟随距离，跟随模式下与召唤者保持的距离</summary>
        public float followDistance = 3f;

        [BoxGroup("Visual Settings")]
        [LabelText("Summon Effect")]
        /// <summary>召唤特效，召唤时播放的视觉效果</summary>
        public GameObject summonEffect;

        [BoxGroup("Visual Settings")]
        [LabelText("Despawn Effect")]
        /// <summary>消失特效，召唤物消失时播放的视觉效果</summary>
        public GameObject despawnEffect;

        [BoxGroup("Audio Settings")]
        [LabelText("Summon Sound")]
        /// <summary>召唤音效，召唤时播放的音频效果</summary>
        public AudioClip summonSound;

        /// <summary>已召唤的实例列表，追踪当前存在的召唤物</summary>
        private System.Collections.Generic.List<GameObject> summonedInstances =
            new System.Collections.Generic.List<GameObject>();

        public override string GetActionName()
        {
            return "Summon Action";
        }

        public override void OnEnter()
        {
            Debug.Log($"[SummonAction] Summoning {summonCount} {summonType}(s)");

            // 检查召唤数量限制
            if (maxSummons > 0)
            {
                CleanupDestroyedSummons();
                int currentSummons = summonedInstances.Count;
                int availableSlots = maxSummons - currentSummons;

                if (availableSlots <= 0)
                {
                    Debug.LogWarning($"[SummonAction] Max summon limit ({maxSummons}) reached!");
                    return;
                }

                if (summonCount > availableSlots)
                {
                    Debug.LogWarning($"[SummonAction] Reducing summon count from {summonCount} to {availableSlots} due to limit");
                    // 移除最旧的召唤物为新的让路
                    int excessCount = summonCount - availableSlots;
                    for (int i = 0; i < excessCount && summonedInstances.Count > 0; i++)
                    {
                        DestroySummon(summonedInstances[0]);
                    }
                }
            }

            PerformSummoning();
        }

        public override void OnTick(int relativeFrame)
        {
            // 监控召唤物状态
            if (relativeFrame % 60 == 0) // 每秒检查一次
            {
                CleanupDestroyedSummons();
                Debug.Log($"[SummonAction] Active summons: {summonedInstances.Count}");
            }
        }

        public override void OnExit()
        {
            Debug.Log($"[SummonAction] Summon action completed. Active summons: {summonedInstances.Count}");
        }

        /// <summary>执行召唤过程</summary>
        private void PerformSummoning()
        {
            var casterTransform = UnityEngine.Object.FindFirstObjectByType<Transform>();
            Vector3 casterPosition = casterTransform != null ? casterTransform.position : Vector3.zero;

            for (int i = 0; i < summonCount; i++)
            {
                Vector3 summonPosition = CalculateSummonPosition(casterPosition, i);
                CreateSummon(summonPosition);
            }

            // 播放召唤效果
            if (summonEffect != null)
            {
                UnityEngine.Object.Instantiate(summonEffect, casterPosition, Quaternion.identity);
            }

            if (summonSound != null)
            {
                Debug.Log($"[SummonAction] Playing summon sound");
            }
        }

        /// <summary>计算召唤位置</summary>
        /// <param name="casterPosition">召唤者位置</param>
        /// <param name="index">召唤物索引</param>
        /// <returns>计算出的召唤位置</returns>
        private Vector3 CalculateSummonPosition(Vector3 casterPosition, int index)
        {
            Vector3 position;

            if (useRandomPositions)
            {
                // 随机位置
                Vector2 randomCircle = UnityEngine.Random.insideUnitCircle * randomRange;
                position = casterPosition + new Vector3(randomCircle.x, 0f, randomCircle.y);
            }
            else if (summonPositions.Length > 0)
            {
                // 使用预定义位置
                int positionIndex = index % summonPositions.Length;
                position = casterPosition + summonPositions[positionIndex];
            }
            else
            {
                // 默认位置
                position = casterPosition;
            }

            // 地面检测
            if (checkGround)
            {
                if (Physics.Raycast(position + Vector3.up * 10f, Vector3.down, out RaycastHit hit, 20f))
                {
                    position.y = hit.point.y;
                }
            }

            return position;
        }

        /// <summary>创建单个召唤物</summary>
        /// <param name="position">召唤位置</param>
        private void CreateSummon(Vector3 position)
        {
            if (summonPrefab == null)
            {
                Debug.LogError("[SummonAction] No summon prefab assigned!");
                return;
            }

            GameObject summon = UnityEngine.Object.Instantiate(summonPrefab, position, Quaternion.identity);
            summonedInstances.Add(summon);

            Debug.Log($"[SummonAction] Created summon at {position}");

            // 配置召唤物属性
            ConfigureSummon(summon);

            // 设置生命周期
            SetupLifetime(summon);
        }

        /// <summary>配置召唤物属性</summary>
        /// <param name="summon">召唤物GameObject</param>
        private void ConfigureSummon(GameObject summon)
        {
            // 在实际项目中，这里会：
            // 1. 设置召唤物的所有者
            // 2. 配置AI行为
            // 3. 应用属性继承
            // 4. 设置攻击目标筛选

            Debug.Log($"[SummonAction] Configuring summon with {aiBehavior} behavior");

            if (inheritCasterStats)
            {
                Debug.Log($"[SummonAction] Applying stat inheritance - Damage: {damageInheritance:P0}, Health: {healthInheritance:P0}");
            }
        }

        /// <summary>设置召唤物生命周期</summary>
        /// <param name="summon">召唤物GameObject</param>
        private void SetupLifetime(GameObject summon)
        {
            switch (lifetimeMode)
            {
                case LifetimeMode.Timed:
                    // 添加定时销毁组件
                    var timedDestroy = summon.AddComponent<TimedDestroy>();
                    timedDestroy.lifetime = lifetimeDuration;
                    timedDestroy.onDestroy = () => OnSummonDestroyed(summon);
                    break;

                case LifetimeMode.Health:
                    // 设置生命值组件
                    Debug.Log($"[SummonAction] Setting summon health to {healthPoints}");
                    break;

                case LifetimeMode.Permanent:
                    Debug.Log($"[SummonAction] Summon created permanently");
                    break;
            }
        }

        /// <summary>销毁指定召唤物</summary>
        /// <param name="summon">要销毁的召唤物</param>
        private void DestroySummon(GameObject summon)
        {
            if (summon != null)
            {
                // 播放消失特效
                if (despawnEffect != null)
                {
                    UnityEngine.Object.Instantiate(despawnEffect, summon.transform.position, Quaternion.identity);
                }

                summonedInstances.Remove(summon);
                UnityEngine.Object.Destroy(summon);
            }
        }

        /// <summary>清理已销毁的召唤物引用</summary>
        private void CleanupDestroyedSummons()
        {
            summonedInstances.RemoveAll(summon => summon == null);
        }

        /// <summary>召唤物被销毁时的回调</summary>
        /// <param name="summon">被销毁的召唤物</param>
        private void OnSummonDestroyed(GameObject summon)
        {
            summonedInstances.Remove(summon);
            Debug.Log($"[SummonAction] Summon destroyed. Remaining: {summonedInstances.Count}");
        }
    }

    /// <summary>召唤类型枚举</summary>
    public enum SummonType
    {
        Creature,   // 生物单位
        Building,   // 建筑结构
        Trap,       // 陷阱装置
        Totem       // 图腾/守卫
    }

    /// <summary>生命周期模式枚举</summary>
    public enum LifetimeMode
    {
        Timed,      // 定时消失
        Health,     // 基于生命值
        Permanent   // 永久存在
    }

    /// <summary>AI行为枚举</summary>
    public enum AIBehavior
    {
        FollowCaster,   // 跟随召唤者
        Aggressive,     // 主动攻击
        Defensive,      // 防御模式
        Stationary      // 静止不动
    }

    /// <summary>定时销毁组件</summary>
    public class TimedDestroy : MonoBehaviour
    {
        public float lifetime = 30f;
        public System.Action onDestroy;

        private void Start()
        {
            Invoke(nameof(DestroyObject), lifetime);
        }

        private void DestroyObject()
        {
            onDestroy?.Invoke();
            Destroy(gameObject);
        }
    }
}