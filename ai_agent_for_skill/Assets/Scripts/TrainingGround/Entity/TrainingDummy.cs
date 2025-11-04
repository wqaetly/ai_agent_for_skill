using UnityEngine;
using System.Collections.Generic;
using System.Linq;

namespace TrainingGround.Entity
{
    /// <summary>
    /// 训练木桩 - 用于测试技能效果的静态目标
    /// </summary>
    public class TrainingDummy : MonoBehaviour, IEntity
    {
        [Header("基础属性")]
        [SerializeField] private string entityName = "Training Dummy";
        [SerializeField] private float maxHealth = 10000f;
        [SerializeField] private float maxShield = 1000f;
        [SerializeField] private float maxResource = 0f; // 木桩不需要资源

        [Header("重置设置")]
        [SerializeField] private bool autoReset = true;
        [SerializeField] private float resetDelay = 3f;

        [Header("视觉反馈")]
        [SerializeField] private Renderer targetRenderer;
        [SerializeField] private Color normalColor = Color.gray;
        [SerializeField] private Color hitColor = Color.red;
        [SerializeField] private Color healColor = Color.green;
        [SerializeField] private float flashDuration = 0.2f;

        // 实体接口实现
        public GameObject GameObject => gameObject;
        public Transform Transform => transform;
        public string EntityName => entityName;

        // 生命值
        private float currentHealth;
        public float CurrentHealth => currentHealth;
        public float MaxHealth => maxHealth;
        public float HealthPercentage => maxHealth > 0 ? currentHealth / maxHealth : 0f;

        // 护盾
        private float currentShield;
        public float CurrentShield => currentShield;
        public float MaxShield => maxShield;

        // 资源（木桩不使用）
        public float CurrentResource => 0f;
        public float MaxResource => maxResource;

        // 状态
        public bool IsAlive => currentHealth > 0;
        public bool IsStunned => false; // 木桩不会被眩晕
        public bool IsInvulnerable => false;

        // Buff系统
        private List<BuffData> activeBuffs = new List<BuffData>();

        // 伤害统计
        private float totalDamageTaken = 0f;
        private float lastDamageTime = 0f;
        private int hitCount = 0;

        // 颜色闪烁
        private Material materialInstance;
        private Coroutine flashCoroutine;

        void Awake()
        {
            // 初始化
            currentHealth = maxHealth;
            currentShield = 0f;

            // 获取Renderer
            if (targetRenderer == null)
                targetRenderer = GetComponent<Renderer>();

            // 创建材质实例
            if (targetRenderer != null)
            {
                materialInstance = targetRenderer.material;
                materialInstance.color = normalColor;
            }

            // 注册到实体管理器
            EntityManager.Instance.RegisterEntity(this);
        }

        void OnDestroy()
        {
            // 从实体管理器注销
            if (EntityManager.Instance != null)
                EntityManager.Instance.UnregisterEntity(this);

            // 清理材质实例
            if (materialInstance != null)
                Destroy(materialInstance);
        }

        void Update()
        {
            // 更新Buff
            UpdateBuffs();
        }

        #region 伤害和治疗

        public void TakeDamage(float amount, DamageType damageType, Vector3 sourcePosition)
        {
            if (!IsAlive || amount <= 0) return;

            // 先扣护盾，再扣血
            float remainingDamage = amount;
            if (currentShield > 0)
            {
                float shieldDamage = Mathf.Min(currentShield, remainingDamage);
                currentShield -= shieldDamage;
                remainingDamage -= shieldDamage;
            }

            if (remainingDamage > 0)
            {
                currentHealth = Mathf.Max(0, currentHealth - remainingDamage);
            }

            // 统计
            totalDamageTaken += amount;
            lastDamageTime = Time.time;
            hitCount++;

            // 视觉反馈
            FlashColor(hitColor);

            // 日志
            Debug.Log($"[TrainingDummy] {entityName} took {amount:F1} {damageType} damage (HP: {currentHealth:F0}/{maxHealth:F0}, Shield: {currentShield:F0})");

            // 死亡检查
            if (!IsAlive && autoReset)
            {
                Invoke(nameof(ResetDummy), resetDelay);
            }
        }

        public void Heal(float amount)
        {
            if (!IsAlive || amount <= 0) return;

            float oldHealth = currentHealth;
            currentHealth = Mathf.Min(maxHealth, currentHealth + amount);
            float actualHeal = currentHealth - oldHealth;

            // 视觉反馈
            FlashColor(healColor);

            Debug.Log($"[TrainingDummy] {entityName} healed for {actualHeal:F1} (HP: {currentHealth:F0}/{maxHealth:F0})");
        }

        public void AddShield(float amount, float duration)
        {
            if (amount <= 0) return;

            currentShield = Mathf.Min(maxShield, currentShield + amount);

            // 如果有持续时间，延迟移除护盾
            if (duration > 0)
            {
                Invoke(nameof(DecayShield), duration);
            }

            Debug.Log($"[TrainingDummy] {entityName} gained {amount:F1} shield (Shield: {currentShield:F0}/{maxShield:F0})");
        }

        #endregion

        #region Buff系统

        public void AddBuff(BuffData buff)
        {
            if (buff == null) return;

            // 检查是否已存在相同Buff
            var existing = activeBuffs.FirstOrDefault(b => b.buffId == buff.buffId);
            if (existing != null)
            {
                // 刷新持续时间或堆叠
                existing.remainingTime = buff.duration;
                existing.stackCount++;
            }
            else
            {
                // 添加新Buff
                buff.remainingTime = buff.duration;
                buff.stackCount = 1;
                activeBuffs.Add(buff);
            }

            Debug.Log($"[TrainingDummy] {entityName} gained buff: {buff.buffName} (stacks: {buff.stackCount})");
        }

        public void RemoveBuff(string buffId)
        {
            var buff = activeBuffs.FirstOrDefault(b => b.buffId == buffId);
            if (buff != null)
            {
                activeBuffs.Remove(buff);
                Debug.Log($"[TrainingDummy] {entityName} lost buff: {buff.buffName}");
            }
        }

        public List<BuffData> GetActiveBuffs()
        {
            return new List<BuffData>(activeBuffs);
        }

        private void UpdateBuffs()
        {
            // 更新Buff持续时间
            for (int i = activeBuffs.Count - 1; i >= 0; i--)
            {
                var buff = activeBuffs[i];
                buff.remainingTime -= Time.deltaTime;

                // 应用Buff效果
                if (buff.damagePerSecond > 0)
                {
                    TakeDamage(buff.damagePerSecond * Time.deltaTime, DamageType.Magical, transform.position);
                }
                else if (buff.healPerSecond > 0)
                {
                    Heal(buff.healPerSecond * Time.deltaTime);
                }

                // 移除过期Buff
                if (buff.remainingTime <= 0)
                {
                    RemoveBuff(buff.buffId);
                }
            }
        }

        #endregion

        #region 位置和移动

        public Vector3 GetPosition()
        {
            return transform.position;
        }

        public void SetPosition(Vector3 position)
        {
            transform.position = position;
        }

        public void ApplyKnockback(Vector3 direction, float force)
        {
            // 木桩默认不会被击退（可以子类化实现）
            Debug.Log($"[TrainingDummy] {entityName} received knockback (ignored)");
        }

        #endregion

        #region 工具方法

        /// <summary>
        /// 重置木桩到初始状态
        /// </summary>
        [ContextMenu("Reset Dummy")]
        public void ResetDummy()
        {
            currentHealth = maxHealth;
            currentShield = 0f;
            activeBuffs.Clear();
            totalDamageTaken = 0f;
            hitCount = 0;

            if (materialInstance != null)
                materialInstance.color = normalColor;

            Debug.Log($"[TrainingDummy] {entityName} reset");
        }

        /// <summary>
        /// 颜色闪烁
        /// </summary>
        private void FlashColor(Color color)
        {
            if (flashCoroutine != null)
                StopCoroutine(flashCoroutine);

            flashCoroutine = StartCoroutine(FlashCoroutine(color));
        }

        private System.Collections.IEnumerator FlashCoroutine(Color color)
        {
            if (materialInstance != null)
                materialInstance.color = color;

            yield return new WaitForSeconds(flashDuration);

            if (materialInstance != null)
                materialInstance.color = normalColor;
        }

        private void DecayShield()
        {
            currentShield = 0f;
        }

        /// <summary>
        /// 获取伤害统计
        /// </summary>
        public DamageStatistics GetStatistics()
        {
            float dps = 0f;
            if (lastDamageTime > 0)
            {
                float duration = lastDamageTime - (lastDamageTime - Time.time);
                dps = duration > 0 ? totalDamageTaken / duration : 0f;
            }

            return new DamageStatistics
            {
                totalDamage = totalDamageTaken,
                hitCount = hitCount,
                averageDamagePerHit = hitCount > 0 ? totalDamageTaken / hitCount : 0f,
                dps = dps
            };
        }

        #endregion
    }

    /// <summary>
    /// 伤害统计数据
    /// </summary>
    [System.Serializable]
    public struct DamageStatistics
    {
        public float totalDamage;
        public int hitCount;
        public float averageDamagePerHit;
        public float dps;
    }
}
