using UnityEngine;
using System.Collections.Generic;
using SkillSystem.Runtime;
using SkillSystem.Data;
using TrainingGround.Entity;
using TrainingGround.Visualizer;
using TrainingGround.UI;
using TrainingGround.Materials;
using TrainingGround.Camera;

namespace TrainingGround.Runtime
{
    /// <summary>
    /// 训练场管理器 - 整合所有训练场组件的核心管理器
    /// 提供一键设置、技能测试、统计数据等功能
    /// </summary>
    public class TrainingGroundManager : MonoBehaviour
    {
        [Header("场景引用")]
        [SerializeField] private GameObject playerPrefab;
        [SerializeField] private GameObject dummyPrefab;
        [SerializeField] private UnityEngine.Camera mainCamera;

        [Header("实体设置")]
        [SerializeField] private int initialDummyCount = 3;
        [SerializeField] private Vector3 dummySpacing = new Vector3(3f, 0f, 0f);
        [SerializeField] private Vector3 dummyStartPosition = new Vector3(0f, 0f, 5f);

        [Header("UI设置")]
        [SerializeField] private Canvas uiCanvas;
        [SerializeField] private bool autoCreateUI = true;

        // 组件引用
        private PlayerCharacter player;
        private List<TrainingDummy> dummies = new List<TrainingDummy>();
        private EntityManager entityManager;
        private SkillVisualizerManager visualizerManager;
        private DamageNumberPool damageNumberPool;
        private SkillTimelinePanel timelinePanel;
        private TrainingGroundCameraController cameraController;

        // 初始化标志
        private bool isInitialized = false;

        void Awake()
        {
            // 初始化EntityManager
            entityManager = EntityManager.Instance;

            // 获取或创建主摄像机
            if (mainCamera == null)
            {
                mainCamera = UnityEngine.Camera.main;
            }

            // 创建并配置相机控制器
            SetupCameraController();

            // 创建UI画布
            if (autoCreateUI && uiCanvas == null)
            {
                CreateUICanvas();
            }
        }

        void Start()
        {
            // 防止重复初始化
            if (isInitialized) return;

            // 自动设置训练场
            SetupTrainingGround();
        }

        /// <summary>
        /// 设置训练场 - 创建玩家、木桩、UI等
        /// </summary>
        [ContextMenu("Setup Training Ground")]
        public void SetupTrainingGround()
        {
            // 防止重复初始化
            if (isInitialized) return;

            Debug.Log("[TrainingGroundManager] Setting up training ground...");

            // 创建玩家
            if (player == null)
            {
                CreatePlayer();
            }

            // 创建木桩
            if (dummies.Count == 0)
            {
                CreateDummies(initialDummyCount);
            }

            // 设置可视化系统
            SetupVisualizationSystem();

            // 设置UI系统
            SetupUISystem();

            Debug.Log($"[TrainingGroundManager] Training ground setup complete! Player: {player != null}, Dummies: {dummies.Count}");

            // 标记为已初始化
            isInitialized = true;
        }

        #region 实体创建

        private void CreatePlayer()
        {
            GameObject playerObj;

            if (playerPrefab != null)
            {
                playerObj = Instantiate(playerPrefab, Vector3.zero, Quaternion.identity);
            }
            else
            {
                // 创建默认玩家
                playerObj = CreateDefaultPlayer();
            }

            playerObj.name = "Player";
            player = playerObj.GetComponent<PlayerCharacter>();

            if (player == null)
            {
                player = playerObj.AddComponent<PlayerCharacter>();
            }

            // 添加CharacterController和移动控制器
            var characterController = playerObj.GetComponent<CharacterController>();
            if (characterController == null)
            {
                characterController = playerObj.AddComponent<CharacterController>();
                // 配置CharacterController参数（匹配Capsule大小）
                characterController.height = 2f;
                characterController.radius = 0.4f;
                characterController.center = Vector3.zero;
                characterController.slopeLimit = 45f; // 斜坡限制45度
                characterController.stepOffset = 0.3f; // 台阶高度0.3
            }

            var movementController = playerObj.GetComponent<TrainingGround.Entity.PlayerMovementController>();
            if (movementController == null)
            {
                movementController = playerObj.AddComponent<TrainingGround.Entity.PlayerMovementController>();
                // 传递相机引用给移动控制器
                if (cameraController != null && cameraController.MainVirtualCamera != null)
                {
                    movementController.SetCamera(cameraController.MainVirtualCamera.transform);
                }
            }

            // 添加SkillPlayer组件
            var skillPlayer = playerObj.GetComponent<SkillPlayer>();
            if (skillPlayer == null)
            {
                skillPlayer = playerObj.AddComponent<SkillPlayer>();
            }

            // 添加血条
            var healthBar = playerObj.GetComponentInChildren<EntityHealthBar>();
            if (healthBar == null)
            {
                GameObject healthBarObj = new GameObject("HealthBar");
                healthBarObj.transform.SetParent(playerObj.transform);
                healthBar = healthBarObj.AddComponent<EntityHealthBar>();
                healthBar.SetTargetEntity(player);
                if (uiCanvas != null)
                {
                    healthBar.SetTargetCanvas(uiCanvas);
                }
                healthBar.SetShowResourceBar(true);
            }
            else
            {
                healthBar.SetTargetEntity(player);
                if (uiCanvas != null)
                {
                    healthBar.SetTargetCanvas(uiCanvas);
                }
                healthBar.SetShowResourceBar(true);
            }

            // 设置相机跟随目标
            if (cameraController != null)
            {
                cameraController.SetFollowTarget(playerObj.transform);
            }

            Debug.Log("[TrainingGroundManager] Player created");
        }

        private void CreateDummies(int count)
        {
            for (int i = 0; i < count; i++)
            {
                CreateDummy(i);
            }
        }

        private TrainingDummy CreateDummy(int index)
        {
            Vector3 position = dummyStartPosition + dummySpacing * index;
            GameObject dummyObj;

            if (dummyPrefab != null)
            {
                dummyObj = Instantiate(dummyPrefab, position, Quaternion.identity);
            }
            else
            {
                // 创建默认木桩
                dummyObj = CreateDefaultDummy(position);
            }

            dummyObj.name = $"TrainingDummy_{index + 1}";
            var dummy = dummyObj.GetComponent<TrainingDummy>();

            if (dummy == null)
            {
                dummy = dummyObj.AddComponent<TrainingDummy>();
            }

            dummies.Add(dummy);

            // 添加血条
            var healthBar = dummyObj.GetComponentInChildren<EntityHealthBar>();
            if (healthBar == null)
            {
                GameObject healthBarObj = new GameObject("HealthBar");
                healthBarObj.transform.SetParent(dummyObj.transform);
                healthBar = healthBarObj.AddComponent<EntityHealthBar>();
                healthBar.SetTargetEntity(dummy);
                if (uiCanvas != null)
                {
                    healthBar.SetTargetCanvas(uiCanvas);
                }
            }
            else
            {
                healthBar.SetTargetEntity(dummy);
                if (uiCanvas != null)
                {
                    healthBar.SetTargetCanvas(uiCanvas);
                }
            }

            Debug.Log($"[TrainingGroundManager] Created dummy {index + 1} at {position}");
            return dummy;
        }

        private GameObject CreateDefaultPlayer()
        {
            GameObject player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            player.transform.localScale = new Vector3(0.8f, 1f, 0.8f);

            var renderer = player.GetComponent<Renderer>();
            if (renderer != null)
            {
                // 使用MaterialLibrary提供的玩家材质
                renderer.material = MaterialLibrary.Instance.GetDefaultPlayerMaterial();
            }

            return player;
        }

        private GameObject CreateDefaultDummy(Vector3 position)
        {
            GameObject dummy = GameObject.CreatePrimitive(PrimitiveType.Cube);
            dummy.transform.position = position;
            dummy.transform.localScale = new Vector3(1f, 2f, 1f);

            var renderer = dummy.GetComponent<Renderer>();
            if (renderer != null)
            {
                // 使用MaterialLibrary提供的敌人材质
                renderer.material = MaterialLibrary.Instance.GetDefaultEnemyMaterial();
            }

            return dummy;
        }

        #endregion

        #region 系统设置

        private void SetupCameraController()
        {
            // 查找或创建相机控制器
            cameraController = FindFirstObjectByType<TrainingGroundCameraController>();

            if (cameraController == null)
            {
                GameObject cameraControllerObj = new GameObject("TrainingGroundCameraController");
                cameraControllerObj.transform.SetParent(transform);
                cameraController = cameraControllerObj.AddComponent<TrainingGroundCameraController>();
            }

            // 确保相机控制器设置为俯视角模式
            cameraController.SwitchToTopDownView();

            Debug.Log("[TrainingGroundManager] Camera controller setup complete - TopDown mode activated");
        }

        private void SetupVisualizationSystem()
        {
            if (player == null) return;

            // 添加SkillVisualizerManager
            visualizerManager = player.GetComponent<SkillVisualizerManager>();
            if (visualizerManager == null)
            {
                visualizerManager = player.gameObject.AddComponent<SkillVisualizerManager>();
            }

            Debug.Log("[TrainingGroundManager] Visualization system setup complete");
        }

        private void SetupUISystem()
        {
            // 创建DamageNumberPool
            var poolObj = GameObject.Find("DamageNumberPool");
            if (poolObj == null)
            {
                poolObj = new GameObject("DamageNumberPool");
                poolObj.transform.SetParent(transform);
            }

            damageNumberPool = poolObj.GetComponent<DamageNumberPool>();
            if (damageNumberPool == null)
            {
                damageNumberPool = poolObj.AddComponent<DamageNumberPool>();
            }

            // 创建SkillTimelinePanel - 添加空值和销毁检查
            if (uiCanvas != null && uiCanvas.transform != null && player != null)
            {
                var skillPlayer = player.GetComponent<SkillPlayer>();
                if (skillPlayer != null)
                {
                    var timelinePanelObj = uiCanvas.transform.Find("SkillTimelinePanel");
                    if (timelinePanelObj == null)
                    {
                        GameObject timelinePanelGO = new GameObject("SkillTimelinePanel");
                        timelinePanelGO.transform.SetParent(uiCanvas.transform, false);

                        var rectTransform = timelinePanelGO.AddComponent<RectTransform>();
                        rectTransform.anchorMin = new Vector2(0.1f, 0.05f);
                        rectTransform.anchorMax = new Vector2(0.9f, 0.15f);
                        rectTransform.offsetMin = Vector2.zero;
                        rectTransform.offsetMax = Vector2.zero;

                        timelinePanel = timelinePanelGO.AddComponent<SkillTimelinePanel>();
                        timelinePanel.SetTargetSkillPlayer(skillPlayer);
                    }
                    else
                    {
                        // 如果已存在，直接获取引用
                        timelinePanel = timelinePanelObj.GetComponent<SkillTimelinePanel>();
                        if (timelinePanel != null)
                        {
                            timelinePanel.SetTargetSkillPlayer(skillPlayer);
                        }
                    }
                }
            }
            else
            {
                Debug.LogWarning("[TrainingGroundManager] Cannot setup SkillTimelinePanel - uiCanvas or player is null or destroyed");
            }

            Debug.Log("[TrainingGroundManager] UI system setup complete");
        }

        private void CreateUICanvas()
        {
            GameObject canvasObj = new GameObject("TrainingGroundCanvas");
            canvasObj.transform.SetParent(transform);

            uiCanvas = canvasObj.AddComponent<Canvas>();
            uiCanvas.renderMode = RenderMode.ScreenSpaceOverlay;

            var scaler = canvasObj.AddComponent<UnityEngine.UI.CanvasScaler>();
            scaler.uiScaleMode = UnityEngine.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);

            canvasObj.AddComponent<UnityEngine.UI.GraphicRaycaster>();

            Debug.Log("[TrainingGroundManager] UI Canvas created");
        }

        #endregion

        #region 公共接口

        /// <summary>
        /// 播放技能
        /// </summary>
        public void PlaySkill(string skillFilePath)
        {
            if (player == null)
            {
                Debug.LogError("[TrainingGroundManager] No player found!");
                return;
            }

            var skillPlayer = player.GetComponent<SkillPlayer>();
            if (skillPlayer == null)
            {
                Debug.LogError("[TrainingGroundManager] No SkillPlayer component found!");
                return;
            }

            // 设置目标为第一个木桩
            if (dummies.Count > 0 && dummies[0] != null)
            {
                player.SetTarget(dummies[0]);
            }

            // 播放技能
            skillPlayer.LoadAndPlaySkill(skillFilePath);
            Debug.Log($"[TrainingGroundManager] Playing skill: {skillFilePath}");
        }

        /// <summary>
        /// 播放技能（从JSON）
        /// </summary>
        public void PlaySkillFromJson(string jsonData)
        {
            if (player == null)
            {
                Debug.LogError("[TrainingGroundManager] No player found!");
                return;
            }

            var skillPlayer = player.GetComponent<SkillPlayer>();
            if (skillPlayer == null)
            {
                Debug.LogError("[TrainingGroundManager] No SkillPlayer component found!");
                return;
            }

            // 设置目标
            if (dummies.Count > 0 && dummies[0] != null)
            {
                player.SetTarget(dummies[0]);
            }

            // 播放技能
            skillPlayer.LoadAndPlaySkillFromJson(jsonData);
            Debug.Log("[TrainingGroundManager] Playing skill from JSON");
        }

        /// <summary>
        /// 重置所有木桩
        /// </summary>
        [ContextMenu("Reset All Dummies")]
        public void ResetAllDummies()
        {
            foreach (var dummy in dummies)
            {
                if (dummy != null)
                {
                    dummy.ResetDummy();
                }
            }
            Debug.Log("[TrainingGroundManager] All dummies reset");
        }

        /// <summary>
        /// 重置玩家
        /// </summary>
        [ContextMenu("Reset Player")]
        public void ResetPlayer()
        {
            if (player != null)
            {
                player.ResetCharacter();
                Debug.Log("[TrainingGroundManager] Player reset");
            }
        }

        /// <summary>
        /// 获取木桩的伤害统计
        /// </summary>
        public void PrintDummyStatistics()
        {
            Debug.Log("========== Dummy Statistics ==========");
            for (int i = 0; i < dummies.Count; i++)
            {
                var dummy = dummies[i];
                if (dummy != null)
                {
                    var stats = dummy.GetStatistics();
                    Debug.Log($"Dummy {i + 1}:");
                    Debug.Log($"  Total Damage: {stats.totalDamage:F0}");
                    Debug.Log($"  Hit Count: {stats.hitCount}");
                    Debug.Log($"  Avg Damage/Hit: {stats.averageDamagePerHit:F0}");
                    Debug.Log($"  DPS: {stats.dps:F0}");
                }
            }
            Debug.Log("======================================");
        }

        /// <summary>
        /// 添加木桩
        /// </summary>
        public TrainingDummy AddDummy(Vector3? position = null)
        {
            Vector3 pos = position ?? (dummyStartPosition + dummySpacing * dummies.Count);
            var dummy = CreateDummy(dummies.Count);
            dummy.transform.position = pos;
            return dummy;
        }

        /// <summary>
        /// 移除木桩
        /// </summary>
        public void RemoveDummy(TrainingDummy dummy)
        {
            if (dummies.Contains(dummy))
            {
                dummies.Remove(dummy);
                Destroy(dummy.gameObject);
            }
        }

        #endregion

        #region Getter

        public PlayerCharacter Player => player;
        public List<TrainingDummy> Dummies => dummies;
        public SkillVisualizerManager VisualizerManager => visualizerManager;
        public DamageNumberPool DamageNumberPool => damageNumberPool;
        public TrainingGroundCameraController CameraController => cameraController;

        #endregion
    }
}
