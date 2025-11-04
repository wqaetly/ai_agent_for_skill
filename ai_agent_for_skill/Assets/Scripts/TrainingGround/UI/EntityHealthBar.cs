using UnityEngine;
using UnityEngine.UI;
using TMPro;
using TrainingGround.Entity;

namespace TrainingGround.UI
{
    /// <summary>
    /// 实体血条 - 显示实体的生命值、护盾和资源
    /// </summary>
    public class EntityHealthBar : MonoBehaviour
    {
        [Header("引用")]
        [SerializeField] private IEntity targetEntity;
        [SerializeField] private Transform targetTransform;
        [SerializeField] private Vector3 offset = new Vector3(0, 2.5f, 0);

        [Header("UI元素")]
        [SerializeField] private Canvas canvas;
        [SerializeField] private Image healthBarFill;
        [SerializeField] private Image shieldBarFill;
        [SerializeField] private Image resourceBarFill;
        [SerializeField] private TextMeshProUGUI healthText;
        [SerializeField] private TextMeshProUGUI entityNameText;

        [Header("设置")]
        [SerializeField] private bool showShieldBar = true;
        [SerializeField] private bool showResourceBar = false;
        [SerializeField] private bool alwaysFaceCamera = true;
        [SerializeField] private float smoothSpeed = 10f;

        private Camera mainCamera;
        private float currentHealthPercentage;
        private float currentShieldPercentage;
        private float currentResourcePercentage;

        void Awake()
        {
            mainCamera = Camera.main;

            // 如果没有Canvas，创建默认UI
            if (canvas == null)
            {
                CreateDefaultUI();
            }
        }

        void Start()
        {
            // 尝试自动获取目标实体
            if (targetEntity == null)
            {
                targetEntity = GetComponentInParent<IEntity>();
            }

            if (targetTransform == null && targetEntity != null)
            {
                targetTransform = targetEntity.Transform;
            }

            // 设置实体名称
            if (targetEntity != null && entityNameText != null)
            {
                entityNameText.text = targetEntity.EntityName;
            }
        }

        void LateUpdate()
        {
            if (targetTransform == null) return;

            // 跟随目标
            transform.position = targetTransform.position + offset;

            // 面向摄像机
            if (alwaysFaceCamera && mainCamera != null)
            {
                transform.rotation = Quaternion.LookRotation(transform.position - mainCamera.transform.position);
            }

            // 更新血条
            UpdateHealthBar();
        }

        private void UpdateHealthBar()
        {
            if (targetEntity == null) return;

            // 获取当前值
            float targetHealthPct = targetEntity.HealthPercentage;
            float targetShieldPct = targetEntity.MaxShield > 0 ? targetEntity.CurrentShield / targetEntity.MaxShield : 0f;
            float targetResourcePct = targetEntity.MaxResource > 0 ? targetEntity.CurrentResource / targetEntity.MaxResource : 0f;

            // 平滑过渡
            currentHealthPercentage = Mathf.Lerp(currentHealthPercentage, targetHealthPct, Time.deltaTime * smoothSpeed);
            currentShieldPercentage = Mathf.Lerp(currentShieldPercentage, targetShieldPct, Time.deltaTime * smoothSpeed);
            currentResourcePercentage = Mathf.Lerp(currentResourcePercentage, targetResourcePct, Time.deltaTime * smoothSpeed);

            // 更新UI
            if (healthBarFill != null)
            {
                healthBarFill.fillAmount = currentHealthPercentage;
            }

            if (shieldBarFill != null && showShieldBar)
            {
                shieldBarFill.fillAmount = currentShieldPercentage;
                shieldBarFill.gameObject.SetActive(currentShieldPercentage > 0.01f);
            }

            if (resourceBarFill != null && showResourceBar)
            {
                resourceBarFill.fillAmount = currentResourcePercentage;
            }

            // 更新文本
            if (healthText != null)
            {
                healthText.text = $"{targetEntity.CurrentHealth:F0} / {targetEntity.MaxHealth:F0}";
            }
        }

        /// <summary>
        /// 创建默认UI
        /// </summary>
        private void CreateDefaultUI()
        {
            // 创建Canvas
            GameObject canvasObj = new GameObject("HealthBarCanvas");
            canvasObj.transform.SetParent(transform, false);
            canvas = canvasObj.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.WorldSpace;

            var rectTransform = canvasObj.GetComponent<RectTransform>();
            rectTransform.sizeDelta = new Vector2(200, 80);
            rectTransform.localScale = Vector3.one * 0.01f;

            // 添加CanvasScaler
            var scaler = canvasObj.AddComponent<UnityEngine.UI.CanvasScaler>();
            scaler.dynamicPixelsPerUnit = 10;

            // 创建背景
            GameObject bgObj = CreateUIElement("Background", canvasObj.transform);
            var bgImage = bgObj.AddComponent<Image>();
            bgImage.color = new Color(0.1f, 0.1f, 0.1f, 0.8f);
            SetupRectTransform(bgObj.GetComponent<RectTransform>(), new Vector2(0, 0.5f), new Vector2(1, 1f), new Vector2(0, -40), new Vector2(0, 0));

            // 创建生命值条背景
            GameObject healthBgObj = CreateUIElement("HealthBarBg", canvasObj.transform);
            var healthBgImage = healthBgObj.AddComponent<Image>();
            healthBgImage.color = new Color(0.3f, 0f, 0f, 0.8f);
            SetupRectTransform(healthBgObj.GetComponent<RectTransform>(), new Vector2(0.05f, 0.6f), new Vector2(0.95f, 0.85f), Vector2.zero, Vector2.zero);

            // 创建生命值条填充
            GameObject healthFillObj = CreateUIElement("HealthBarFill", healthBgObj.transform);
            healthBarFill = healthFillObj.AddComponent<Image>();
            healthBarFill.color = Color.green;
            healthBarFill.type = Image.Type.Filled;
            healthBarFill.fillMethod = Image.FillMethod.Horizontal;
            healthBarFill.fillAmount = 1f;
            SetupRectTransform(healthFillObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            // 创建护盾条
            GameObject shieldBgObj = CreateUIElement("ShieldBarBg", canvasObj.transform);
            var shieldBgImage = shieldBgObj.AddComponent<Image>();
            shieldBgImage.color = new Color(0f, 0.2f, 0.3f, 0.8f);
            SetupRectTransform(shieldBgObj.GetComponent<RectTransform>(), new Vector2(0.05f, 0.4f), new Vector2(0.95f, 0.55f), Vector2.zero, Vector2.zero);

            GameObject shieldFillObj = CreateUIElement("ShieldBarFill", shieldBgObj.transform);
            shieldBarFill = shieldFillObj.AddComponent<Image>();
            shieldBarFill.color = Color.cyan;
            shieldBarFill.type = Image.Type.Filled;
            shieldBarFill.fillMethod = Image.FillMethod.Horizontal;
            shieldBarFill.fillAmount = 0f;
            SetupRectTransform(shieldFillObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            // 创建文本
            GameObject textObj = CreateUIElement("HealthText", canvasObj.transform);
            healthText = textObj.AddComponent<TextMeshProUGUI>();
            healthText.fontSize = 18;
            healthText.alignment = TextAlignmentOptions.Center;
            healthText.color = Color.white;
            SetupRectTransform(textObj.GetComponent<RectTransform>(), new Vector2(0, 0.1f), new Vector2(1, 0.35f), Vector2.zero, Vector2.zero);

            // 创建名称文本
            GameObject nameObj = CreateUIElement("EntityName", bgObj.transform);
            entityNameText = nameObj.AddComponent<TextMeshProUGUI>();
            entityNameText.fontSize = 20;
            entityNameText.alignment = TextAlignmentOptions.Center;
            entityNameText.color = Color.white;
            entityNameText.fontStyle = FontStyles.Bold;
            SetupRectTransform(nameObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
        }

        private GameObject CreateUIElement(string name, Transform parent)
        {
            GameObject obj = new GameObject(name);
            obj.transform.SetParent(parent, false);
            return obj;
        }

        private void SetupRectTransform(RectTransform rect, Vector2 anchorMin, Vector2 anchorMax, Vector2 offsetMin, Vector2 offsetMax)
        {
            rect.anchorMin = anchorMin;
            rect.anchorMax = anchorMax;
            rect.offsetMin = offsetMin;
            rect.offsetMax = offsetMax;
        }

        /// <summary>
        /// 设置目标实体
        /// </summary>
        public void SetTargetEntity(IEntity entity)
        {
            targetEntity = entity;
            targetTransform = entity?.Transform;

            if (entityNameText != null && entity != null)
            {
                entityNameText.text = entity.EntityName;
            }
        }

        /// <summary>
        /// 设置是否显示护盾条
        /// </summary>
        public void SetShowShieldBar(bool show)
        {
            showShieldBar = show;
        }

        /// <summary>
        /// 设置是否显示资源条
        /// </summary>
        public void SetShowResourceBar(bool show)
        {
            showResourceBar = show;
        }
    }
}
