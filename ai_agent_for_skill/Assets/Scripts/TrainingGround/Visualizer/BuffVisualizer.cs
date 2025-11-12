using UnityEngine;
using SkillSystem.Actions;
using TrainingGround.Entity;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// Buff可视化器
    /// </summary>
    public class BuffVisualizer : SkillVisualizerBase<BuffAction>
    {
        protected override void OnVisualizeEnter(BuffAction action, GameObject caster)
        {
            Debug.Log($"[BuffVisualizer] Visualizing buff action from {caster.name}");
            ExecuteBuffVisualization(action, caster);
        }

        protected override void OnVisualizeTick(BuffAction action, GameObject caster, int relativeFrame)
        {
            // Buff通常在Enter时应用，Tick不需要处理
        }

        protected override void OnVisualizeExit(BuffAction action, GameObject caster)
        {
            // Buff由实体的Buff系统管理过期
        }

        private void ExecuteBuffVisualization(BuffAction action, GameObject caster)
        {
            // 创建BuffData
            var buffData = new BuffData
            {
                buffId = System.Guid.NewGuid().ToString(),
                buffName = action.buffName,
                duration = action.durationSeconds,
                buffType = ConvertBuffType(action.buffType),
                damagePerSecond = action.damagePerSecond,
                healPerSecond = action.healPerSecond,
                moveSpeedModifier = action.moveSpeedModifier,
                attackSpeedModifier = action.attackSpeedModifier
            };

            // 获取目标
            var targets = GetTargets(action, caster);

            foreach (var target in targets)
            {
                target.AddBuff(buffData);
                Debug.Log($"[BuffVisualizer] Applied buff '{buffData.buffName}' to {target.EntityName}");
            }
        }

        private System.Collections.Generic.List<IEntity> GetTargets(BuffAction action, GameObject caster)
        {
            var targets = new System.Collections.Generic.List<IEntity>();

            // 根据目标筛选器获取目标
            var casterEntity = caster.GetComponent<IEntity>();

            if (action.targetFilter == TargetFilter.Self)
            {
                if (casterEntity != null)
                {
                    targets.Add(casterEntity);
                }
            }
            else
            {
                // 获取玩家的当前目标
                var playerCharacter = caster.GetComponent<PlayerCharacter>();
                var primaryTarget = playerCharacter?.GetCurrentTarget();

                if (primaryTarget != null)
                {
                    targets.Add(primaryTarget);
                }
                else
                {
                    // 如果没有目标，尝试获取最近的实体
                    var nearestEntity = EntityManager.Instance.GetNearestEntity(caster.transform.position);
                    if (nearestEntity != null && nearestEntity.GameObject != caster)
                    {
                        targets.Add(nearestEntity);
                    }
                }
            }

            return targets;
        }

        private TrainingGround.Entity.BuffType ConvertBuffType(SkillSystem.Actions.BuffType skillBuffType)
        {
            switch (skillBuffType)
            {
                case SkillSystem.Actions.BuffType.Positive:
                    return TrainingGround.Entity.BuffType.Positive;
                case SkillSystem.Actions.BuffType.Negative:
                    return TrainingGround.Entity.BuffType.Negative;
                case SkillSystem.Actions.BuffType.Neutral:
                    return TrainingGround.Entity.BuffType.Neutral;
                default:
                    return TrainingGround.Entity.BuffType.Neutral;
            }
        }
    }
}
