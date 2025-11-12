using UnityEngine;
using System.Collections.Generic;
using SkillSystem.Actions;
using SkillSystem.Runtime;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// 技能可视化管理器 - 监听SkillPlayer事件，分发给各个Visualizer
    /// </summary>
    public class SkillVisualizerManager : MonoBehaviour
    {
        [SerializeField] private SkillPlayer targetSkillPlayer;
        [SerializeField] private GameObject casterObject;

        // 可视化器注册表
        private Dictionary<System.Type, ISkillVisualizer> visualizers = new Dictionary<System.Type, ISkillVisualizer>();

        // 当前活动的Action及其帧数
        private Dictionary<ISkillAction, int> activeActions = new Dictionary<ISkillAction, int>();

        void Awake()
        {
            // 自动获取SkillPlayer
            if (targetSkillPlayer == null)
                targetSkillPlayer = GetComponent<SkillPlayer>();

            // 默认施法者为自己
            if (casterObject == null)
                casterObject = gameObject;

            // 注册所有可视化器
            RegisterAllVisualizers();
        }

        void OnEnable()
        {
            // 订阅SkillPlayer事件
            if (targetSkillPlayer != null)
            {
                targetSkillPlayer.OnSkillStarted += OnSkillStarted;
                targetSkillPlayer.OnSkillFinished += OnSkillFinished;
                targetSkillPlayer.OnFrameChanged += OnFrameChanged;
                targetSkillPlayer.OnActionExecuted += OnActionExecuted;
            }
        }

        void OnDisable()
        {
            // 取消订阅
            if (targetSkillPlayer != null)
            {
                targetSkillPlayer.OnSkillStarted -= OnSkillStarted;
                targetSkillPlayer.OnSkillFinished -= OnSkillFinished;
                targetSkillPlayer.OnFrameChanged -= OnFrameChanged;
                targetSkillPlayer.OnActionExecuted -= OnActionExecuted;
            }
        }

        void Update()
        {
            // 更新所有活动的Action可视化
            UpdateActiveActions();
        }

        #region 注册可视化器

        /// <summary>
        /// 注册所有可视化器
        /// </summary>
        private void RegisterAllVisualizers()
        {
            // 注册核心可视化器
            RegisterVisualizer(new DamageVisualizer());
            RegisterVisualizer(new HealVisualizer());
            RegisterVisualizer(new BuffVisualizer());
            RegisterVisualizer(new ProjectileVisualizer());
            RegisterVisualizer(new AOEVisualizer());
            RegisterVisualizer(new MovementVisualizer());

            Debug.Log($"[SkillVisualizerManager] Registered {visualizers.Count} visualizers");
        }

        /// <summary>
        /// 注册单个可视化器
        /// </summary>
        public void RegisterVisualizer(ISkillVisualizer visualizer)
        {
            if (visualizer == null) return;

            var actionType = visualizer.SupportedActionType;
            if (visualizers.ContainsKey(actionType))
            {
                Debug.LogWarning($"[SkillVisualizerManager] Visualizer for {actionType.Name} already registered, replacing");
            }

            visualizers[actionType] = visualizer;
            Debug.Log($"[SkillVisualizerManager] Registered visualizer for {actionType.Name}");
        }

        /// <summary>
        /// 获取可视化器
        /// </summary>
        private ISkillVisualizer GetVisualizer(System.Type actionType)
        {
            visualizers.TryGetValue(actionType, out ISkillVisualizer visualizer);
            return visualizer;
        }

        #endregion

        #region SkillPlayer事件处理

        private void OnSkillStarted(SkillSystem.Data.SkillData skillData)
        {
            Debug.Log($"[SkillVisualizerManager] Skill started: {skillData.skillName}");
            activeActions.Clear();
        }

        private void OnSkillFinished(SkillSystem.Data.SkillData skillData)
        {
            Debug.Log($"[SkillVisualizerManager] Skill finished: {skillData.skillName}");

            // 清理所有活动Action的可视化
            foreach (var action in activeActions.Keys)
            {
                var visualizer = GetVisualizer(action.GetType());
                visualizer?.VisualizeExit(action, casterObject);
            }

            activeActions.Clear();
        }

        private void OnFrameChanged(int currentFrame)
        {
            // 帧变化时在UpdateActiveActions中处理
        }

        private void OnActionExecuted(ISkillAction action)
        {
            // Action执行时调用VisualizeEnter
            var visualizer = GetVisualizer(action.GetType());
            if (visualizer != null)
            {
                visualizer.VisualizeEnter(action, casterObject);
                activeActions[action] = 0; // 相对帧从0开始
                Debug.Log($"[SkillVisualizerManager] Visualizing action: {action.GetDisplayName()}");
            }
            else
            {
                Debug.LogWarning($"[SkillVisualizerManager] No visualizer found for action type: {action.GetType().Name}");
            }
        }

        #endregion

        #region Action生命周期管理

        private void UpdateActiveActions()
        {
            if (targetSkillPlayer == null || !targetSkillPlayer.IsPlaying)
                return;

            var currentActions = targetSkillPlayer.GetActiveActions();
            var currentFrame = targetSkillPlayer.CurrentFrame;

            // 检查新激活的Action
            foreach (var action in currentActions)
            {
                if (!activeActions.ContainsKey(action))
                {
                    // 新Action激活
                    var visualizer = GetVisualizer(action.GetType());
                    if (visualizer != null)
                    {
                        visualizer.VisualizeEnter(action, casterObject);
                        activeActions[action] = currentFrame - action.frame;
                    }
                }
                else
                {
                    // 已存在的Action - 更新Tick
                    int relativeFrame = currentFrame - action.frame;
                    activeActions[action] = relativeFrame;

                    var visualizer = GetVisualizer(action.GetType());
                    visualizer?.VisualizeTick(action, casterObject, relativeFrame);
                }
            }

            // 检查退出的Action
            var actionsToRemove = new List<ISkillAction>();
            foreach (var kvp in activeActions)
            {
                if (!currentActions.Contains(kvp.Key))
                {
                    // Action已退出
                    var visualizer = GetVisualizer(kvp.Key.GetType());
                    visualizer?.VisualizeExit(kvp.Key, casterObject);
                    actionsToRemove.Add(kvp.Key);
                }
            }

            // 移除已退出的Action
            foreach (var action in actionsToRemove)
            {
                activeActions.Remove(action);
            }
        }

        #endregion

        #region 公共接口

        /// <summary>
        /// 设置施法者对象
        /// </summary>
        public void SetCaster(GameObject caster)
        {
            casterObject = caster;
        }

        /// <summary>
        /// 设置目标SkillPlayer
        /// </summary>
        public void SetTargetSkillPlayer(SkillPlayer player)
        {
            // 先取消旧的订阅
            if (targetSkillPlayer != null)
            {
                targetSkillPlayer.OnSkillStarted -= OnSkillStarted;
                targetSkillPlayer.OnSkillFinished -= OnSkillFinished;
                targetSkillPlayer.OnFrameChanged -= OnFrameChanged;
                targetSkillPlayer.OnActionExecuted -= OnActionExecuted;
            }

            targetSkillPlayer = player;

            // 订阅新的事件
            if (targetSkillPlayer != null && enabled)
            {
                targetSkillPlayer.OnSkillStarted += OnSkillStarted;
                targetSkillPlayer.OnSkillFinished += OnSkillFinished;
                targetSkillPlayer.OnFrameChanged += OnFrameChanged;
                targetSkillPlayer.OnActionExecuted += OnActionExecuted;
            }
        }

        /// <summary>
        /// 从外部触发Action进入（用于编辑器预览）
        /// </summary>
        public void TriggerActionEnter(ISkillAction action)
        {
            if (action == null) return;

            var visualizer = GetVisualizer(action.GetType());
            if (visualizer != null)
            {
                visualizer.VisualizeEnter(action, casterObject);
                activeActions[action] = 0;
                Debug.Log($"[SkillVisualizerManager] [Editor Preview] Visualizing action enter: {action.GetDisplayName()}");
            }
            else
            {
                Debug.LogWarning($"[SkillVisualizerManager] No visualizer found for action type: {action.GetType().Name}");
            }
        }

        /// <summary>
        /// 从外部触发Action Tick（用于编辑器预览）
        /// </summary>
        public void TriggerActionTick(ISkillAction action, int relativeFrame)
        {
            if (action == null) return;

            if (activeActions.ContainsKey(action))
            {
                activeActions[action] = relativeFrame;
                var visualizer = GetVisualizer(action.GetType());
                visualizer?.VisualizeTick(action, casterObject, relativeFrame);
            }
        }

        /// <summary>
        /// 从外部触发Action退出（用于编辑器预览）
        /// </summary>
        public void TriggerActionExit(ISkillAction action)
        {
            if (action == null) return;

            if (activeActions.ContainsKey(action))
            {
                var visualizer = GetVisualizer(action.GetType());
                visualizer?.VisualizeExit(action, casterObject);
                activeActions.Remove(action);
                Debug.Log($"[SkillVisualizerManager] [Editor Preview] Visualizing action exit: {action.GetDisplayName()}");
            }
        }

        #endregion

        void OnDestroy()
        {
            // 清理所有可视化器
            foreach (var visualizer in visualizers.Values)
            {
                visualizer.Cleanup();
            }
        }
    }
}
