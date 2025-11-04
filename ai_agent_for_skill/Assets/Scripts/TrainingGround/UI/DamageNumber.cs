using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace TrainingGround.UI
{
    /// <summary>
    /// 伤害数字组件 - 单个飘字
    /// </summary>
    public class DamageNumber : MonoBehaviour
    {
        [SerializeField] private TextMeshProUGUI textMesh;
        [SerializeField] private float floatSpeed = 2f;
        [SerializeField] private float lifetime = 1.5f;
        [SerializeField] private float fadeOutTime = 0.5f;

        private float elapsedTime = 0f;
        private Vector3 startPosition;
        private Color startColor;

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
        }

        public void Initialize(Vector3 worldPosition, float value, Color color, bool isCritical = false, bool isHeal = false)
        {
            // 设置起始位置
            startPosition = worldPosition;
            transform.position = worldPosition;

            // 设置文本
            string prefix = isHeal ? "+" : "-";
            textMesh.text = $"{prefix}{value:F0}";

            // 设置颜色
            startColor = color;
            textMesh.color = color;

            // 暴击或治疗时放大
            if (isCritical)
            {
                textMesh.fontSize = 48;
                textMesh.fontStyle = FontStyles.Bold;
            }
            else if (isHeal)
            {
                textMesh.fontSize = 42;
                textMesh.fontStyle = FontStyles.Bold;
            }
            else
            {
                textMesh.fontSize = 36;
                textMesh.fontStyle = FontStyles.Normal;
            }

            elapsedTime = 0f;
        }

        void Update()
        {
            elapsedTime += Time.deltaTime;

            // 向上飘动
            transform.position = startPosition + Vector3.up * (floatSpeed * elapsedTime);

            // 淡出效果
            if (elapsedTime >= lifetime - fadeOutTime)
            {
                float fadeT = (elapsedTime - (lifetime - fadeOutTime)) / fadeOutTime;
                Color color = startColor;
                color.a = Mathf.Lerp(1f, 0f, fadeT);
                textMesh.color = color;
            }

            // 生命周期结束
            if (elapsedTime >= lifetime)
            {
                ReturnToPool();
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
            transform.localScale = Vector3.one;
            gameObject.SetActive(true);
        }
    }
}
