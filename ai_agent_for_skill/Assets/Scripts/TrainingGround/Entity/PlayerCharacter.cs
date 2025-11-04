using UnityEngine;
using System.Collections.Generic;
using System.Linq;
using SkillSystem.Runtime;
using SkillSystem.Data;

namespace TrainingGround.Entity
{
    /// <summary>
    /// 玩家角色 - 技能施放者
    /// </summary>
    public class PlayerCharacter : MonoBehaviour, IEntity
    {
        [Header("基础属性")]
        [SerializeField] private string entityName = "Player";
        [SerializeField] private float maxHealth = 2000f;
        [SerializeField] private float maxShield = 500f;
        [SerializeField] private float maxResource = 1000f; // 蓝量/能量

        [Header("资源再生")]
        [SerializeField] private float resourceRegenPerSecond = 50f;
        [SerializeField] private float healthRegenPerSecond = 10f;

        [Header("技能系统")]
        [SerializeField] private SkillPlayer skillPlayer;

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

        // 资源
        private float currentResource;
        public float CurrentResource => currentResource;
        public float MaxResource => maxResource;

        // 状态
        public bool IsAlive => currentHealth > 0;
        private bool isStunned = false;
        public bool IsStunned => isStunned;
        public bool IsInvulnerable => false;

        // Buff系统
        private List<BuffData> activeBuffs = new List<BuffData>();

        // 目标系统
        private IEntity currentTarget;

        void Awake()
        {
            // 初始化
            currentHealth = maxHealth;
            currentShield = 0f;
            currentResource = maxResource;

            // 获取SkillPlayer组件
            if (skillPlayer == null)
                skillPlayer = GetComponent<SkillPlayer>();

            // 注册到实体管理器
            EntityManager.Instance.RegisterEntity(this);
        }

        void OnDestroy()
        {
            // 从实体管理器注销
            if (EntityManager.Instance != null)
                EntityManager.Instance.UnregisterEntity(this);
        }

        void Update()
        {
            // 更新Buff
            UpdateBuffs();

            // 资源再生
            RegenerateResources();
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

            Debug.Log($"[PlayerCharacter] {entityName} took {amount:F1} {damageType} damage (HP: {currentHealth:F0}/{maxHealth:F0})");

            // 死亡检查
            if (!IsAlive)
            {
                OnDeath();
            }
        }

        public void Heal(float amount)
        {
            if (!IsAlive || amount <= 0) return;

            float oldHealth = currentHealth;
            currentHealth = Mathf.Min(maxHealth, currentHealth + amount);
            float actualHeal = currentHealth - oldHealth;

            Debug.Log($"[PlayerCharacter] {entityName} healed for {actualHeal:F1} (HP: {currentHealth:F0}/{maxHealth:F0})");
        }

        public void AddShield(float amount, float duration)
        {
            if (amount <= 0) return;

            currentShield = Mathf.Min(maxShield, currentShield + amount);

            if (duration > 0)
            {
                Invoke(nameof(DecayShield), duration);
            }

            Debug.Log($"[PlayerCharacter] {entityName} gained {amount:F1} shield (Shield: {currentShield:F0}/{maxShield:F0})");
        }

        #endregion

        #region Buff系统

        public void AddBuff(BuffData buff)
        {
            if (buff == null) return;

            var existing = activeBuffs.FirstOrDefault(b => b.buffId == buff.buffId);
            if (existing != null)
            {
                existing.remainingTime = buff.duration;
                existing.stackCount++;
            }
            else
            {
                buff.remainingTime = buff.duration;
                buff.stackCount = 1;
                activeBuffs.Add(buff);
            }

            Debug.Log($"[PlayerCharacter] {entityName} gained buff: {buff.buffName} (stacks: {buff.stackCount})");
        }

        public void RemoveBuff(string buffId)
        {
            var buff = activeBuffs.FirstOrDefault(b => b.buffId == buffId);
            if (buff != null)
            {
                activeBuffs.Remove(buff);
                Debug.Log($"[PlayerCharacter] {entityName} lost buff: {buff.buffName}");
            }
        }

        public List<BuffData> GetActiveBuffs()
        {
            return new List<BuffData>(activeBuffs);
        }

        private void UpdateBuffs()
        {
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
            // 可以集成CharacterController或Rigidbody实现击退
            Debug.Log($"[PlayerCharacter] {entityName} received knockback: {direction * force}");
        }

        #endregion

        #region 技能系统

        /// <summary>
        /// 消耗资源（蓝量/能量）
        /// </summary>
        public bool ConsumeResource(float amount)
        {
            if (currentResource >= amount)
            {
                currentResource -= amount;
                Debug.Log($"[PlayerCharacter] Consumed {amount} resource (Resource: {currentResource:F0}/{maxResource:F0})");
                return true;
            }

            Debug.LogWarning($"[PlayerCharacter] Not enough resource! (Need: {amount}, Have: {currentResource:F0})");
            return false;
        }

        /// <summary>
        /// 恢复资源
        /// </summary>
        public void RestoreResource(float amount)
        {
            currentResource = Mathf.Min(maxResource, currentResource + amount);
        }

        /// <summary>
        /// 资源再生
        /// </summary>
        private void RegenerateResources()
        {
            // 资源再生
            if (currentResource < maxResource)
            {
                currentResource = Mathf.Min(maxResource, currentResource + resourceRegenPerSecond * Time.deltaTime);
            }

            // 生命再生
            if (currentHealth < maxHealth && healthRegenPerSecond > 0)
            {
                currentHealth = Mathf.Min(maxHealth, currentHealth + healthRegenPerSecond * Time.deltaTime);
            }
        }

        /// <summary>
        /// 施放技能
        /// </summary>
        public void CastSkill(SkillData skillData, IEntity target = null)
        {
            if (skillPlayer == null)
            {
                Debug.LogError("[PlayerCharacter] SkillPlayer component not found!");
                return;
            }

            // 设置目标
            currentTarget = target;

            // 加载并播放技能
            // 注意：需要将SkillData序列化为JSON或直接使用LoadSkillFromJson
            Debug.Log($"[PlayerCharacter] Casting skill: {skillData?.skillName ?? "Unknown"}");

            // TODO: 集成资源消耗检查
            // 这里需要扩展SkillData支持资源消耗字段
        }

        /// <summary>
        /// 获取当前目标
        /// </summary>
        public IEntity GetCurrentTarget()
        {
            return currentTarget;
        }

        /// <summary>
        /// 设置目标
        /// </summary>
        public void SetTarget(IEntity target)
        {
            currentTarget = target;
            Debug.Log($"[PlayerCharacter] Target set to: {target?.EntityName ?? "None"}");
        }

        #endregion

        #region 事件处理

        private void OnDeath()
        {
            Debug.Log($"[PlayerCharacter] {entityName} died");
            // 可以触发死亡事件、播放动画等
        }

        private void DecayShield()
        {
            currentShield = 0f;
        }

        #endregion

        #region 调试方法

        [ContextMenu("Reset Character")]
        public void ResetCharacter()
        {
            currentHealth = maxHealth;
            currentShield = 0f;
            currentResource = maxResource;
            activeBuffs.Clear();
            isStunned = false;

            Debug.Log($"[PlayerCharacter] {entityName} reset");
        }

        [ContextMenu("Print Status")]
        public void PrintStatus()
        {
            Debug.Log($"[PlayerCharacter] {entityName} Status:");
            Debug.Log($"  Health: {currentHealth:F0}/{maxHealth:F0} ({HealthPercentage:P0})");
            Debug.Log($"  Shield: {currentShield:F0}/{maxShield:F0}");
            Debug.Log($"  Resource: {currentResource:F0}/{maxResource:F0}");
            Debug.Log($"  Buffs: {activeBuffs.Count}");
            Debug.Log($"  Target: {currentTarget?.EntityName ?? "None"}");
        }

        #endregion
    }
}
