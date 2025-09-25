using Sirenix.OdinInspector;
using UnityEngine;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 镜头效果Action - 控制游戏镜头的各种效果，包括震屏、缩放、移动等
    /// 支持多种镜头效果组合，可用于技能释放时的视觉冲击
    /// </summary>
    [System.Serializable]
    public class CameraAction : ISkillAction
    {
        [Title("基础设置")]
        public int frame;
        public int duration;
        public bool enabled = true;

        [Title("镜头效果类型")]
        [Tooltip("震屏效果强度，0表示无震屏")]
        [Range(0f, 2f)]
        public float shakeIntensity = 0f;

        [Tooltip("镜头缩放倍率，1.0表示正常大小")]
        [Range(0.5f, 3f)]
        public float zoomScale = 1f;

        [Tooltip("镜头位移偏移量")]
        public Vector3 positionOffset = Vector3.zero;

        [Tooltip("镜头旋转偏移量")]
        public Vector3 rotationOffset = Vector3.zero;

        [Title("过渡设置")]
        [Tooltip("效果渐入时间（秒）")]
        [Range(0f, 2f)]
        public float fadeInTime = 0.1f;

        [Tooltip("效果渐出时间（秒）")]
        [Range(0f, 2f)]
        public float fadeOutTime = 0.1f;

        [Title("震屏参数")]
        [ShowIf("@shakeIntensity > 0")]
        [Tooltip("震屏频率")]
        [Range(1f, 30f)]
        public float shakeFrequency = 10f;

        [ShowIf("@shakeIntensity > 0")]
        [Tooltip("震屏衰减曲线")]
        public AnimationCurve shakeCurve = AnimationCurve.EaseInOut(0f, 1f, 1f, 0f);

        [Title("目标设置")]
        [Tooltip("是否跟随施法者")]
        public bool followCaster = true;

        [Tooltip("是否影响主相机")]
        public bool affectMainCamera = true;

        // ISkillAction接口实现
        public int Frame => frame;
        public int Duration => duration;
        public bool Enabled => enabled;

        public void OnEnter(object context)
        {
            // 镜头效果开始逻辑 - 这里只是占位，实际项目中会有具体的镜头控制系统
        }

        public void OnTick(object context, int currentFrame)
        {
            // 镜头效果更新逻辑 - 实时计算震屏、缩放等效果
        }

        public void OnExit(object context)
        {
            // 镜头效果结束逻辑 - 恢复镜头到默认状态
        }
    }
}