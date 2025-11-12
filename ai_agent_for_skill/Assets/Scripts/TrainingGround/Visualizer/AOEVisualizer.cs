using UnityEngine;
using System.Collections.Generic;
using SkillSystem.Actions;
using TrainingGround.Entity;
using TrainingGround.Materials;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// AOE范围效果可视化器
    /// </summary>
    public class AOEVisualizer : SkillVisualizerBase<AreaOfEffectAction>
    {
        private Dictionary<AreaOfEffectAction, GameObject> activeAOEs = new Dictionary<AreaOfEffectAction, GameObject>();

        protected override void OnVisualizeEnter(AreaOfEffectAction action, GameObject caster)
        {
            Debug.Log($"[AOEVisualizer] Creating AOE effect from {caster.name}");

            // 创建AOE可视化对�?
            GameObject aoeObject = CreateAOEObject(action, caster);
            activeAOEs[action] = aoeObject;

            // 应用伤害
            ApplyAOEDamage(action, caster, aoeObject.transform.position);
        }

        protected override void OnVisualizeTick(AreaOfEffectAction action, GameObject caster, int relativeFrame)
        {
            // 持续性AOE可以在这里处�?
            // 目前大多数AOE是瞬时的
        }

        protected override void OnVisualizeExit(AreaOfEffectAction action, GameObject caster)
        {
            // 清理AOE对象
            if (activeAOEs.TryGetValue(action, out GameObject aoeObject))
            {
                if (aoeObject != null)
                {
                    Object.Destroy(aoeObject);
                }
                activeAOEs.Remove(action);
            }
        }

        private GameObject CreateAOEObject(AreaOfEffectAction action, GameObject caster)
        {
            // 确定AOE中心位置
            Vector3 center = DetermineAOECenter(action, caster);

            // 创建AOE指示器（地面圆环�?
            GameObject aoeObject = CreateGroundCircle(center, action.radius);
            aoeObject.name = "AOE_Indicator";

            // 添加扩散动画
            var animator = aoeObject.AddComponent<AOEAnimator>();
            animator.Initialize(action.radius, action.duration);

            return aoeObject;
        }

        private Vector3 DetermineAOECenter(AreaOfEffectAction action, GameObject caster)
        {
            if (action.followCaster)
            {
                return caster.transform.position;
            }
            else
            {
                // 尝试获取目标位置
                var playerCharacter = caster.GetComponent<PlayerCharacter>();
                var target = playerCharacter?.GetCurrentTarget();

                if (target != null)
                {
                    return target.GetPosition();
                }
                else
                {
                    // 默认使用施法者前�?
                    return caster.transform.position + caster.transform.forward * 5f;
                }
            }
        }

        private GameObject CreateGroundCircle(Vector3 center, float radius)
        {
            // 创建圆环GameObject
            GameObject circle = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            circle.transform.position = center + Vector3.up * 0.1f; // 稍微抬高避免z-fighting
            circle.transform.localScale = new Vector3(radius * 2f, 0.05f, radius * 2f);

            // 移除碰撞�?
            Object.Destroy(circle.GetComponent<Collider>());

            // 设置材质（半透明红色�?- 使用MaterialLibrary
            var renderer = circle.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material = MaterialLibrary.Instance.GetDefaultAOEMaterial();
            }

            return circle;
        }

        private void ApplyAOEDamage(AreaOfEffectAction action, GameObject caster, Vector3 center)
        {
            // 获取范围内的所有实�?
            var entitiesInRadius = EntityManager.Instance.GetEntitiesInRadius(center, action.radius);

            int hitCount = 0;
            foreach (var entity in entitiesInRadius)
            {
                // 排除施法者（如果需要）
                if (entity.GameObject == caster && !action.affectsCaster)
                    continue;

                // 应用伤害
                if (action.damagePerTick > 0)
                {
                    entity.TakeDamage(action.damagePerTick, TrainingGround.Entity.DamageType.Magical, center);
                    hitCount++;

                    Debug.Log($"[AOEVisualizer] Hit {entity.EntityName} with {action.damagePerTick:F1} damage");
                }

                // 达到最大目标数�?
                if (hitCount >= action.maxTargets)
                    break;
            }

            Debug.Log($"[AOEVisualizer] AOE hit {hitCount} targets in radius {action.radius}");
        }

        public override void Cleanup()
        {
            // 清理所有AOE对象
            foreach (var aoeObject in activeAOEs.Values)
            {
                if (aoeObject != null)
                {
                    Object.Destroy(aoeObject);
                }
            }
            activeAOEs.Clear();
        }
    }

    /// <summary>
    /// AOE动画组件 - 控制AOE的扩散和消失效果
    /// </summary>
    public class AOEAnimator : MonoBehaviour
    {
        private float targetRadius;
        private float duration;
        private float elapsedTime = 0f;
        private Vector3 initialScale;

        public void Initialize(float radius, float durationSeconds)
        {
            targetRadius = radius;
            duration = Mathf.Max(durationSeconds, 0.5f); // 至少0.5�?
            initialScale = new Vector3(0.1f, transform.localScale.y, 0.1f);
            transform.localScale = initialScale;
        }

        void Update()
        {
            elapsedTime += Time.deltaTime;

            // 扩散动画（前半段�?
            if (elapsedTime < duration * 0.3f)
            {
                float t = elapsedTime / (duration * 0.3f);
                float currentRadius = Mathf.Lerp(0.1f, targetRadius, t);
                transform.localScale = new Vector3(currentRadius * 2f, transform.localScale.y, currentRadius * 2f);
            }
            // 保持（中段）
            else if (elapsedTime < duration * 0.7f)
            {
                // 保持最大半�?
            }
            // 消失动画（后段）
            else if (elapsedTime < duration)
            {
                float t = (elapsedTime - duration * 0.7f) / (duration * 0.3f);
                float alpha = Mathf.Lerp(0.3f, 0f, t);

                var renderer = GetComponent<Renderer>();
                if (renderer != null && renderer.material != null)
                {
                    Color color = renderer.material.color;
                    color.a = alpha;
                    renderer.material.color = color;
                }
            }
            else
            {
                // 时间到，销�?
                Destroy(gameObject);
            }
        }
    }
}
