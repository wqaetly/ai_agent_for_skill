using UnityEngine;
using SkillSystem.Actions;
using TrainingGround.Entity;
using TrainingGround.UI;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// 治疗可视化器
    /// </summary>
    public class HealVisualizer : SkillVisualizerBase<HealAction>
    {
        protected override void OnVisualizeEnter(HealAction action, GameObject caster)
        {
            Debug.Log($"[HealVisualizer] Visualizing heal action from {caster.name}");
        }

        protected override void OnVisualizeTick(HealAction action, GameObject caster, int relativeFrame)
        {
            if (relativeFrame == 0)
            {
                ExecuteHealVisualization(action, caster);
            }
        }

        protected override void OnVisualizeExit(HealAction action, GameObject caster)
        {
            // 无需清理
        }

        private void ExecuteHealVisualization(HealAction action, GameObject caster)
        {
            // 计算治疗�?
            float healAmount = action.baseHealAmount;

            // 添加治疗浮动
            if (action.healVariance > 0)
            {
                float variance = Random.Range(-action.healVariance, action.healVariance);
                healAmount *= (1f + variance);
            }

            // 获取目标
            var targets = GetTargets(action, caster);

            foreach (var target in targets)
            {
                // 应用治疗
                target.Heal(healAmount);

                // 显示治疗数字
                ShowHealNumber(target, healAmount);
            }
        }

        private System.Collections.Generic.List<IEntity> GetTargets(HealAction action, GameObject caster)
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
            else if (action.healRadius > 0)
            {
                // AOE治疗
                var entitiesInRadius = EntityManager.Instance.GetEntitiesInRadius(caster.transform.position, action.healRadius);
                foreach (var entity in entitiesInRadius)
                {
                    targets.Add(entity);
                    if (targets.Count >= action.maxTargets)
                        break;
                }
            }

            return targets;
        }

        private void ShowHealNumber(IEntity target, float healAmount)
        {
            Vector3 position = target.GetPosition() + Vector3.up * 2f;
            Color color = Color.green;

            var pool = Object.FindObjectOfType<DamageNumberPool>();
            if (pool != null)
            {
                pool.ShowHealNumber(position, healAmount, color);
            }
            else
            {
                Debug.Log($"[HealVisualizer] Heal: +{healAmount:F0} to {target.EntityName}");
            }
        }
    }
}
