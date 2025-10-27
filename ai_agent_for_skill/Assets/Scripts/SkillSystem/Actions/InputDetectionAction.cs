using System;
using UnityEngine;
using Sirenix.OdinInspector;
using SkillSystem.Runtime;

namespace SkillSystem.Actions
{
    /// <summary>
    /// 输入检测行为脚本
    /// 功能概述：在指定时间窗口内检测玩家输入，并根据配置触发帧跳转或事件。
    /// 支持多种按键类型和输入状态检测（按下/抬起/持续按住）。
    /// 适用于需要玩家交互控制的技能，如蓄力技能、可中断技能、连续施法等。
    /// 典型应用：赛恩W引爆、蔚Q蓄力、卡牌R取消传送、瑞文Q连续施法。
    /// </summary>
    [Serializable]
    [ActionDisplayName("输入检测")]
    public class InputDetectionAction : ISkillAction
    {
        [BoxGroup("Input Settings")]
        [LabelText("Input Key")]
        [InfoBox("监听的按键")]
        /// <summary>监听的按键代码</summary>
        public KeyCode inputKey = KeyCode.W;

        [BoxGroup("Input Settings")]
        [LabelText("Input Type")]
        /// <summary>输入检测类型</summary>
        public InputDetectionType detectionType = InputDetectionType.KeyDown;

        [BoxGroup("Input Settings")]
        [LabelText("Alternative Keys")]
        [InfoBox("可选的备用按键列表，任意一个触发即可")]
        /// <summary>备用按键列表</summary>
        public KeyCode[] alternativeKeys = new KeyCode[0];

        [BoxGroup("Action Settings")]
        [LabelText("Action Mode")]
        [InfoBox("检测到输入后执行的操作类型")]
        /// <summary>动作模式</summary>
        public InputActionMode actionMode = InputActionMode.JumpToFrame;

        [BoxGroup("Action Settings")]
        [LabelText("Target Frame")]
        [MinValue(0)]
        [ShowIf("@actionMode == InputActionMode.JumpToFrame")]
        [InfoBox("跳转的目标帧数")]
        /// <summary>跳转目标帧</summary>
        public int targetFrame = 90;

        [BoxGroup("Action Settings")]
        [LabelText("Stop Skill")]
        [ShowIf("@actionMode == InputActionMode.StopSkill")]
        /// <summary>是否停止技能播放</summary>
        public bool stopSkill = true;

        [BoxGroup("Action Settings")]
        [LabelText("Condition Name")]
        [ShowIf("@actionMode == InputActionMode.TriggerCondition")]
        [InfoBox("触发的条件名称，用于外部逻辑判断")]
        /// <summary>条件名称</summary>
        public string conditionName = "InputDetected";

        [BoxGroup("Timing Settings")]
        [LabelText("Consume Input")]
        [InfoBox("检测到输入后是否立即停止检测（避免重复触发）")]
        /// <summary>消耗输入，检测到后立即停止</summary>
        public bool consumeInput = true;

        [BoxGroup("Timing Settings")]
        [LabelText("Cooldown After Trigger")]
        [MinValue(0)]
        [InfoBox("触发后的冷却时间（帧数），防止连续触发")]
        /// <summary>触发后的冷却帧数</summary>
        public int cooldownFrames = 0;

        [BoxGroup("Visual Settings")]
        [LabelText("Show Input Prompt")]
        [InfoBox("是否显示输入提示UI")]
        /// <summary>显示输入提示</summary>
        public bool showInputPrompt = false;

        [BoxGroup("Visual Settings")]
        [LabelText("Prompt Text")]
        [ShowIf("showInputPrompt")]
        /// <summary>提示文本</summary>
        public string promptText = "Press W to activate";

        [BoxGroup("Visual Settings")]
        [LabelText("Input Effect")]
        [InfoBox("检测到输入时播放的视觉效果")]
        /// <summary>输入检测特效</summary>
        public GameObject inputEffect;

        [BoxGroup("Audio Settings")]
        [LabelText("Input Sound")]
        /// <summary>输入检测音效</summary>
        public AudioClip inputSound;

        [BoxGroup("Debug Settings")]
        [LabelText("Debug Mode")]
        [InfoBox("调试模式，在Console输出详细日志")]
        /// <summary>调试模式</summary>
        public bool debugMode = true;

        /// <summary>是否已触发</summary>
        private bool hasTriggered = false;
        /// <summary>冷却剩余帧数</summary>
        private int cooldownRemaining = 0;

        public override string GetActionName()
        {
            return "Input Detection Action";
        }

        public override void OnEnter()
        {
            hasTriggered = false;
            cooldownRemaining = 0;

            if (debugMode)
            {
                Debug.Log($"[InputDetectionAction] Started monitoring input: {inputKey}, Type: {detectionType}, Mode: {actionMode}");
            }

            if (showInputPrompt)
            {
                ShowPrompt();
            }
        }

        public override void OnTick(int relativeFrame)
        {
            // 冷却中，跳过检测
            if (cooldownRemaining > 0)
            {
                cooldownRemaining--;
                return;
            }

            // 已触发且设置为消耗输入，停止检测
            if (hasTriggered && consumeInput)
            {
                return;
            }

            // 检测输入
            if (CheckInput())
            {
                if (debugMode)
                {
                    Debug.Log($"[InputDetectionAction] Input detected at relative frame {relativeFrame}");
                }

                OnInputDetected();
            }
        }

        public override void OnExit()
        {
            if (showInputPrompt)
            {
                HidePrompt();
            }

            if (debugMode)
            {
                Debug.Log($"[InputDetectionAction] Stopped monitoring input. Triggered: {hasTriggered}");
            }
        }

        /// <summary>检测输入</summary>
        /// <returns>是否检测到输入</returns>
        private bool CheckInput()
        {
            bool detected = false;

            // 检测主按键
            detected = CheckKey(inputKey);

            // 检测备用按键
            if (!detected && alternativeKeys != null)
            {
                foreach (var altKey in alternativeKeys)
                {
                    if (CheckKey(altKey))
                    {
                        detected = true;
                        break;
                    }
                }
            }

            return detected;
        }

        /// <summary>检测单个按键</summary>
        /// <param name="key">按键代码</param>
        /// <returns>是否满足检测条件</returns>
        private bool CheckKey(KeyCode key)
        {
            switch (detectionType)
            {
                case InputDetectionType.KeyDown:
                    return Input.GetKeyDown(key);

                case InputDetectionType.KeyUp:
                    return Input.GetKeyUp(key);

                case InputDetectionType.KeyHold:
                    return Input.GetKey(key);

                default:
                    return false;
            }
        }

        /// <summary>输入检测到后的处理</summary>
        private void OnInputDetected()
        {
            hasTriggered = true;
            cooldownRemaining = cooldownFrames;

            // 播放特效
            PlayEffects();

            // 通知事件系统
            SkillSystemEvents.NotifyInputDetected(inputKey);

            // 根据动作模式执行操作
            ExecuteAction();
        }

        /// <summary>执行对应的动作</summary>
        private void ExecuteAction()
        {
            switch (actionMode)
            {
                case InputActionMode.JumpToFrame:
                    if (debugMode)
                    {
                        Debug.Log($"[InputDetectionAction] Requesting frame jump to {targetFrame}");
                    }
                    SkillSystemEvents.RequestFrameJump(targetFrame);
                    break;

                case InputActionMode.StopSkill:
                    if (debugMode)
                    {
                        Debug.Log($"[InputDetectionAction] Requesting skill stop");
                    }
                    SkillSystemEvents.RequestSkillStop();
                    break;

                case InputActionMode.TriggerCondition:
                    if (debugMode)
                    {
                        Debug.Log($"[InputDetectionAction] Triggering condition: {conditionName}");
                    }
                    SkillSystemEvents.TriggerCondition(conditionName, inputKey);
                    break;

                case InputActionMode.NotifyOnly:
                    // 仅通知，不执行其他操作
                    if (debugMode)
                    {
                        Debug.Log($"[InputDetectionAction] Input notified only");
                    }
                    break;
            }
        }

        /// <summary>播放特效和音效</summary>
        private void PlayEffects()
        {
            if (inputEffect != null)
            {
                var casterTransform = UnityEngine.Object.FindFirstObjectByType<Transform>();
                if (casterTransform != null)
                {
                    UnityEngine.Object.Instantiate(inputEffect, casterTransform.position, Quaternion.identity);
                }
            }

            if (inputSound != null)
            {
                // 在实际项目中，这里会播放音效
                Debug.Log($"[InputDetectionAction] Playing input sound");
            }
        }

        /// <summary>显示输入提示</summary>
        private void ShowPrompt()
        {
            // 在实际项目中，这里会显示UI提示
            Debug.Log($"[InputDetectionAction] Showing prompt: {promptText}");
        }

        /// <summary>隐藏输入提示</summary>
        private void HidePrompt()
        {
            // 在实际项目中，这里会隐藏UI提示
            Debug.Log($"[InputDetectionAction] Hiding prompt");
        }
    }

    /// <summary>输入检测类型枚举</summary>
    public enum InputDetectionType
    {
        KeyDown,    // 按键按下（单次触发）
        KeyUp,      // 按键抬起（单次触发）
        KeyHold     // 按键持续按住（持续触发）
    }

    /// <summary>输入动作模式枚举</summary>
    public enum InputActionMode
    {
        JumpToFrame,        // 跳转到指定帧
        StopSkill,          // 停止技能播放
        TriggerCondition,   // 触发条件（供外部逻辑判断）
        NotifyOnly          // 仅通知，不执行其他操作
    }
}
