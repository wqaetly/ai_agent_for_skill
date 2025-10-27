using UnityEngine;

namespace SkillSystem.Runtime
{
    /// <summary>
    /// 技能系统静态事件类
    /// 功能概述：提供全局事件通信机制，用于Action与SkillPlayer之间的解耦通信。
    /// 支持帧跳转、技能中断、条件分支等高级控制功能。
    /// 使用静态事件避免直接引用，保持系统的模块化和可测试性。
    /// </summary>
    public static class SkillSystemEvents
    {
        /// <summary>
        /// 帧跳转事件
        /// 当Action检测到特定条件（如玩家输入）需要跳转到其他帧时触发
        /// </summary>
        public static event System.Action<int> OnRequestFrameJump;

        /// <summary>
        /// 技能中断事件
        /// 当需要立即停止技能播放时触发
        /// </summary>
        public static event System.Action OnRequestSkillStop;

        /// <summary>
        /// 条件分支事件
        /// 当Action检测到条件满足，需要执行特定分支逻辑时触发
        /// </summary>
        public static event System.Action<string, object> OnConditionTriggered;

        /// <summary>
        /// 输入检测事件
        /// 当InputDetectionAction检测到玩家输入时触发，可用于外部逻辑监听
        /// </summary>
        public static event System.Action<KeyCode> OnInputDetected;

        /// <summary>
        /// 请求帧跳转
        /// </summary>
        /// <param name="targetFrame">目标帧数</param>
        public static void RequestFrameJump(int targetFrame)
        {
            OnRequestFrameJump?.Invoke(targetFrame);
            Debug.Log($"[SkillSystemEvents] Frame jump requested to frame {targetFrame}");
        }

        /// <summary>
        /// 请求停止技能
        /// </summary>
        public static void RequestSkillStop()
        {
            OnRequestSkillStop?.Invoke();
            Debug.Log($"[SkillSystemEvents] Skill stop requested");
        }

        /// <summary>
        /// 触发条件分支
        /// </summary>
        /// <param name="conditionName">条件名称</param>
        /// <param name="data">附加数据</param>
        public static void TriggerCondition(string conditionName, object data = null)
        {
            OnConditionTriggered?.Invoke(conditionName, data);
            Debug.Log($"[SkillSystemEvents] Condition triggered: {conditionName}");
        }

        /// <summary>
        /// 通知输入检测
        /// </summary>
        /// <param name="keyCode">按键代码</param>
        public static void NotifyInputDetected(KeyCode keyCode)
        {
            OnInputDetected?.Invoke(keyCode);
            Debug.Log($"[SkillSystemEvents] Input detected: {keyCode}");
        }

        /// <summary>
        /// 清除所有事件订阅（用于场景切换或重置）
        /// </summary>
        public static void ClearAllEvents()
        {
            OnRequestFrameJump = null;
            OnRequestSkillStop = null;
            OnConditionTriggered = null;
            OnInputDetected = null;
            Debug.Log($"[SkillSystemEvents] All events cleared");
        }
    }
}
