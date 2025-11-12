using UnityEngine;
using System.Collections.Generic;
using TMPro;

namespace TrainingGround.UI
{
    /// <summary>
    /// 伤害数字对象�?- 管理伤害飘字的创建和回收
    /// </summary>
    public class DamageNumberPool : MonoBehaviour
    {
        [Header("预制体设�?)]
        [SerializeField] private GameObject damageNumberPrefab;
        [SerializeField] private Transform poolContainer;

        [Header("对象池设�?)]
        [SerializeField] private int initialPoolSize = 20;
        [SerializeField] private int maxPoolSize = 100;

        private Queue<DamageNumber> availableNumbers = new Queue<DamageNumber>();
        private List<DamageNumber> activeNumbers = new List<DamageNumber>();

        void Awake()
        {
            // 如果没有指定容器，创建一�?
            if (poolContainer == null)
            {
                poolContainer = new GameObject("DamageNumberPool").transform;
                poolContainer.SetParent(transform);
            }

            // 如果没有预制体，创建默认预制�?
            if (damageNumberPrefab == null)
            {
                damageNumberPrefab = CreateDefaultPrefab();
            }

            // 预创建对象池
            for (int i = 0; i < initialPoolSize; i++)
            {
                CreateNewDamageNumber();
            }
        }

        /// <summary>
        /// 显示伤害数字
        /// </summary>
        public void ShowDamageNumber(Vector3 worldPosition, float damage, Color color, bool isCritical = false)
        {
            var damageNumber = GetFromPool();
            if (damageNumber != null)
            {
                damageNumber.Initialize(worldPosition, damage, color, isCritical, false);
                activeNumbers.Add(damageNumber);
            }
        }

        /// <summary>
        /// 显示治疗数字
        /// </summary>
        public void ShowHealNumber(Vector3 worldPosition, float healAmount, Color color)
        {
            var damageNumber = GetFromPool();
            if (damageNumber != null)
            {
                damageNumber.Initialize(worldPosition, healAmount, color, false, true);
                activeNumbers.Add(damageNumber);
            }
        }

        /// <summary>
        /// 从对象池获取
        /// </summary>
        private DamageNumber GetFromPool()
        {
            DamageNumber damageNumber = null;

            if (availableNumbers.Count > 0)
            {
                damageNumber = availableNumbers.Dequeue();
                damageNumber.gameObject.SetActive(true);
                damageNumber.ResetState();
            }
            else if (activeNumbers.Count + availableNumbers.Count < maxPoolSize)
            {
                damageNumber = CreateNewDamageNumber();
            }
            else
            {
                Debug.LogWarning("[DamageNumberPool] Pool is full, cannot create more damage numbers");
            }

            return damageNumber;
        }

        /// <summary>
        /// 归还到对象池
        /// </summary>
        public void ReturnToPool(DamageNumber damageNumber)
        {
            if (damageNumber == null) return;

            activeNumbers.Remove(damageNumber);
            damageNumber.gameObject.SetActive(false);
            damageNumber.transform.SetParent(poolContainer);

            if (!availableNumbers.Contains(damageNumber))
            {
                availableNumbers.Enqueue(damageNumber);
            }
        }

        /// <summary>
        /// 创建新的伤害数字对象
        /// </summary>
        private DamageNumber CreateNewDamageNumber()
        {
            GameObject go = Instantiate(damageNumberPrefab, poolContainer);
            go.SetActive(false);

            var damageNumber = go.GetComponent<DamageNumber>();
            if (damageNumber == null)
            {
                damageNumber = go.AddComponent<DamageNumber>();
            }

            availableNumbers.Enqueue(damageNumber);
            return damageNumber;
        }

        /// <summary>
        /// 创建默认预制体（如果用户没有提供�?
        /// </summary>
        private GameObject CreateDefaultPrefab()
        {
            // 创建基础GameObject
            GameObject prefab = new GameObject("DamageNumber_Default");
            prefab.transform.SetParent(transform);

            // 添加Canvas
            var canvas = prefab.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.WorldSpace;

            // 延迟设置相机，避免在Awake中找不到
            if (UnityEngine.Camera.main != null)
            {
                canvas.worldCamera = UnityEngine.Camera.main;
            }

            // 设置RectTransform
            var rectTransform = prefab.GetComponent<RectTransform>();
            rectTransform.sizeDelta = new Vector2(200, 100);
            rectTransform.localScale = Vector3.one * 0.01f; // 调整缩放以适配字体大小

            // 添加CanvasScaler
            var scaler = prefab.AddComponent<UnityEngine.UI.CanvasScaler>();
            scaler.dynamicPixelsPerUnit = 10;

            // 创建Text子对�?
            GameObject textObject = new GameObject("Text");
            textObject.transform.SetParent(prefab.transform, false);

            // 添加TextMeshProUGUI
            var textMesh = textObject.AddComponent<TextMeshProUGUI>();
            textMesh.fontSize = 36;
            textMesh.alignment = TextAlignmentOptions.Center;
            textMesh.color = Color.white;
            textMesh.text = "999";
            textMesh.outlineWidth = 0.2f;
            textMesh.outlineColor = new Color(0, 0, 0, 0.8f);

            // 设置Text的RectTransform
            var textRect = textObject.GetComponent<RectTransform>();
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.sizeDelta = Vector2.zero;

            // 添加DamageNumber组件
            prefab.AddComponent<DamageNumber>();

            // 保存为预制体引用
            prefab.SetActive(false);

            return prefab;
        }

        /// <summary>
        /// 清空对象�?
        /// </summary>
        public void ClearPool()
        {
            foreach (var number in activeNumbers)
            {
                if (number != null)
                {
                    Destroy(number.gameObject);
                }
            }

            while (availableNumbers.Count > 0)
            {
                var number = availableNumbers.Dequeue();
                if (number != null)
                {
                    Destroy(number.gameObject);
                }
            }

            activeNumbers.Clear();
            availableNumbers.Clear();
        }

        void OnDestroy()
        {
            ClearPool();
        }
    }
}
