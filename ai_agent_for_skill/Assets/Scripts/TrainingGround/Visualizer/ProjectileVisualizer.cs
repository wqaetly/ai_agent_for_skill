using UnityEngine;
using System.Collections.Generic;
using SkillSystem.Actions;
using TrainingGround.Entity;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// 投射物可视化器
    /// </summary>
    public class ProjectileVisualizer : SkillVisualizerBase<ProjectileAction>
    {
        private Dictionary<ProjectileAction, GameObject> activeProjectiles = new Dictionary<ProjectileAction, GameObject>();

        protected override void OnVisualizeEnter(ProjectileAction action, GameObject caster)
        {
            Debug.Log($"[ProjectileVisualizer] Creating projectile from {caster.name}");

            // 创建投射物GameObject
            GameObject projectile = CreateProjectileObject(action, caster);

            // 记录投射物
            activeProjectiles[action] = projectile;

            // 启动投射物运动
            var projectileBehavior = projectile.GetComponent<ProjectileBehavior>();
            if (projectileBehavior != null)
            {
                projectileBehavior.Launch(action, caster);
            }
        }

        protected override void OnVisualizeTick(ProjectileAction action, GameObject caster, int relativeFrame)
        {
            // 投射物的运动由ProjectileBehavior组件自己管理
        }

        protected override void OnVisualizeExit(ProjectileAction action, GameObject caster)
        {
            // 清理投射物
            if (activeProjectiles.TryGetValue(action, out GameObject projectile))
            {
                if (projectile != null)
                {
                    Object.Destroy(projectile);
                }
                activeProjectiles.Remove(action);
            }
        }

        private GameObject CreateProjectileObject(ProjectileAction action, GameObject caster)
        {
            // 创建基础GameObject
            GameObject projectile = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            projectile.name = "Projectile";
            projectile.transform.localScale = Vector3.one * 0.3f;

            // 移除碰撞体（我们用自己的碰撞检测）
            Object.Destroy(projectile.GetComponent<Collider>());

            // 设置起始位置（施法者前方）
            Vector3 startPosition = caster.transform.position + Vector3.up + caster.transform.forward * 0.5f;
            projectile.transform.position = startPosition;

            // 设置颜色（根据投射物类型）
            var renderer = projectile.GetComponent<Renderer>();
            if (renderer != null)
            {
                var material = new Material(Shader.Find("Standard"));
                material.color = GetProjectileColor(action);
                material.SetFloat("_Metallic", 0.5f);
                renderer.material = material;
            }

            // 添加拖尾
            var trail = projectile.AddComponent<TrailRenderer>();
            trail.time = 0.5f;
            trail.startWidth = 0.2f;
            trail.endWidth = 0.05f;
            trail.material = new Material(Shader.Find("Sprites/Default"));
            trail.startColor = GetProjectileColor(action);
            trail.endColor = new Color(GetProjectileColor(action).r, GetProjectileColor(action).g, GetProjectileColor(action).b, 0f);

            // 添加行为组件
            var behavior = projectile.AddComponent<ProjectileBehavior>();

            return projectile;
        }

        private Color GetProjectileColor(ProjectileAction action)
        {
            // 根据不同投射物类型返回不同颜色
            // 这里可以根据action的参数来决定
            return new Color(1f, 0.5f, 0f); // 默认橙色
        }

        public override void Cleanup()
        {
            // 清理所有投射物
            foreach (var projectile in activeProjectiles.Values)
            {
                if (projectile != null)
                {
                    Object.Destroy(projectile);
                }
            }
            activeProjectiles.Clear();
        }
    }

    /// <summary>
    /// 投射物行为组件 - 控制投射物的飞行和碰撞
    /// </summary>
    public class ProjectileBehavior : MonoBehaviour
    {
        private ProjectileAction actionData;
        private GameObject caster;
        private Vector3 targetPosition;
        private float speed;
        private float lifetime;
        private float elapsedTime = 0f;

        public void Launch(ProjectileAction action, GameObject casterObject)
        {
            actionData = action;
            caster = casterObject;
            speed = action.projectileSpeed;
            lifetime = action.maxTravelDistance / speed; // 根据最大距离计算生命周期

            // 确定目标位置
            DetermineTargetPosition();
        }

        private void DetermineTargetPosition()
        {
            // 尝试获取目标实体
            var playerCharacter = caster.GetComponent<PlayerCharacter>();
            var target = playerCharacter?.GetCurrentTarget();

            if (target != null)
            {
                targetPosition = target.GetPosition();
            }
            else
            {
                // 如果没有目标，使用施法者的前方
                targetPosition = caster.transform.position + caster.transform.forward * actionData.maxTravelDistance;
            }
        }

        void Update()
        {
            if (actionData == null) return;

            elapsedTime += Time.deltaTime;

            // 移动投射物
            Vector3 direction = (targetPosition - transform.position).normalized;
            transform.position += direction * speed * Time.deltaTime;

            // 检查碰撞
            CheckCollision();

            // 超时或到达目标后销毁
            if (elapsedTime >= lifetime || Vector3.Distance(transform.position, targetPosition) < 0.5f)
            {
                OnHitTarget();
                Destroy(gameObject);
            }
        }

        private void CheckCollision()
        {
            // 简单的距离检测
            var entities = EntityManager.Instance.GetEntitiesInRadius(transform.position, 0.5f);
            foreach (var entity in entities)
            {
                if (entity.GameObject != caster)
                {
                    OnHitEntity(entity);
                    Destroy(gameObject);
                    return;
                }
            }
        }

        private void OnHitEntity(IEntity entity)
        {
            Debug.Log($"[ProjectileBehavior] Hit entity: {entity.EntityName}");

            // 应用伤害（如果有）
            if (actionData.damageOnHit > 0)
            {
                entity.TakeDamage(actionData.damageOnHit, TrainingGround.Entity.DamageType.Magical, caster.transform.position);
            }

            // 触发特效
            CreateHitEffect();
        }

        private void OnHitTarget()
        {
            // 到达目标位置的处理
            CreateHitEffect();
        }

        private void CreateHitEffect()
        {
            // 简单的命中特效（闪光）
            GameObject flash = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            flash.transform.position = transform.position;
            flash.transform.localScale = Vector3.one * 0.5f;

            var renderer = flash.GetComponent<Renderer>();
            if (renderer != null)
            {
                var material = new Material(Shader.Find("Standard"));
                material.color = Color.yellow;
                material.SetFloat("_Metallic", 0.8f);
                renderer.material = material;
            }

            // 移除碰撞体
            Destroy(flash.GetComponent<Collider>());

            // 1秒后销毁
            Destroy(flash, 0.2f);
        }
    }
}
