using UnityEngine;
using UnityEngine.UI;
using TMPro;
using TrainingGround.Entity;

namespace TrainingGround.UI
{
    /// <summary>
    /// Entity health bar rendered inside a screen-space canvas that follows a world-space target.
    /// </summary>
    public class EntityHealthBar : MonoBehaviour
    {
        [Header("Target")]
        [SerializeField] private IEntity targetEntity;
        [SerializeField] private Transform targetTransform;
        [SerializeField] private Vector3 offset = new Vector3(0f, 2.5f, 0f);

        [Header("UI References")]
        [SerializeField] private Canvas canvas;
        [SerializeField] private RectTransform healthBarRoot;
        [SerializeField] private Image healthBarFill;
        [SerializeField] private Image shieldBarFill;
        [SerializeField] private Image resourceBarFill;
        [SerializeField] private TextMeshProUGUI healthText;
        [SerializeField] private TextMeshProUGUI resourceText;
        [SerializeField] private TextMeshProUGUI entityNameText;

        [Header("Options")]
        [SerializeField] private bool showShieldBar = true;
        [SerializeField] private bool showResourceBar = false;
        [SerializeField] private float smoothSpeed = 10f;
        [SerializeField] private float positionSmoothSpeed = 15f;

        private UnityEngine.Camera mainCamera;
        private RectTransform canvasRectTransform;
        private GameObject shieldBarContainer;
        private GameObject resourceBarContainer;
        private float currentHealthPercentage;
        private float currentShieldPercentage;
        private float currentResourcePercentage;
        private bool ownsHealthBarRoot;

        private void Awake()
        {
            mainCamera = UnityEngine.Camera.main;
            EnsureCanvasReference();

            if (healthBarRoot == null && canvas != null)
            {
                CreateDefaultUI();
            }
            else if (healthBarRoot != null && canvas != null)
            {
                healthBarRoot.SetParent(canvas.transform, false);
                canvasRectTransform = canvas.transform as RectTransform;
            }

            ApplyVisibilitySettings();
        }

        private void Start()
        {
            if (targetEntity == null)
            {
                targetEntity = GetComponentInParent<IEntity>();
            }

            if (targetTransform == null && targetEntity != null)
            {
                targetTransform = targetEntity.Transform;
            }

            if (targetEntity != null && entityNameText != null)
            {
                entityNameText.text = targetEntity.EntityName;
            }

            ApplyVisibilitySettings();
            UpdateHealthBar();
        }

        private void LateUpdate()
        {
            if (targetTransform == null || healthBarRoot == null)
            {
                return;
            }

            Vector3 worldPosition = targetTransform.position + offset;
            transform.position = worldPosition;

            if (canvas != null && canvas.renderMode != RenderMode.WorldSpace)
            {
                UpdateScreenSpacePosition(worldPosition);
            }
            else
            {
                UpdateWorldSpacePosition(worldPosition);
            }

            UpdateHealthBar();
        }

        private void UpdateScreenSpacePosition(Vector3 worldPosition)
        {
            EnsureCanvasReference();
            if (canvas == null || healthBarRoot == null || canvasRectTransform == null)
            {
                return;
            }

            UnityEngine.Camera cameraForWorldPoint = mainCamera ?? canvas.worldCamera ?? UnityEngine.Camera.main;
            if (cameraForWorldPoint == null)
            {
                return;
            }

            Vector3 screenPoint = RectTransformUtility.WorldToScreenPoint(cameraForWorldPoint, worldPosition);
            UnityEngine.Camera cameraForCanvas = canvas.renderMode == RenderMode.ScreenSpaceOverlay
                ? null
                : canvas.worldCamera ?? cameraForWorldPoint;

            if (RectTransformUtility.ScreenPointToLocalPointInRectangle(canvasRectTransform, screenPoint, cameraForCanvas, out Vector2 localPoint))
            {
                // 平滑插值位置，避免抖动
                Vector2 currentPos = healthBarRoot.anchoredPosition;
                Vector2 smoothPos = Vector2.Lerp(currentPos, localPoint, Time.deltaTime * positionSmoothSpeed);
                healthBarRoot.anchoredPosition = smoothPos;
            }
        }

        private void UpdateWorldSpacePosition(Vector3 worldPosition)
        {
            if (healthBarRoot == null)
            {
                return;
            }

            // 平滑插值位置，避免抖动
            Vector3 currentPos = healthBarRoot.position;
            Vector3 smoothPos = Vector3.Lerp(currentPos, worldPosition, Time.deltaTime * positionSmoothSpeed);
            healthBarRoot.position = smoothPos;

            if (mainCamera == null)
            {
                mainCamera = UnityEngine.Camera.main;
            }

            if (mainCamera != null)
            {
                // 平滑旋转，避免突然转�?                Quaternion targetRotation = mainCamera.transform.rotation;
                healthBarRoot.rotation = Quaternion.Slerp(healthBarRoot.rotation, targetRotation, Time.deltaTime * positionSmoothSpeed);
            }
        }

        private void UpdateHealthBar()
        {
            if (targetEntity == null)
            {
                return;
            }

            float targetHealthPct = targetEntity.HealthPercentage;
            float targetShieldPct = targetEntity.MaxShield > 0f ? targetEntity.CurrentShield / targetEntity.MaxShield : 0f;
            float targetResourcePct = targetEntity.MaxResource > 0f ? targetEntity.CurrentResource / targetEntity.MaxResource : 0f;

            currentHealthPercentage = Mathf.Lerp(currentHealthPercentage, targetHealthPct, Time.deltaTime * smoothSpeed);
            currentShieldPercentage = Mathf.Lerp(currentShieldPercentage, targetShieldPct, Time.deltaTime * smoothSpeed);
            currentResourcePercentage = Mathf.Lerp(currentResourcePercentage, targetResourcePct, Time.deltaTime * smoothSpeed);

            if (healthBarFill != null)
            {
                healthBarFill.fillAmount = currentHealthPercentage;
            }

            if (shieldBarFill != null)
            {
                shieldBarFill.fillAmount = currentShieldPercentage;
                shieldBarFill.gameObject.SetActive(showShieldBar && currentShieldPercentage > 0.01f);
            }

            if (resourceBarFill != null && showResourceBar)
            {
                resourceBarFill.fillAmount = currentResourcePercentage;
            }

            if (healthText != null)
            {
                healthText.text = $"{targetEntity.CurrentHealth:F0} / {targetEntity.MaxHealth:F0}";
            }

            if (resourceText != null && showResourceBar)
            {
                resourceText.text = $"{targetEntity.CurrentResource:F0} / {targetEntity.MaxResource:F0}";
            }
        }

        private void EnsureCanvasReference()
        {
            if (canvas != null)
            {
                canvasRectTransform ??= canvas.transform as RectTransform;
                return;
            }

            Canvas[] canvases = FindObjectsOfType<Canvas>();
            foreach (var candidate in canvases)
            {
                if (!candidate.isActiveAndEnabled)
                {
                    continue;
                }

                if (candidate.renderMode == RenderMode.WorldSpace)
                {
                    continue;
                }

                canvas = candidate;
                canvasRectTransform = candidate.transform as RectTransform;
                return;
            }

            if (canvases.Length > 0)
            {
                canvas = canvases[0];
                canvasRectTransform = canvas.transform as RectTransform;
            }
        }

        private void CreateDefaultUI()
        {
            EnsureCanvasReference();
            if (canvas == null)
            {
                Debug.LogWarning("[EntityHealthBar] No canvas available for health bar UI.");
                return;
            }

            GameObject rootObject = new GameObject("EntityHealthBar_UI", typeof(RectTransform));
            healthBarRoot = rootObject.GetComponent<RectTransform>();
            healthBarRoot.SetParent(canvas.transform, false);
            healthBarRoot.anchorMin = new Vector2(0.5f, 0.5f);
            healthBarRoot.anchorMax = new Vector2(0.5f, 0.5f);
            healthBarRoot.pivot = new Vector2(0.5f, 0f);
            healthBarRoot.sizeDelta = new Vector2(160f, 45f);

            ownsHealthBarRoot = true;

            // 名字文本（在最顶部�?            GameObject nameObj = CreateUIElement("EntityName", healthBarRoot);
            entityNameText = nameObj.AddComponent<TextMeshProUGUI>();
            entityNameText.fontSize = 12f;
            entityNameText.alignment = TextAlignmentOptions.Center;
            entityNameText.color = Color.white;
            entityNameText.fontStyle = FontStyles.Bold;
            entityNameText.enableWordWrapping = false;
            entityNameText.overflowMode = TextOverflowModes.Ellipsis;
            SetupRectTransform(nameObj.GetComponent<RectTransform>(), new Vector2(0f, 1f), new Vector2(1f, 1.28f), Vector2.zero, Vector2.zero);

            // 血条背�?            GameObject healthBg = CreateUIElement("HealthBarBg", healthBarRoot);
            var healthBgRect = healthBg.GetComponent<RectTransform>();
            SetupRectTransform(healthBgRect, new Vector2(0f, 0.35f), new Vector2(1f, 0.95f), Vector2.zero, Vector2.zero);
            var healthBgImage = healthBg.AddComponent<Image>();
            healthBgImage.color = new Color(0.2f, 0.2f, 0.2f, 0.9f);

            // 血条填�?            GameObject healthFillObj = CreateUIElement("HealthBarFill", healthBg.transform);
            healthBarFill = healthFillObj.AddComponent<Image>();
            healthBarFill.color = new Color(0.2f, 0.8f, 0.2f, 1f);
            healthBarFill.type = Image.Type.Filled;
            healthBarFill.fillMethod = Image.FillMethod.Horizontal;
            healthBarFill.fillOrigin = (int)Image.OriginHorizontal.Left;
            healthBarFill.fillAmount = 1f;
            SetupRectTransform(healthFillObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            // 护盾条（叠加在血条上方）
            shieldBarContainer = CreateUIElement("ShieldBarContainer", healthBg.transform);
            SetupRectTransform(shieldBarContainer.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            GameObject shieldFillObj = CreateUIElement("ShieldBarFill", shieldBarContainer.transform);
            shieldBarFill = shieldFillObj.AddComponent<Image>();
            shieldBarFill.color = new Color(0.5f, 0.8f, 1f, 0.7f);
            shieldBarFill.type = Image.Type.Filled;
            shieldBarFill.fillMethod = Image.FillMethod.Horizontal;
            shieldBarFill.fillOrigin = (int)Image.OriginHorizontal.Left;
            shieldBarFill.fillAmount = 0f;
            SetupRectTransform(shieldFillObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            // 血量文字（覆盖在血条上�?            GameObject healthTextObj = CreateUIElement("HealthText", healthBg.transform);
            healthText = healthTextObj.AddComponent<TextMeshProUGUI>();
            healthText.fontSize = 11f;
            healthText.alignment = TextAlignmentOptions.Center;
            healthText.color = Color.white;
            healthText.fontStyle = FontStyles.Bold;
            healthText.enableWordWrapping = false;
            var healthTextOutline = healthTextObj.AddComponent<UnityEngine.UI.Outline>();
            healthTextOutline.effectColor = Color.black;
            healthTextOutline.effectDistance = new Vector2(1f, -1f);
            SetupRectTransform(healthTextObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            // 资源条背�?            resourceBarContainer = CreateUIElement("ResourceBar", healthBarRoot);
            var resourceBgRect = resourceBarContainer.GetComponent<RectTransform>();
            SetupRectTransform(resourceBgRect, new Vector2(0f, 0.05f), new Vector2(1f, 0.30f), Vector2.zero, Vector2.zero);
            var resourceBgImage = resourceBarContainer.AddComponent<Image>();
            resourceBgImage.color = new Color(0.15f, 0.15f, 0.2f, 0.9f);

            // 资源条填�?            GameObject resourceFillObj = CreateUIElement("ResourceBarFill", resourceBarContainer.transform);
            resourceBarFill = resourceFillObj.AddComponent<Image>();
            resourceBarFill.color = new Color(0.3f, 0.5f, 1f, 1f);
            resourceBarFill.type = Image.Type.Filled;
            resourceBarFill.fillMethod = Image.FillMethod.Horizontal;
            resourceBarFill.fillOrigin = (int)Image.OriginHorizontal.Left;
            resourceBarFill.fillAmount = 0f;
            SetupRectTransform(resourceFillObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            // 资源文字（覆盖在资源条上�?            GameObject resourceTextObj = CreateUIElement("ResourceText", resourceBarContainer.transform);
            resourceText = resourceTextObj.AddComponent<TextMeshProUGUI>();
            resourceText.fontSize = 9f;
            resourceText.alignment = TextAlignmentOptions.Center;
            resourceText.color = Color.white;
            resourceText.fontStyle = FontStyles.Bold;
            resourceText.enableWordWrapping = false;
            var resourceTextOutline = resourceTextObj.AddComponent<UnityEngine.UI.Outline>();
            resourceTextOutline.effectColor = Color.black;
            resourceTextOutline.effectDistance = new Vector2(1f, -1f);
            SetupRectTransform(resourceTextObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            ApplyVisibilitySettings();
        }

        private GameObject CreateUIElement(string name, Transform parent)
        {
            GameObject obj = new GameObject(name, typeof(RectTransform));
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

        private void ApplyVisibilitySettings()
        {
            if (shieldBarContainer != null)
            {
                shieldBarContainer.SetActive(showShieldBar);
            }

            if (shieldBarFill != null && shieldBarFill.gameObject.activeSelf != (showShieldBar && currentShieldPercentage > 0.01f))
            {
                shieldBarFill.gameObject.SetActive(showShieldBar && currentShieldPercentage > 0.01f);
            }

            if (resourceBarContainer != null)
            {
                resourceBarContainer.SetActive(showResourceBar);
            }

            if (resourceBarFill != null && resourceBarFill.gameObject.activeSelf != showResourceBar)
            {
                resourceBarFill.gameObject.SetActive(showResourceBar);
            }

            if (resourceText != null)
            {
                resourceText.gameObject.SetActive(showResourceBar);
            }
        }

        public void SetTargetEntity(IEntity entity)
        {
            targetEntity = entity;
            targetTransform = entity?.Transform;

            if (entityNameText != null && entity != null)
            {
                entityNameText.text = entity.EntityName;
            }
        }

        public void SetTargetCanvas(Canvas targetCanvas)
        {
            if (canvas == targetCanvas)
            {
                return;
            }

            canvas = targetCanvas;
            EnsureCanvasReference();

            if (canvas != null && healthBarRoot != null)
            {
                healthBarRoot.SetParent(canvas.transform, false);
            }
            else if (canvas != null && healthBarRoot == null)
            {
                CreateDefaultUI();
            }

            ApplyVisibilitySettings();
        }

        public void SetShowShieldBar(bool show)
        {
            showShieldBar = show;
            ApplyVisibilitySettings();
        }

        public void SetShowResourceBar(bool show)
        {
            showResourceBar = show;
            ApplyVisibilitySettings();
        }

        private void OnDestroy()
        {
            if (ownsHealthBarRoot && healthBarRoot != null)
            {
                Destroy(healthBarRoot.gameObject);
            }
        }
    }
}
