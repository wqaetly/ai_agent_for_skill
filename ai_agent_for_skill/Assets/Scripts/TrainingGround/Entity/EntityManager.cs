using UnityEngine;
using System.Collections.Generic;
using System.Linq;

namespace TrainingGround.Entity
{
    /// <summary>
    /// 实体管理器 - 单例模式管理场景中的所有实体
    /// </summary>
    public class EntityManager : MonoBehaviour
    {
        private static EntityManager instance;
        public static EntityManager Instance
        {
            get
            {
                if (instance == null)
                {
                    instance = FindObjectOfType<EntityManager>();
                    if (instance == null)
                    {
                        var go = new GameObject("EntityManager");
                        instance = go.AddComponent<EntityManager>();
                    }
                }
                return instance;
            }
        }

        // 实体注册表
        private List<IEntity> allEntities = new List<IEntity>();
        private Dictionary<string, IEntity> entitiesByName = new Dictionary<string, IEntity>();

        void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }

            instance = this;
            DontDestroyOnLoad(gameObject);
        }

        #region 实体注册

        /// <summary>
        /// 注册实体
        /// </summary>
        public void RegisterEntity(IEntity entity)
        {
            if (entity == null || allEntities.Contains(entity))
                return;

            allEntities.Add(entity);

            // 按名称注册（如果有重名，添加后缀）
            string name = entity.EntityName;
            int suffix = 1;
            while (entitiesByName.ContainsKey(name))
            {
                name = $"{entity.EntityName}_{suffix++}";
            }
            entitiesByName[name] = entity;

            Debug.Log($"[EntityManager] Registered entity: {name}");
        }

        /// <summary>
        /// 注销实体
        /// </summary>
        public void UnregisterEntity(IEntity entity)
        {
            if (entity == null)
                return;

            allEntities.Remove(entity);

            // 从名称字典中移除
            var kvp = entitiesByName.FirstOrDefault(x => x.Value == entity);
            if (kvp.Key != null)
            {
                entitiesByName.Remove(kvp.Key);
                Debug.Log($"[EntityManager] Unregistered entity: {kvp.Key}");
            }
        }

        #endregion

        #region 实体查询

        /// <summary>
        /// 获取所有实体
        /// </summary>
        public List<IEntity> GetAllEntities()
        {
            return new List<IEntity>(allEntities);
        }

        /// <summary>
        /// 根据名称获取实体
        /// </summary>
        public IEntity GetEntityByName(string name)
        {
            entitiesByName.TryGetValue(name, out IEntity entity);
            return entity;
        }

        /// <summary>
        /// 获取所有存活的实体
        /// </summary>
        public List<IEntity> GetAliveEntities()
        {
            return allEntities.Where(e => e.IsAlive).ToList();
        }

        /// <summary>
        /// 获取指定类型的实体
        /// </summary>
        public List<T> GetEntitiesOfType<T>() where T : class, IEntity
        {
            return allEntities.OfType<T>().ToList();
        }

        /// <summary>
        /// 获取最近的实体
        /// </summary>
        public IEntity GetNearestEntity(Vector3 position, float maxDistance = Mathf.Infinity)
        {
            IEntity nearest = null;
            float minDistance = maxDistance;

            foreach (var entity in allEntities)
            {
                if (!entity.IsAlive) continue;

                float distance = Vector3.Distance(position, entity.GetPosition());
                if (distance < minDistance)
                {
                    minDistance = distance;
                    nearest = entity;
                }
            }

            return nearest;
        }

        /// <summary>
        /// 获取范围内的所有实体
        /// </summary>
        public List<IEntity> GetEntitiesInRadius(Vector3 center, float radius)
        {
            return allEntities
                .Where(e => e.IsAlive && Vector3.Distance(center, e.GetPosition()) <= radius)
                .ToList();
        }

        /// <summary>
        /// 获取范围内的敌对实体（排除指定实体）
        /// </summary>
        public List<IEntity> GetHostileEntitiesInRadius(Vector3 center, float radius, IEntity exclude = null)
        {
            return allEntities
                .Where(e => e.IsAlive
                    && e != exclude
                    && Vector3.Distance(center, e.GetPosition()) <= radius)
                .ToList();
        }

        #endregion

        #region 玩家和木桩快捷访问

        /// <summary>
        /// 获取玩家角色（假设只有一个）
        /// </summary>
        public PlayerCharacter GetPlayer()
        {
            return GetEntitiesOfType<PlayerCharacter>().FirstOrDefault();
        }

        /// <summary>
        /// 获取所有训练木桩
        /// </summary>
        public List<TrainingDummy> GetAllDummies()
        {
            return GetEntitiesOfType<TrainingDummy>();
        }

        /// <summary>
        /// 获取最近的木桩
        /// </summary>
        public TrainingDummy GetNearestDummy(Vector3 position)
        {
            TrainingDummy nearest = null;
            float minDistance = Mathf.Infinity;

            foreach (var dummy in GetAllDummies())
            {
                if (!dummy.IsAlive) continue;

                float distance = Vector3.Distance(position, dummy.GetPosition());
                if (distance < minDistance)
                {
                    minDistance = distance;
                    nearest = dummy;
                }
            }

            return nearest;
        }

        #endregion

        #region 调试和统计

        /// <summary>
        /// 打印所有实体信息
        /// </summary>
        [ContextMenu("Print All Entities")]
        public void PrintAllEntities()
        {
            Debug.Log($"[EntityManager] Total entities: {allEntities.Count}");
            Debug.Log($"  - Players: {GetEntitiesOfType<PlayerCharacter>().Count}");
            Debug.Log($"  - Dummies: {GetEntitiesOfType<TrainingDummy>().Count}");

            foreach (var entity in allEntities)
            {
                Debug.Log($"  - {entity.EntityName}: HP {entity.CurrentHealth:F0}/{entity.MaxHealth:F0}, Alive: {entity.IsAlive}");
            }
        }

        /// <summary>
        /// 重置所有实体
        /// </summary>
        [ContextMenu("Reset All Entities")]
        public void ResetAllEntities()
        {
            foreach (var entity in allEntities)
            {
                if (entity is TrainingDummy dummy)
                {
                    dummy.ResetDummy();
                }
                else if (entity is PlayerCharacter player)
                {
                    player.ResetCharacter();
                }
            }

            Debug.Log("[EntityManager] All entities reset");
        }

        /// <summary>
        /// 清空所有实体
        /// </summary>
        public void ClearAllEntities()
        {
            allEntities.Clear();
            entitiesByName.Clear();
            Debug.Log("[EntityManager] All entities cleared");
        }

        #endregion
    }
}
