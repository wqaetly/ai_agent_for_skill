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
        [SerializeField] private TextMeshProUGUI entityNameText;

        [Header("Options")]
        [SerializeField] private bool showShieldBar = true;
        [SerializeField] private bool showResourceBar = false;
        [SerializeField] private float smoothSpeed = 10f;

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
                healthBarRoot.anchoredPosition = localPoint;
            }
        }

        private void UpdateWorldSpacePosition(Vector3 worldPosition)
        {
            if (healthBarRoot == null)
            {
                return;
            }

            healthBarRoot.position = worldPosition;

            if (mainCamera == null)
            {
                mainCamera = UnityEngine.Camera.main;
            }

            if (mainCamera != null)
            {
                healthBarRoot.rotation = mainCamera.transform.rotation;
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
            healthBarRoot.sizeDelta = new Vector2(220f, 90f);

            ownsHealthBarRoot = true;

            GameObject background = CreateUIElement("Background", healthBarRoot);
            var backgroundRect = background.GetComponent<RectTransform>();
            SetupRectTransform(backgroundRect, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            var backgroundImage = background.AddComponent<Image>();
            backgroundImage.color = new Color(0.1f, 0.1f, 0.1f, 0.7f);

            GameObject healthBg = CreateUIElement("HealthBarBg", healthBarRoot);
            var healthBgRect = healthBg.GetComponent<RectTransform>();
            SetupRectTransform(healthBgRect, new Vector2(0.08f, 0.55f), new Vector2(0.92f, 0.82f), Vector2.zero, Vector2.zero);
            var healthBgImage = healthBg.AddComponent<Image>();
            healthBgImage.color = new Color(0.3f, 0f, 0f, 0.8f);

            GameObject healthFillObj = CreateUIElement("HealthBarFill", healthBg.transform);
            healthBarFill = healthFillObj.AddComponent<Image>();
            healthBarFill.color = Color.green;
            healthBarFill.type = Image.Type.Filled;
            healthBarFill.fillMethod = Image.FillMethod.Horizontal;
            healthBarFill.fillOrigin = (int)Image.OriginHorizontal.Left;
            healthBarFill.fillAmount = 1f;
            SetupRectTransform(healthFillObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            shieldBarContainer = CreateUIElement("ShieldBar", healthBarRoot);
            var shieldBgRect = shieldBarContainer.GetComponent<RectTransform>();
            SetupRectTransform(shieldBgRect, new Vector2(0.08f, 0.35f), new Vector2(0.92f, 0.52f), Vector2.zero, Vector2.zero);
            var shieldBgImage = shieldBarContainer.AddComponent<Image>();
            shieldBgImage.color = new Color(0f, 0.25f, 0.35f, 0.8f);

            GameObject shieldFillObj = CreateUIElement("ShieldBarFill", shieldBarContainer.transform);
            shieldBarFill = shieldFillObj.AddComponent<Image>();
            shieldBarFill.color = Color.cyan;
            shieldBarFill.type = Image.Type.Filled;
            shieldBarFill.fillMethod = Image.FillMethod.Horizontal;
            shieldBarFill.fillOrigin = (int)Image.OriginHorizontal.Left;
            shieldBarFill.fillAmount = 0f;
            SetupRectTransform(shieldFillObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            resourceBarContainer = CreateUIElement("ResourceBar", healthBarRoot);
            var resourceBgRect = resourceBarContainer.GetComponent<RectTransform>();
            SetupRectTransform(resourceBgRect, new Vector2(0.08f, 0.15f), new Vector2(0.92f, 0.32f), Vector2.zero, Vector2.zero);
            var resourceBgImage = resourceBarContainer.AddComponent<Image>();
            resourceBgImage.color = new Color(0f, 0f, 0.3f, 0.75f);

            GameObject resourceFillObj = CreateUIElement("ResourceBarFill", resourceBarContainer.transform);
            resourceBarFill = resourceFillObj.AddComponent<Image>();
            resourceBarFill.color = new Color(0.25f, 0.4f, 1f, 1f);
            resourceBarFill.type = Image.Type.Filled;
            resourceBarFill.fillMethod = Image.FillMethod.Horizontal;
            resourceBarFill.fillOrigin = (int)Image.OriginHorizontal.Left;
            resourceBarFill.fillAmount = 0f;
            SetupRectTransform(resourceFillObj.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            GameObject healthTextObj = CreateUIElement("HealthText", healthBarRoot);
            healthText = healthTextObj.AddComponent<TextMeshProUGUI>();
            healthText.fontSize = 20f;
            healthText.alignment = TextAlignmentOptions.Center;
            healthText.color = Color.white;
            SetupRectTransform(healthTextObj.GetComponent<RectTransform>(), new Vector2(0f, 0.82f), new Vector2(1f, 1f), Vector2.zero, Vector2.zero);

            GameObject nameObj = CreateUIElement("EntityName", healthBarRoot);
            entityNameText = nameObj.AddComponent<TextMeshProUGUI>();
            entityNameText.fontSize = 22f;
            entityNameText.alignment = TextAlignmentOptions.Center;
            entityNameText.color = Color.white;
            entityNameText.fontStyle = FontStyles.Bold;
            SetupRectTransform(nameObj.GetComponent<RectTransform>(), new Vector2(0f, 1.05f), new Vector2(1f, 1.35f), Vector2.zero, Vector2.zero);

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
