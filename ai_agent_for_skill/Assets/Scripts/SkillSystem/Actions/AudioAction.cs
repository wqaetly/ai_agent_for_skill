using Sirenix.OdinInspector;
using UnityEngine;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 音频效果Action - 控制技能音效的播放，支持2D和3D音效
    /// 可配置音量、音调、空间音效等参数，用于增强技能的听觉反馈
    /// </summary>
    [System.Serializable]
    public class AudioAction : ISkillAction
    {
        [Title("基础设置")]
        public int frame;
        public int duration;
        public bool enabled = true;

        [Title("音频设置")]
        [Tooltip("音频片段名称或路径")]
        public string audioClipName = "";

        [Tooltip("音量大小")]
        [Range(0f, 1f)]
        public float volume = 1f;

        [Tooltip("音调调整")]
        [Range(0.1f, 3f)]
        public float pitch = 1f;

        [Tooltip("是否循环播放")]
        public bool loop = false;

        [Title("空间音效")]
        [Tooltip("是否为3D空间音效")]
        public bool is3D = true;

        [ShowIf("is3D")]
        [Tooltip("音效播放位置偏移")]
        public Vector3 positionOffset = Vector3.zero;

        [ShowIf("is3D")]
        [Tooltip("最小听声距离")]
        [Range(1f, 50f)]
        public float minDistance = 1f;

        [ShowIf("is3D")]
        [Tooltip("最大听声距离")]
        [Range(5f, 500f)]
        public float maxDistance = 50f;

        [ShowIf("is3D")]
        [Tooltip("音量衰减曲线类型")]
        public AudioRolloffMode rolloffMode = AudioRolloffMode.Logarithmic;

        [Title("播放控制")]
        [Tooltip("延迟播放时间（秒）")]
        [Range(0f, 2f)]
        public float delayTime = 0f;

        [Tooltip("淡入时间（秒）")]
        [Range(0f, 2f)]
        public float fadeInTime = 0f;

        [Tooltip("淡出时间（秒）")]
        [Range(0f, 2f)]
        public float fadeOutTime = 0f;

        [Title("高级设置")]
        [Tooltip("音频优先级")]
        [Range(0, 256)]
        public int priority = 128;

        [Tooltip("是否绕过监听器效果")]
        public bool bypassListenerEffects = false;

        [Tooltip("是否绕过混响效果")]
        public bool bypassReverbZones = false;

        // ISkillAction接口实现
        public int Frame => frame;
        public int Duration => duration;
        public bool Enabled => enabled;

        public void OnEnter(object context)
        {
            // 音频播放开始逻辑 - 创建AudioSource并开始播放
        }

        public void OnTick(object context, int currentFrame)
        {
            // 音频播放更新逻辑 - 处理淡入淡出、音量调节等
        }

        public void OnExit(object context)
        {
            // 音频播放结束逻辑 - 停止播放或淡出结束
        }
    }
}