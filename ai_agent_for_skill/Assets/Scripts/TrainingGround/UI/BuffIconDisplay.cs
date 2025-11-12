using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections.Generic;
using TrainingGround.Entity;

namespace TrainingGround.UI
{
    /// <summary>
    /// Buff图标显示 - 显示实体的所有Buff状�?
    /// </summary>
    public class BuffIconDisplay : MonoBehaviour
    {
        [Header("引用")]
        [SerializeField] private IEntity targetEntity;
        [SerializeField] private Transform iconContainer;

        [Header("设置")]
        [SerializeField] private GameObject buffIconPrefab;
        [SerializeField] private int maxVisibleBuffs = 10;
        [SerializeField] private float iconSize = 40f;
        [SerializeField] private float iconSpacing = 5f;

        private Dictionary<string, BuffIcon> activeIcons = new Dictionary<string, BuffIcon>();
        private Queue<BuffIcon> iconPool = new Queue<BuffIcon>();

        void Awake()
        {
            // 如果没有容器，创建一�?
            if (iconContainer == null)
            {
                GameObject containerObj = new GameObject("IconContainer");
                containerObj.transform.SetParent(transform, false);
                iconContainer = containerObj.transform;

                // 添加HorizontalLayoutGroup
                var layoutGroup = containerObj.AddComponent<HorizontalLayoutGroup>();
                layoutGroup.spacing = iconSpacing;
                layoutGroup.childAlignment = TextAnchor.MiddleLeft;
                layoutGroup.childControlWidth = false;
                layoutGroup.childControlHeight = false;
                layoutGroup.childForceExpandWidth = false;
                layoutGroup.childForceExpandHeight = false;
            }

            // 如果没有预制体，创建默认预制�?
            if (buffIconPrefab == null)
            {
                buffIconPrefab = CreateDefaultBuffIconPrefab();
            }
        }

        void Start()
        {
            // 尝试自动获取目标实体
            if (targetEntity == null)
            {
                targetEntity = GetComponentInParent<IEntity>();
            }
        }

        void Update()
        {
            if (targetEntity == null) return;

            // 更新Buff显示
            UpdateBuffIcons();
        }

        private void UpdateBuffIcons()
        {
            var activeBuffs = targetEntity.GetActiveBuffs();

            // 移除已过期的Buff图标
            var iconsToRemove = new List<string>();
            foreach (var kvp in activeIcons)
            {
                bool stillActive = activeBuffs.Exists(b => b.buffId == kvp.Key);
                if (!stillActive)
                {
                    iconsToRemove.Add(kvp.Key);
                }
            }

            foreach (var buffId in iconsToRemove)
            {
                RemoveBuffIcon(buffId);
            }

            // 添加或更新Buff图标
            foreach (var buff in activeBuffs)
            {
                if (activeIcons.ContainsKey(buff.buffId))
                {
                    // 更新现有图标
                    activeIcons[buff.buffId].UpdateBuff(buff);
                }
                else
                {
                    // 创建新图�?
                    if (activeIcons.Count < maxVisibleBuffs)
                    {
                        CreateBuffIcon(buff);
                    }
                }
            }
        }

        private void CreateBuffIcon(BuffData buff)
        {
            BuffIcon icon = GetIconFromPool();
            if (icon != null)
            {
                icon.Initialize(buff);
                icon.transform.SetParent(iconContainer, false);
                icon.gameObject.SetActive(true);
                activeIcons[buff.buffId] = icon;
            }
        }

        private void RemoveBuffIcon(string buffId)
        {
            if (activeIcons.TryGetValue(buffId, out BuffIcon icon))
            {
                activeIcons.Remove(buffId);
                ReturnIconToPool(icon);
            }
        }

        private BuffIcon GetIconFromPool()
        {
            BuffIcon icon;
            if (iconPool.Count > 0)
            {
                icon = iconPool.Dequeue();
            }
            else
            {
                GameObject obj = Instantiate(buffIconPrefab, iconContainer);
                icon = obj.GetComponent<BuffIcon>();
                if (icon == null)
                {
                    icon = obj.AddComponent<BuffIcon>();
                }
            }
            return icon;
        }

        private void ReturnIconToPool(BuffIcon icon)
        {
            icon.gameObject.SetActive(false);
            icon.transform.SetParent(transform, false);
            iconPool.Enqueue(icon);
        }

        private GameObject CreateDefaultBuffIconPrefab()
        {
            GameObject prefab = new GameObject("BuffIcon_Default");
            prefab.transform.SetParent(transform, false);

            var rectTransform = prefab.AddComponent<RectTransform>();
            rectTransform.sizeDelta = new Vector2(iconSize, iconSize);

            // 背景图片
            var bgImage = prefab.AddComponent<Image>();
            bgImage.color = new Color(0.2f, 0.2f, 0.2f, 0.8f);

            // 堆叠数文�?
            GameObject stackTextObj = new GameObject("StackText");
            stackTextObj.transform.SetParent(prefab.transform, false);
            var stackRect = stackTextObj.AddComponent<RectTransform>();
            stackRect.anchorMin = new Vector2(0.6f, 0f);
            stackRect.anchorMax = new Vector2(1f, 0.4f);
            stackRect.offsetMin = Vector2.zero;
            stackRect.offsetMax = Vector2.zero;

            var stackText = stackTextObj.AddComponent<TextMeshProUGUI>();
            stackText.fontSize = 14;
            stackText.alignment = TextAlignmentOptions.BottomRight;
            stackText.color = Color.white;
            stackText.fontStyle = FontStyles.Bold;

            // 倒计时文�?
            GameObject timerTextObj = new GameObject("TimerText");
            timerTextObj.transform.SetParent(prefab.transform, false);
            var timerRect = timerTextObj.AddComponent<RectTransform>();
            timerRect.anchorMin = Vector2.zero;
            timerRect.anchorMax = Vector2.one;
            timerRect.offsetMin = Vector2.zero;
            timerRect.offsetMax = Vector2.zero;

            var timerText = timerTextObj.AddComponent<TextMeshProUGUI>();
            timerText.fontSize = 16;
            timerText.alignment = TextAlignmentOptions.Center;
            timerText.color = Color.white;

            prefab.SetActive(false);
            return prefab;
        }

        public void SetTargetEntity(IEntity entity)
        {
            targetEntity = entity;
        }
    }

    /// <summary>
    /// 单个Buff图标组件
    /// </summary>
    public class BuffIcon : MonoBehaviour
    {
        private Image backgroundImage;
        private TextMeshProUGUI stackText;
        private TextMeshProUGUI timerText;
        private BuffData currentBuff;

        void Awake()
        {
            backgroundImage = GetComponent<Image>();
            stackText = transform.Find("StackText")?.GetComponent<TextMeshProUGUI>();
            timerText = transform.Find("TimerText")?.GetComponent<TextMeshProUGUI>();
        }

        public void Initialize(BuffData buff)
        {
            currentBuff = buff;
            UpdateBuff(buff);
        }

        public void UpdateBuff(BuffData buff)
        {
            currentBuff = buff;

            // 更新颜色（根据Buff类型�?
            if (backgroundImage != null)
            {
                backgroundImage.color = GetBuffTypeColor(buff.buffType);
            }

            // 更新堆叠�?
            if (stackText != null)
            {
                stackText.text = buff.stackCount > 1 ? buff.stackCount.ToString() : "";
            }

            // 更新倒计�?
            if (timerText != null)
            {
                timerText.text = buff.remainingTime > 0 ? buff.remainingTime.ToString("F0") : "";
            }
        }

        private Color GetBuffTypeColor(BuffType buffType)
        {
            switch (buffType)
            {
                case BuffType.Positive:
                    return new Color(0f, 0.6f, 0f, 0.8f); // 绿色
                case BuffType.Negative:
                    return new Color(0.6f, 0f, 0f, 0.8f); // 红色
                case BuffType.Neutral:
                    return new Color(0.5f, 0.5f, 0.5f, 0.8f); // 灰色
                default:
                    return new Color(0.2f, 0.2f, 0.2f, 0.8f);
            }
        }

        void Update()
        {
            if (currentBuff != null)
            {
                UpdateBuff(currentBuff);
            }
        }
    }
}
