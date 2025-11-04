using UnityEngine;
using System.Collections.Generic;

namespace TrainingGround.Entity
{
    /// <summary>
    /// 实体接口 - 定义训练场中所有可交互对象的基础能力
    /// </summary>
    public interface IEntity
    {
        // 基础属性
        GameObject GameObject { get; }
        Transform Transform { get; }
        string EntityName { get; }

        // 生命值系统
        float CurrentHealth { get; }
        float MaxHealth { get; }
        float HealthPercentage { get; }

        // 护盾系统
        float CurrentShield { get; }
        float MaxShield { get; }

        // 资源系统（蓝量/能量）
        float CurrentResource { get; }
        float MaxResource { get; }

        // 伤害相关
        void TakeDamage(float amount, DamageType damageType, Vector3 sourcePosition);
        void Heal(float amount);
        void AddShield(float amount, float duration);

        // Buff系统
        void AddBuff(BuffData buff);
        void RemoveBuff(string buffId);
        List<BuffData> GetActiveBuffs();

        // 位置相关
        Vector3 GetPosition();
        void SetPosition(Vector3 position);
        void ApplyKnockback(Vector3 direction, float force);

        // 状态
        bool IsAlive { get; }
        bool IsStunned { get; }
        bool IsInvulnerable { get; }
    }

    /// <summary>
    /// Buff数据结构
    /// </summary>
    [System.Serializable]
    public class BuffData
    {
        public string buffId;
        public string buffName;
        public Sprite icon;
        public float duration;
        public float remainingTime;
        public int stackCount;
        public BuffType buffType;

        // Buff效果参数
        public float damagePerSecond;
        public float healPerSecond;
        public float moveSpeedModifier;
        public float attackSpeedModifier;
    }

    /// <summary>
    /// Buff类型
    /// </summary>
    public enum BuffType
    {
        Positive,   // 增益
        Negative,   // 减益
        Neutral     // 中性
    }

    /// <summary>
    /// 伤害类型（与SkillSystem.Actions.DamageType保持一致）
    /// </summary>
    public enum DamageType
    {
        Physical,   // 物理伤害
        Magical,    // 魔法伤害
        Pure        // 纯粹伤害
    }
}
