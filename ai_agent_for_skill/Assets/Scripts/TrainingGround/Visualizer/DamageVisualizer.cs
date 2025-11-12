using UnityEngine;
using SkillSystem.Actions;
using TrainingGround.Entity;
using TrainingGround.UI;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// 伤害可视化器 - 将DamageAction转换为伤害数字和视觉反馈
    /// </summary>
    public class DamageVisualizer : SkillVisualizerBase<DamageAction>
    {
        protected override void OnVisualizeEnter(DamageAction action, GameObject caster)
        {
            Debug.Log($"[DamageVisualizer] Visualizing damage action from {caster.name}");
        }

        protected override void OnVisualizeTick(DamageAction action, GameObject caster, int relativeFrame)
        {
            // 在第一帧执行伤害
            if (relativeFrame == 0)
            {
                ExecuteDamageVisualization(action, caster);
            }
        }

        protected override void OnVisualizeExit(DamageAction action, GameObject caster)
        {
            // 伤害行为通常没有退出时的清理
        }

        private void ExecuteDamageVisualization(DamageAction action, GameObject caster)
        {
            // 计算最终伤害
            float finalDamage = CalculateDamage(action);

            // 获取目标
            var targets = GetTargets(action, caster);

            foreach (var target in targets)
            {
                // 应用伤害
                target.TakeDamage(finalDamage, ConvertDamageType(action.damageType), caster.transform.position);

                // 显示飘字
                ShowDamageNumber(target, finalDamage, action.damageType);

                // 处理生命偷取
                ProcessLifeSteal(action, caster, finalDamage);
            }
        }

        private float CalculateDamage(DamageAction action)
        {
            float damage = action.baseDamage;

            // 伤害浮动
            if (action.damageVariance > 0)
            {
                float variance = Random.Range(-action.damageVariance, action.damageVariance);
                damage *= (1f + variance);
            }

            // 暴击判定
            if (Random.value < action.criticalChance)
            {
                damage *= action.criticalMultiplier;
                Debug.Log($"[DamageVisualizer] Critical hit! Damage: {damage:F1}");
            }

            return damage;
        }

        private System.Collections.Generic.List<IEntity> GetTargets(DamageAction action, GameObject caster)
        {
            var targets = new System.Collections.Generic.List<IEntity>();

            // 获取施法者的目标（从PlayerCharacter获取）
            var playerCharacter = caster.GetComponent<PlayerCharacter>();
            var primaryTarget = playerCharacter?.GetCurrentTarget();

            if (action.damageRadius > 0)
            {
                // AOE伤害 - 获取范围内的目标
                Vector3 center = primaryTarget != null ? primaryTarget.GetPosition() : caster.transform.position;
                var entitiesInRadius = EntityManager.Instance.GetEntitiesInRadius(center, action.damageRadius);

                // 根据目标筛选器过滤
                foreach (var entity in entitiesInRadius)
                {
                    if (ShouldTargetEntity(entity, caster, action.targetFilter))
                    {
                        targets.Add(entity);
                        if (targets.Count >= action.maxTargets)
                            break;
                    }
                }
            }
            else
            {
                // 单体伤害
                if (primaryTarget != null && ShouldTargetEntity(primaryTarget, caster, action.targetFilter))
                {
                    targets.Add(primaryTarget);
                }
                else
                {
                    // 如果没有指定目标，尝试获取最近的敌人
                    var nearestEnemy = EntityManager.Instance.GetNearestDummy(caster.transform.position);
                    if (nearestEnemy != null)
                    {
                        targets.Add(nearestEnemy);
                    }
                }
            }

            return targets;
        }

        private bool ShouldTargetEntity(IEntity entity, GameObject caster, TargetFilter filter)
        {
            switch (filter)
            {
                case TargetFilter.Enemy:
                    // 假设除了自己都是敌人
                    return entity.GameObject != caster;

                case TargetFilter.Ally:
                    // TODO: 实现队伍系统
                    return false;

                case TargetFilter.Self:
                    return entity.GameObject == caster;

                case TargetFilter.All:
                    return true;

                default:
                    return false;
            }
        }

        private void ShowDamageNumber(IEntity target, float damage, SkillSystem.Actions.DamageType damageType)
        {
            // 使用DamageNumber UI系统显示飘字
            Vector3 position = target.GetPosition() + Vector3.up * 2f; // 在目标头顶显示

            // 根据伤害类型选择颜色
            Color color = GetDamageTypeColor(damageType);

            // 创建飘字（需要DamageNumberPool组件）
            var pool = Object.FindObjectOfType<DamageNumberPool>();
            if (pool != null)
            {
                pool.ShowDamageNumber(position, damage, color);
            }
            else
            {
                Debug.Log($"[DamageVisualizer] Damage: {damage:F0} to {target.EntityName} (No DamageNumberPool found)");
            }
        }

        private void ProcessLifeSteal(DamageAction action, GameObject caster, float damage)
        {
            float healAmount = 0f;

            if (action.lifeStealPercentage > 0 && action.damageType == SkillSystem.Actions.DamageType.Physical)
            {
                healAmount = damage * action.lifeStealPercentage;
            }
            else if (action.spellVampPercentage > 0 && action.damageType == SkillSystem.Actions.DamageType.Magical)
            {
                healAmount = damage * action.spellVampPercentage;
            }

            if (healAmount > 0)
            {
                var casterEntity = caster.GetComponent<IEntity>();
                if (casterEntity != null)
                {
                    casterEntity.Heal(healAmount);
                    Debug.Log($"[DamageVisualizer] Life steal: {healAmount:F1}");
                }
            }
        }

        private Entity.DamageType ConvertDamageType(SkillSystem.Actions.DamageType skillDamageType)
        {
            switch (skillDamageType)
            {
                case SkillSystem.Actions.DamageType.Physical:
                    return Entity.DamageType.Physical;
                case SkillSystem.Actions.DamageType.Magical:
                    return Entity.DamageType.Magical;
                case SkillSystem.Actions.DamageType.Pure:
                    return Entity.DamageType.Pure;
                default:
                    return Entity.DamageType.Physical;
            }
        }

        private Color GetDamageTypeColor(SkillSystem.Actions.DamageType damageType)
        {
            switch (damageType)
            {
                case SkillSystem.Actions.DamageType.Physical:
                    return new Color(1f, 0.5f, 0f); // 橙色
                case SkillSystem.Actions.DamageType.Magical:
                    return new Color(0.3f, 0.5f, 1f); // 蓝色
                case SkillSystem.Actions.DamageType.Pure:
                    return new Color(1f, 1f, 0f); // 黄色
                default:
                    return Color.white;
            }
        }
    }
}
