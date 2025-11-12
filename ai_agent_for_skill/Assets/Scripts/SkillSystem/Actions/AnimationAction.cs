using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 动画播放Action
    /// 功能概述：控制角色播放指定的动画片段，支持动画层级、归一化时间和淡入淡出�?
    /// </summary>
    [Serializable]
    [ActionDisplayName("播放动画")]
    [ActionCategory("Visual & Audio")]
    [ActionDescription("播放角色动画片段。通过指定动画剪辑名称(AnimationClip Name)来播放对应动画，支持动画层级切换、归一化时间控制、交叉淡入淡�?CrossFade)等功能。常用于攻击动画、技能释放动画、移动动画等视觉表现。不涉及伤害、控制、移动等游戏逻辑，纯粹用于视觉展示�?)]
    public class AnimationAction : ISkillAction
    {
        [SerializeField]
        [LabelText("Animation Clip Name")]
        public string animationClipName = "Attack01";

        [SerializeField]
        [LabelText("Normalized Time")]
        [Range(0f, 1f)]
        public float normalizedTime = 0f;

        [SerializeField]
        [LabelText("Cross Fade Duration")]
        [MinValue(0f)]
        public float crossFadeDuration = 0.1f;

        [SerializeField]
        [LabelText("Animation Layer")]
        [MinValue(0)]
        public int animationLayer = 0;

        public override string GetActionName()
        {
            return "Animation Action";
        }

        public override void Execute()
        {
            var animator = UnityEngine.Object.FindFirstObjectByType<Animator>();
            if (animator != null)
            {
                animator.CrossFade(animationClipName, crossFadeDuration, animationLayer, normalizedTime);
                Debug.Log($"Playing animation: {animationClipName}");
            }
            else
            {
                Debug.LogWarning("No Animator found in scene for AnimationAction");
            }
        }

        public override void OnEnter()
        {
            var animator = UnityEngine.Object.FindFirstObjectByType<Animator>();
            if (animator != null)
            {
                animator.CrossFade(animationClipName, crossFadeDuration, animationLayer, normalizedTime);
                Debug.Log($"[AnimationAction] Started animation: {animationClipName}");
            }
            else
            {
                Debug.LogWarning("[AnimationAction] No Animator found in scene");
            }
        }

        public override void OnTick(int relativeFrame)
        {
            // Monitor animation state during execution
            var animator = UnityEngine.Object.FindFirstObjectByType<Animator>();
            if (animator != null)
            {
                var currentState = animator.GetCurrentAnimatorStateInfo(animationLayer);
                if (relativeFrame % 5 == 0) // Log every 5 frames
                {
                    Debug.Log($"[AnimationAction] {animationClipName} progress: {currentState.normalizedTime:F2}");
                }
            }
        }

        public override void OnExit()
        {
            Debug.Log($"[AnimationAction] Finished animation action: {animationClipName}");
        }
    }
}