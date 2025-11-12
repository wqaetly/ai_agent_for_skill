using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace TrainingGround.UI
{
    /// <summary>
    /// 伤害数字组件 - 单个飘字（商业级动画效果�?
    /// </summary>
    public class DamageNumber : MonoBehaviour
    {
        [Header("组件引用")]
        [SerializeField] private TextMeshProUGUI textMesh;

        [Header("动画设置")]
        [SerializeField] private float floatSpeed = 2f;
        [SerializeField] private float lifetime = 1.5f;
        [SerializeField] private float fadeOutTime = 0.5f;
        [SerializeField] private AnimationCurve popCurve = AnimationCurve.EaseInOut(0f, 0f, 0.2f, 1f);
        [SerializeField] private AnimationCurve moveCurve = AnimationCurve.Linear(0f, 0f, 1f, 1f);

        [Header("视觉增强")]
        [SerializeField] private bool enableOutline = true;
        [SerializeField] private bool enableScaleAnimation = true;
        [SerializeField] private bool enableRandomOffset = true;
        [SerializeField] private float maxRandomOffset = 0.5f;

        private float elapsedTime = 0f;
        private Vector3 startPosition;
        private Vector3 randomOffset;
        private Color startColor;
        private float startScale = 1f;
        private Vector3 baseScale = Vector3.one;

        void Awake()
        {
            if (textMesh == null)
            {
                textMesh = GetComponentInChildren<TextMeshProUGUI>();
            }

            if (textMesh == null)
            {
                Debug.LogError("[DamageNumber] TextMeshProUGUI component not found!");
            }

            baseScale = transform.localScale;
        }

        public void Initialize(Vector3 worldPosition, float value, Color color, bool isCritical = false, bool isHeal = false)
        {
            // 设置起始位置
            startPosition = worldPosition;

            // 随机偏移（避免重叠）
            if (enableRandomOffset)
            {
                randomOffset = new Vector3(
                    Random.Range(-maxRandomOffset, maxRandomOffset),
                    0f,
                    Random.Range(-maxRandomOffset, maxRandomOffset)
                );
                startPosition += randomOffset;
            }

            // 使用RectTransform设置位置（适用于WorldSpace Canvas�?
            var rectTransform = GetComponent<RectTransform>();
            if (rectTransform != null)
            {
                rectTransform.position = startPosition;
            }
            else
            {
                transform.position = startPosition;
            }

            // 设置文本
            string prefix = isHeal ? "+" : "-";
            textMesh.text = $"{prefix}{value:F0}";

            // 设置颜色
            startColor = color;
            textMesh.color = color;

            // 配置视觉样式
            if (isCritical)
            {
                // 暴击：大号、粗体、描�?
                textMesh.fontSize = 52;
                textMesh.fontStyle = FontStyles.Bold;
                startScale = 1.3f;

                if (enableOutline)
                {
                    textMesh.outlineWidth = 0.3f;
                    textMesh.outlineColor = new Color(0f, 0f, 0f, 0.8f);
                }
            }
            else if (isHeal)
            {
                // 治疗：中号、粗体、轻微描�?
                textMesh.fontSize = 44;
                textMesh.fontStyle = FontStyles.Bold;
                startScale = 1.1f;

                if (enableOutline)
                {
                    textMesh.outlineWidth = 0.2f;
                    textMesh.outlineColor = new Color(0f, 0f, 0f, 0.6f);
                }
            }
            else
            {
                // 普通伤害：标准大小
                textMesh.fontSize = 38;
                textMesh.fontStyle = FontStyles.Normal;
                startScale = 1f;

                if (enableOutline)
                {
                    textMesh.outlineWidth = 0.2f;
                    textMesh.outlineColor = new Color(0f, 0f, 0f, 0.5f);
                }
            }

            // 初始缩放�?（弹出动画）
            if (enableScaleAnimation)
            {
                transform.localScale = Vector3.zero;
            }
            else
            {
                transform.localScale = baseScale * startScale;
            }

            elapsedTime = 0f;
        }

        void Update()
        {
            elapsedTime += Time.deltaTime;
            float normalizedTime = elapsedTime / lifetime;

            // 弹出动画（前20%时间�?
            if (enableScaleAnimation && normalizedTime < 0.2f)
            {
                float popT = normalizedTime / 0.2f;
                float scale = popCurve.Evaluate(popT) * startScale;
                transform.localScale = baseScale * scale;
            }
            else if (enableScaleAnimation && transform.localScale.x < baseScale.x * startScale)
            {
                transform.localScale = baseScale * startScale;
            }

            // 向上飘动（使用曲线）
            float moveT = moveCurve.Evaluate(normalizedTime);
            float currentHeight = floatSpeed * moveT * lifetime;
            Vector3 currentPosition = startPosition + Vector3.up * currentHeight;

            // 使用RectTransform更新位置
            var rectTransform = GetComponent<RectTransform>();
            if (rectTransform != null)
            {
                rectTransform.position = currentPosition;
            }
            else
            {
                transform.position = currentPosition;
            }

            // 淡出效果（后30%时间�?
            if (elapsedTime >= lifetime - fadeOutTime)
            {
                float fadeT = (elapsedTime - (lifetime - fadeOutTime)) / fadeOutTime;

                // Alpha淡出
                Color color = startColor;
                color.a = Mathf.Lerp(1f, 0f, fadeT);
                textMesh.color = color;

                // 轻微缩小
                if (enableScaleAnimation)
                {
                    float shrinkScale = Mathf.Lerp(startScale, startScale * 0.8f, fadeT);
                    transform.localScale = baseScale * shrinkScale;
                }
            }

            // 生命周期结束
            if (elapsedTime >= lifetime)
            {
                ReturnToPool();
            }

            // 始终面向相机
            if (UnityEngine.Camera.main != null)
            {
                transform.rotation = UnityEngine.Camera.main.transform.rotation;
            }
        }

        private void ReturnToPool()
        {
            // 回收到对象池
            var pool = FindObjectOfType<DamageNumberPool>();
            if (pool != null)
            {
                pool.ReturnToPool(this);
            }
            else
            {
                Destroy(gameObject);
            }
        }

        public void ResetState()
        {
            elapsedTime = 0f;
            transform.localScale = baseScale;
            gameObject.SetActive(true);
        }
    }
}
