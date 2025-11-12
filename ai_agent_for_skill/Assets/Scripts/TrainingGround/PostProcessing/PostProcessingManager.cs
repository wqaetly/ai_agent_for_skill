using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TrainingGround.PostProcessing
{
    /// <summary>
    /// Post-Processing管理器 - 管理URP后期处理效果
    /// 提供动态调整后期效果、战斗模式切换等商业级功能
    /// </summary>
    public class PostProcessingManager : MonoBehaviour
    {
        [Header("Volume组件")]
        [SerializeField] private Volume globalVolume;
        [SerializeField] private Volume combatVolume;

        [Header("Profile配置")]
        [SerializeField] private VolumeProfile globalProfile;
        [SerializeField] private VolumeProfile combatProfile;

        [Header("效果设置")]
        [SerializeField] private bool enableBloom = true;
        [SerializeField] private bool enableColorGrading = true;
        [SerializeField] private bool enableVignette = true;
        [SerializeField] private bool enableChromaticAberration = false;
        [SerializeField] private bool enableMotionBlur = false;

        [Header("战斗模式设置")]
        [SerializeField] private float combatVignetteIntensity = 0.35f;
        [SerializeField] private Color combatColorTint = new Color(1f, 0.95f, 0.9f);
        [SerializeField] private float combatBloomIntensity = 0.3f;

        // Post-Processing组件引用
        private Bloom bloomEffect;
        private ColorAdjustments colorAdjustments;
        private Vignette vignetteEffect;
        private ChromaticAberration chromaticAberration;
        private MotionBlur motionBlur;

        // 状态
        private bool isInCombatMode = false;

        void Awake()
        {
            // 创建Global Volume（如果不存在）
            if (globalVolume == null)
            {
                CreateGlobalVolume();
            }

            // 初始化Profile
            InitializeVolumeProfile();
        }

        void Start()
        {
            // 应用初始效果
            ApplyDefaultEffects();
        }

        /// <summary>
        /// 创建Global Volume
        /// </summary>
        private void CreateGlobalVolume()
        {
            GameObject volumeObj = new GameObject("Global Volume");
            volumeObj.transform.SetParent(transform);

            globalVolume = volumeObj.AddComponent<Volume>();
            globalVolume.isGlobal = true;
            globalVolume.priority = 0;

            // 创建新的Profile
            globalProfile = ScriptableObject.CreateInstance<VolumeProfile>();
            globalVolume.profile = globalProfile;

            Debug.Log("[PostProcessingManager] Global Volume created");
        }

        /// <summary>
        /// 初始化Volume Profile
        /// </summary>
        private void InitializeVolumeProfile()
        {
            if (globalProfile == null)
            {
                globalProfile = ScriptableObject.CreateInstance<VolumeProfile>();
                if (globalVolume != null)
                {
                    globalVolume.profile = globalProfile;
                }
            }

            // 添加Bloom效果
            if (enableBloom && !globalProfile.Has<Bloom>())
            {
                bloomEffect = globalProfile.Add<Bloom>();
                ConfigureBloom(bloomEffect);
            }
            else if (globalProfile.Has<Bloom>())
            {
                globalProfile.TryGet<Bloom>(out bloomEffect);
            }

            // 添加Color Adjustments效果
            if (enableColorGrading && !globalProfile.Has<ColorAdjustments>())
            {
                colorAdjustments = globalProfile.Add<ColorAdjustments>();
                ConfigureColorAdjustments(colorAdjustments);
            }
            else if (globalProfile.Has<ColorAdjustments>())
            {
                globalProfile.TryGet<ColorAdjustments>(out colorAdjustments);
            }

            // 添加Vignette效果
            if (enableVignette && !globalProfile.Has<Vignette>())
            {
                vignetteEffect = globalProfile.Add<Vignette>();
                ConfigureVignette(vignetteEffect);
            }
            else if (globalProfile.Has<Vignette>())
            {
                globalProfile.TryGet<Vignette>(out vignetteEffect);
            }

            // 添加Chromatic Aberration效果
            if (enableChromaticAberration && !globalProfile.Has<ChromaticAberration>())
            {
                chromaticAberration = globalProfile.Add<ChromaticAberration>();
                ConfigureChromaticAberration(chromaticAberration);
            }
            else if (globalProfile.Has<ChromaticAberration>())
            {
                globalProfile.TryGet<ChromaticAberration>(out chromaticAberration);
            }

            // 添加Motion Blur效果
            if (enableMotionBlur && !globalProfile.Has<MotionBlur>())
            {
                motionBlur = globalProfile.Add<MotionBlur>();
                ConfigureMotionBlur(motionBlur);
            }
            else if (globalProfile.Has<MotionBlur>())
            {
                globalProfile.TryGet<MotionBlur>(out motionBlur);
            }

            Debug.Log("[PostProcessingManager] Volume Profile initialized");
        }

        #region 效果配置

        private void ConfigureBloom(Bloom bloom)
        {
            bloom.active = true;
            bloom.intensity.value = 0.2f;
            bloom.threshold.value = 0.9f;
            bloom.scatter.value = 0.7f;
        }

        private void ConfigureColorAdjustments(ColorAdjustments colorAdjustments)
        {
            colorAdjustments.active = true;
            colorAdjustments.postExposure.value = 0f;
            colorAdjustments.contrast.value = 5f;
            colorAdjustments.saturation.value = 5f;
        }

        private void ConfigureVignette(Vignette vignette)
        {
            vignette.active = true;
            vignette.intensity.value = 0.2f;
            vignette.smoothness.value = 0.4f;
            vignette.color.value = Color.black;
        }

        private void ConfigureChromaticAberration(ChromaticAberration chromatic)
        {
            chromatic.active = false; // 默认关闭，战斗时可开启
            chromatic.intensity.value = 0.1f;
        }

        private void ConfigureMotionBlur(MotionBlur motionBlur)
        {
            motionBlur.active = false; // 默认关闭
            motionBlur.intensity.value = 0.3f;
            motionBlur.quality.value = MotionBlurQuality.Medium;
        }

        #endregion

        #region 公共接口

        /// <summary>
        /// 应用默认效果
        /// </summary>
        public void ApplyDefaultEffects()
        {
            isInCombatMode = false;

            if (vignetteEffect != null)
            {
                vignetteEffect.intensity.value = 0.2f;
            }

            if (bloomEffect != null)
            {
                bloomEffect.intensity.value = 0.2f;
            }

            if (colorAdjustments != null)
            {
                colorAdjustments.colorFilter.value = Color.white;
            }

            Debug.Log("[PostProcessingManager] Default effects applied");
        }

        /// <summary>
        /// 切换到战斗模式后期效果
        /// </summary>
        public void SwitchToCombatMode()
        {
            isInCombatMode = true;

            // 增强Vignette（边缘暗角）
            if (vignetteEffect != null)
            {
                vignetteEffect.intensity.value = combatVignetteIntensity;
            }

            // 增强Bloom（光晕）
            if (bloomEffect != null)
            {
                bloomEffect.intensity.value = combatBloomIntensity;
            }

            // 色调偏移
            if (colorAdjustments != null)
            {
                colorAdjustments.colorFilter.value = combatColorTint;
            }

            Debug.Log("[PostProcessingManager] Switched to combat mode");
        }

        /// <summary>
        /// 切换回普通模式
        /// </summary>
        public void SwitchToNormalMode()
        {
            ApplyDefaultEffects();
            Debug.Log("[PostProcessingManager] Switched to normal mode");
        }

        /// <summary>
        /// 动态调整Bloom强度
        /// </summary>
        public void SetBloomIntensity(float intensity)
        {
            if (bloomEffect != null)
            {
                bloomEffect.intensity.value = Mathf.Clamp(intensity, 0f, 1f);
            }
        }

        /// <summary>
        /// 动态调整Vignette强度
        /// </summary>
        public void SetVignetteIntensity(float intensity)
        {
            if (vignetteEffect != null)
            {
                vignetteEffect.intensity.value = Mathf.Clamp01(intensity);
            }
        }

        /// <summary>
        /// 设置色调滤镜
        /// </summary>
        public void SetColorFilter(Color color)
        {
            if (colorAdjustments != null)
            {
                colorAdjustments.colorFilter.value = color;
            }
        }

        /// <summary>
        /// 启用/禁用Motion Blur
        /// </summary>
        public void SetMotionBlur(bool enabled)
        {
            if (motionBlur != null)
            {
                motionBlur.active = enabled;
            }
        }

        /// <summary>
        /// 启用/禁用Chromatic Aberration（色差）
        /// </summary>
        public void SetChromaticAberration(bool enabled, float intensity = 0.1f)
        {
            if (chromaticAberration != null)
            {
                chromaticAberration.active = enabled;
                chromaticAberration.intensity.value = intensity;
            }
        }

        /// <summary>
        /// 技能释放时的特殊效果
        /// </summary>
        public void TriggerSkillEffect(float duration = 0.5f)
        {
            StartCoroutine(SkillEffectCoroutine(duration));
        }

        private System.Collections.IEnumerator SkillEffectCoroutine(float duration)
        {
            // 技能释放时短暂增强效果
            float originalBloom = bloomEffect != null ? bloomEffect.intensity.value : 0f;
            float originalVignette = vignetteEffect != null ? vignetteEffect.intensity.value : 0f;

            // 增强效果
            if (bloomEffect != null) bloomEffect.intensity.value = originalBloom * 1.5f;
            if (vignetteEffect != null) vignetteEffect.intensity.value = originalVignette * 1.3f;
            if (chromaticAberration != null)
            {
                chromaticAberration.active = true;
                chromaticAberration.intensity.value = 0.2f;
            }

            yield return new WaitForSeconds(duration);

            // 恢复效果
            if (bloomEffect != null) bloomEffect.intensity.value = originalBloom;
            if (vignetteEffect != null) vignetteEffect.intensity.value = originalVignette;
            if (chromaticAberration != null && !enableChromaticAberration)
            {
                chromaticAberration.active = false;
            }
        }

        #endregion

        #region Editor工具

#if UNITY_EDITOR
        [ContextMenu("Apply Default Effects")]
        private void EditorApplyDefaultEffects()
        {
            InitializeVolumeProfile();
            ApplyDefaultEffects();
        }

        [ContextMenu("Apply Combat Effects")]
        private void EditorApplyCombatEffects()
        {
            InitializeVolumeProfile();
            SwitchToCombatMode();
        }

        [ContextMenu("Reset All Effects")]
        private void EditorResetEffects()
        {
            if (globalProfile != null)
            {
                globalProfile.components.Clear();
                InitializeVolumeProfile();
            }
        }
#endif

        #endregion
    }
}
