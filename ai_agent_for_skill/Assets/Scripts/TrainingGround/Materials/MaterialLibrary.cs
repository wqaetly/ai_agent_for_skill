using UnityEngine;
using System.Collections.Generic;

namespace TrainingGround.Materials
{
    /// <summary>
    /// 材质库 - 提供预配置的URP兼容材质
    /// 避免运行时重复创建材质，提升性能
    /// </summary>
    public class MaterialLibrary : MonoBehaviour
    {
        private static MaterialLibrary instance;
        public static MaterialLibrary Instance
        {
            get
            {
                if (instance == null)
                {
                    GameObject obj = new GameObject("MaterialLibrary");
                    instance = obj.AddComponent<MaterialLibrary>();
                    DontDestroyOnLoad(obj);
                }
                return instance;
            }
        }

        [Header("基础材质配置")]
        [SerializeField] private bool useInstancedMaterials = true;

        // 材质缓存
        private Dictionary<string, Material> materialCache = new Dictionary<string, Material>();

        // Shader缓存
        private Shader urpLitShader;
        private Shader urpUnlitShader;
        private Shader urpParticleShader;

        void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }

            instance = this;
            DontDestroyOnLoad(gameObject);

            // 缓存Shader
            CacheShaders();
        }

        /// <summary>
        /// 缓存URP Shader
        /// </summary>
        private void CacheShaders()
        {
            urpLitShader = Shader.Find("Universal Render Pipeline/Lit");
            urpUnlitShader = Shader.Find("Universal Render Pipeline/Unlit");
            urpParticleShader = Shader.Find("Universal Render Pipeline/Particles/Unlit");

            if (urpLitShader == null)
            {
                Debug.LogError("[MaterialLibrary] URP Lit Shader not found!");
            }

            Debug.Log("[MaterialLibrary] Shaders cached");
        }

        #region 玩家材质

        /// <summary>
        /// 获取玩家材质
        /// </summary>
        public Material GetPlayerMaterial(Color color)
        {
            string key = $"Player_{color.r}_{color.g}_{color.b}";

            if (materialCache.TryGetValue(key, out Material cached))
            {
                return cached;
            }

            Material mat = CreateLitMaterial(color, 0.3f, 0.5f);
            materialCache[key] = mat;

            return mat;
        }

        /// <summary>
        /// 获取默认玩家材质（蓝色）
        /// </summary>
        public Material GetDefaultPlayerMaterial()
        {
            return GetPlayerMaterial(Color.blue);
        }

        #endregion

        #region 敌人材质

        /// <summary>
        /// 获取敌人材质（训练木桩）
        /// </summary>
        public Material GetEnemyMaterial(Color color)
        {
            string key = $"Enemy_{color.r}_{color.g}_{color.b}";

            if (materialCache.TryGetValue(key, out Material cached))
            {
                return cached;
            }

            Material mat = CreateLitMaterial(color, 0.1f, 0.3f);
            materialCache[key] = mat;

            return mat;
        }

        /// <summary>
        /// 获取默认敌人材质（灰色）
        /// </summary>
        public Material GetDefaultEnemyMaterial()
        {
            return GetEnemyMaterial(Color.gray);
        }

        #endregion

        #region 特效材质

        /// <summary>
        /// 获取AOE范围指示材质（半透明）
        /// </summary>
        public Material GetAOEIndicatorMaterial(Color color, float alpha = 0.3f)
        {
            string key = $"AOE_{color.r}_{color.g}_{color.b}_{alpha}";

            if (materialCache.TryGetValue(key, out Material cached))
            {
                return cached;
            }

            Material mat = CreateTransparentMaterial(color, alpha);
            materialCache[key] = mat;

            return mat;
        }

        /// <summary>
        /// 获取默认AOE材质（红色半透明）
        /// </summary>
        public Material GetDefaultAOEMaterial()
        {
            return GetAOEIndicatorMaterial(Color.red, 0.3f);
        }

        /// <summary>
        /// 获取投射物材质
        /// </summary>
        public Material GetProjectileMaterial(Color color, float metallic = 0.5f)
        {
            string key = $"Projectile_{color.r}_{color.g}_{color.b}_{metallic}";

            if (materialCache.TryGetValue(key, out Material cached))
            {
                return cached;
            }

            Material mat = CreateLitMaterial(color, metallic, 0.5f);
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", color * 0.5f);

            materialCache[key] = mat;

            return mat;
        }

        /// <summary>
        /// 获取默认投射物材质（橙色）
        /// </summary>
        public Material GetDefaultProjectileMaterial()
        {
            return GetProjectileMaterial(new Color(1f, 0.5f, 0f), 0.5f);
        }

        /// <summary>
        /// 获取粒子材质（用于拖尾等）
        /// </summary>
        public Material GetParticleMaterial(Color color)
        {
            string key = $"Particle_{color.r}_{color.g}_{color.b}";

            if (materialCache.TryGetValue(key, out Material cached))
            {
                return cached;
            }

            Material mat = new Material(urpParticleShader);
            mat.color = color;
            mat.SetFloat("_Surface", 1); // Transparent
            mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;

            materialCache[key] = mat;

            return mat;
        }

        /// <summary>
        /// 获取命中特效材质（发光）
        /// </summary>
        public Material GetHitEffectMaterial(Color color)
        {
            string key = $"HitEffect_{color.r}_{color.g}_{color.b}";

            if (materialCache.TryGetValue(key, out Material cached))
            {
                return cached;
            }

            Material mat = CreateLitMaterial(color, 0.8f, 0.9f);
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", color * 2f); // 强发光

            materialCache[key] = mat;

            return mat;
        }

        #endregion

        #region 材质创建工具

        /// <summary>
        /// 创建标准Lit材质
        /// </summary>
        private Material CreateLitMaterial(Color color, float metallic = 0f, float smoothness = 0.5f)
        {
            Material mat = new Material(urpLitShader);
            mat.color = color;
            mat.SetFloat("_Metallic", metallic);
            mat.SetFloat("_Smoothness", smoothness);
            mat.SetFloat("_Surface", 0); // Opaque
            mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Geometry;

            return mat;
        }

        /// <summary>
        /// 创建透明材质
        /// </summary>
        private Material CreateTransparentMaterial(Color baseColor, float alpha)
        {
            Material mat = new Material(urpLitShader);

            Color colorWithAlpha = new Color(baseColor.r, baseColor.g, baseColor.b, alpha);
            mat.color = colorWithAlpha;

            // URP透明材质设置
            mat.SetFloat("_Surface", 1); // 0 = Opaque, 1 = Transparent
            mat.SetFloat("_Blend", 0); // 0 = Alpha, 1 = Premultiply, 2 = Additive, 3 = Multiply
            mat.SetFloat("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            mat.SetFloat("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            mat.SetFloat("_ZWrite", 0);
            mat.SetFloat("_AlphaClip", 0);

            // 设置渲染队列为透明
            mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;

            // 启用关键字
            mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            mat.EnableKeyword("_ALPHAPREMULTIPLY_ON");

            return mat;
        }

        /// <summary>
        /// 创建Unlit材质（无光照）
        /// </summary>
        private Material CreateUnlitMaterial(Color color)
        {
            Material mat = new Material(urpUnlitShader);
            mat.color = color;
            mat.SetFloat("_Surface", 0); // Opaque

            return mat;
        }

        #endregion

        #region 材质实例管理

        /// <summary>
        /// 为Renderer创建材质实例（避免共享材质）
        /// </summary>
        public Material CreateMaterialInstance(Material baseMaterial)
        {
            if (baseMaterial == null) return null;

            Material instance = new Material(baseMaterial);
            return instance;
        }

        /// <summary>
        /// 清理未使用的材质缓存
        /// </summary>
        [ContextMenu("Clear Material Cache")]
        public void ClearMaterialCache()
        {
            foreach (var mat in materialCache.Values)
            {
                if (mat != null)
                {
                    Destroy(mat);
                }
            }

            materialCache.Clear();
            Debug.Log("[MaterialLibrary] Material cache cleared");
        }

        #endregion

        #region 高级材质效果

        /// <summary>
        /// 创建受击闪烁材质
        /// </summary>
        public Material CreateDamagedMaterial(Material baseMaterial, Color flashColor)
        {
            if (baseMaterial == null) return null;

            Material flashMat = new Material(baseMaterial);
            flashMat.EnableKeyword("_EMISSION");
            flashMat.SetColor("_EmissionColor", flashColor * 1.5f);

            return flashMat;
        }

        /// <summary>
        /// 创建溶解材质（用于死亡效果等）
        /// </summary>
        public Material CreateDissolveMaterial(Color color)
        {
            // 这里可以使用自定义的Dissolve Shader
            // 目前使用基础Lit材质作为占位
            Material mat = CreateLitMaterial(color, 0.5f, 0.5f);
            mat.EnableKeyword("_ALPHATEST_ON");

            return mat;
        }

        #endregion

        void OnDestroy()
        {
            ClearMaterialCache();
        }
    }
}
