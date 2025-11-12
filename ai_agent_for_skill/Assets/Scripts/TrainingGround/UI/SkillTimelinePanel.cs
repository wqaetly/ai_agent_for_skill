using UnityEngine;
using UnityEngine.UI;
using TMPro;
using SkillSystem.Runtime;
using SkillSystem.Data;
using System.Collections.Generic;

namespace TrainingGround.UI
{
    /// <summary>
    /// 技能时间轴面板 - 显示技能播放进度和Action时间�?
    /// </summary>
    public class SkillTimelinePanel : MonoBehaviour
    {
        [Header("引用")]
        [SerializeField] private SkillPlayer targetSkillPlayer;

        [Header("UI元素")]
        [SerializeField] private Slider progressSlider;
        [SerializeField] private TextMeshProUGUI frameText;
        [SerializeField] private TextMeshProUGUI skillNameText;
        [SerializeField] private Transform actionMarkerContainer;

        [Header("设置")]
        [SerializeField] private bool autoHide = true;
        [SerializeField] private float hideDelay = 2f;

        private CanvasGroup canvasGroup;
        private List<GameObject> actionMarkers = new List<GameObject>();
        private float hideTimer = 0f;

        void Awake()
        {
            canvasGroup = GetComponent<CanvasGroup>();
            if (canvasGroup == null)
            {
                canvasGroup = gameObject.AddComponent<CanvasGroup>();
            }

            // 如果没有SkillPlayer，尝试查�?
            if (targetSkillPlayer == null)
            {
                targetSkillPlayer = FindObjectOfType<SkillPlayer>();
            }
        }

        void OnEnable()
        {
            if (targetSkillPlayer != null)
            {
                targetSkillPlayer.OnSkillStarted += OnSkillStarted;
                targetSkillPlayer.OnSkillFinished += OnSkillFinished;
                targetSkillPlayer.OnFrameChanged += OnFrameChanged;
            }
        }

        void OnDisable()
        {
            if (targetSkillPlayer != null)
            {
                targetSkillPlayer.OnSkillStarted -= OnSkillStarted;
                targetSkillPlayer.OnSkillFinished -= OnSkillFinished;
                targetSkillPlayer.OnFrameChanged -= OnFrameChanged;
            }
        }

        void Update()
        {
            // 更新进度�?
            UpdateProgressBar();

            // 自动隐藏逻辑
            if (autoHide && targetSkillPlayer != null && !targetSkillPlayer.IsPlaying)
            {
                hideTimer += Time.deltaTime;
                if (hideTimer >= hideDelay)
                {
                    canvasGroup.alpha = Mathf.Lerp(canvasGroup.alpha, 0f, Time.deltaTime * 5f);
                }
            }
            else
            {
                hideTimer = 0f;
                canvasGroup.alpha = Mathf.Lerp(canvasGroup.alpha, 1f, Time.deltaTime * 10f);
            }
        }

        private void OnSkillStarted(SkillData skillData)
        {
            // 显示面板
            gameObject.SetActive(true);
            canvasGroup.alpha = 1f;
            hideTimer = 0f;

            // 设置技能名�?
            if (skillNameText != null)
            {
                skillNameText.text = skillData.skillName;
            }

            // 初始化进度条
            if (progressSlider != null)
            {
                progressSlider.minValue = 0;
                progressSlider.maxValue = skillData.totalDuration;
                progressSlider.value = 0;
            }

            // 创建Action标记
            CreateActionMarkers(skillData);
        }

        private void OnSkillFinished(SkillData skillData)
        {
            // 清理Action标记
            ClearActionMarkers();

            // 重置进度�?
            if (progressSlider != null)
            {
                progressSlider.value = 0;
            }
        }

        private void OnFrameChanged(int currentFrame)
        {
            // 在UpdateProgressBar中处�?
        }

        private void UpdateProgressBar()
        {
            if (targetSkillPlayer == null || targetSkillPlayer.CurrentSkillData == null)
                return;

            int currentFrame = targetSkillPlayer.CurrentFrame;
            int totalFrames = targetSkillPlayer.CurrentSkillData.totalDuration;

            // 更新进度�?
            if (progressSlider != null)
            {
                progressSlider.value = currentFrame;
            }

            // 更新帧数文本
            if (frameText != null)
            {
                frameText.text = $"Frame: {currentFrame} / {totalFrames}";
            }
        }

        private void CreateActionMarkers(SkillData skillData)
        {
            ClearActionMarkers();

            if (actionMarkerContainer == null || progressSlider == null)
                return;

            // 遍历所有轨道的所有Action
            foreach (var track in skillData.tracks)
            {
                if (!track.enabled) continue;

                foreach (var action in track.actions)
                {
                    if (!action.enabled) continue;

                    // 创建标记
                    GameObject marker = CreateActionMarker(action, skillData.totalDuration);
                    actionMarkers.Add(marker);
                }
            }
        }

        private GameObject CreateActionMarker(SkillSystem.Actions.ISkillAction action, int totalFrames)
        {
            GameObject marker = new GameObject($"Marker_{action.GetDisplayName()}");
            marker.transform.SetParent(actionMarkerContainer, false);

            var rectTransform = marker.AddComponent<RectTransform>();

            // 计算位置（相对于进度条）
            float normalizedPosition = (float)action.frame / totalFrames;
            rectTransform.anchorMin = new Vector2(normalizedPosition, 0f);
            rectTransform.anchorMax = new Vector2(normalizedPosition, 1f);
            rectTransform.sizeDelta = new Vector2(2f, 0f); // 2像素宽的�?
            rectTransform.anchoredPosition = Vector2.zero;

            // 添加图片
            var image = marker.AddComponent<Image>();
            image.color = GetActionTypeColor(action.GetType().Name);

            // 添加Tooltip（可选）
            var tooltip = marker.AddComponent<ToolTip>();
            tooltip.tooltipText = $"{action.GetDisplayName()}\nFrame: {action.frame}";

            return marker;
        }

        private void ClearActionMarkers()
        {
            foreach (var marker in actionMarkers)
            {
                if (marker != null)
                {
                    Destroy(marker);
                }
            }
            actionMarkers.Clear();
        }

        private Color GetActionTypeColor(string actionTypeName)
        {
            // 根据Action类型返回不同颜色
            if (actionTypeName.Contains("Damage"))
                return Color.red;
            else if (actionTypeName.Contains("Heal"))
                return Color.green;
            else if (actionTypeName.Contains("Buff"))
                return Color.yellow;
            else if (actionTypeName.Contains("Projectile"))
                return new Color(1f, 0.5f, 0f); // 橙色
            else if (actionTypeName.Contains("AOE") || actionTypeName.Contains("AreaOfEffect"))
                return Color.magenta;
            else if (actionTypeName.Contains("Movement"))
                return Color.cyan;
            else
                return Color.white;
        }

        public void SetTargetSkillPlayer(SkillPlayer player)
        {
            // 取消旧订�?
            if (targetSkillPlayer != null)
            {
                targetSkillPlayer.OnSkillStarted -= OnSkillStarted;
                targetSkillPlayer.OnSkillFinished -= OnSkillFinished;
                targetSkillPlayer.OnFrameChanged -= OnFrameChanged;
            }

            targetSkillPlayer = player;

            // 订阅新事�?
            if (targetSkillPlayer != null && enabled)
            {
                targetSkillPlayer.OnSkillStarted += OnSkillStarted;
                targetSkillPlayer.OnSkillFinished += OnSkillFinished;
                targetSkillPlayer.OnFrameChanged += OnFrameChanged;
            }
        }
    }

    /// <summary>
    /// 简单的Tooltip组件
    /// </summary>
    public class ToolTip : MonoBehaviour, UnityEngine.EventSystems.IPointerEnterHandler, UnityEngine.EventSystems.IPointerExitHandler
    {
        public string tooltipText;
        private GameObject tooltipObject;

        public void OnPointerEnter(UnityEngine.EventSystems.PointerEventData eventData)
        {
            // 显示Tooltip（简化实现）
            Debug.Log($"[Tooltip] {tooltipText}");
        }

        public void OnPointerExit(UnityEngine.EventSystems.PointerEventData eventData)
        {
            // 隐藏Tooltip
        }
    }
}
