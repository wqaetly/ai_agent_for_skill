using UnityEngine;
using TrainingGround.Runtime;

namespace SkillSystem.Editor
{
    /// <summary>
    /// 执行环境检测器 - 用于检测当前运行环境和执行条件
    /// </summary>
    public static class ExecutionEnvironmentDetector
    {
        // 调试开�?- 设置为true可以看到详细的执行日�?        private static readonly bool EnableDebugLog = true;

        // 编辑器预览模式开�?- 允许在编辑器中预览技能效果（位移、动画等�?        // 默认�?false，避免默认托管角色移动，用户可以通过技能编辑器 UI 手动启用
        public static bool EnableEditorPreview = false;

        /// <summary>
        /// 检查是否应该执行技能Action
        /// </summary>
        /// <returns>应该执行返回true，否则返回false</returns>
        public static bool ShouldExecuteActions()
        {
            if (EnableDebugLog)
            {
                Debug.Log($"[ExecutionEnvironmentDetector] ShouldExecuteActions - Application.isPlaying: {Application.isPlaying}");
            }

            // 方案1：优先检查是否在训练场场景中（基于场景名称）
            if (IsInTrainingGroundScene())
            {
                if (EnableDebugLog)
                {
                    Debug.Log("[ExecutionEnvironmentDetector] 检测到训练场场景，允许执行Action");
                }
                return true;
            }

            // 方案2：运行时模式下的检�?            if (Application.isPlaying)
            {
                // 如果在训练场，需要检查训练场状�?                if (IsInTrainingGround())
                {
                    bool shouldExecute = ShouldExecuteInTrainingGround();
                    if (EnableDebugLog)
                    {
                        Debug.Log($"[ExecutionEnvironmentDetector] 在训练场运行时，ShouldExecuteInTrainingGround: {shouldExecute}");
                    }
                    return shouldExecute;
                }

                // 非训练场运行时，正常执行
                if (EnableDebugLog)
                {
                    Debug.Log("[ExecutionEnvironmentDetector] 非训练场运行时，正常执行Action");
                }
                return true;
            }

            // 编辑器预览模式检�?            if (EnableEditorPreview)
            {
                if (EnableDebugLog)
                {
                    Debug.Log("[ExecutionEnvironmentDetector] 编辑器预览模式已启用，允许执行Action");
                }
                return true;
            }

            // 编辑器预览模式禁用，不执行任何Action
            if (EnableDebugLog)
            {
                Debug.Log("[ExecutionEnvironmentDetector] 编辑器预览模式禁用，不执行Action");
            }
            return false;
        }

        /// <summary>
        /// 检查是否应该在训练场运行时执行技能Action
        /// </summary>
        /// <returns>如果在训练场运行时应该执行返回true，否则返回false</returns>
        public static bool ShouldExecuteInTrainingGround()
        {
            // 非运行时不执�?            if (!Application.isPlaying)
                return false;

            // 查找训练场管理器
            var trainingGroundManager = Object.FindFirstObjectByType<TrainingGroundManager>();
            if (trainingGroundManager == null)
            {
                if (EnableDebugLog)
                {
                    Debug.LogWarning("[ExecutionEnvironmentDetector] 无法找到训练场管理器实例");
                }
                return false;
            }

            if (EnableDebugLog)
            {
                Debug.Log("[ExecutionEnvironmentDetector] 找到训练场管理器，允许执行Action");
            }

            // 检查训练场是否在播放状�?            // TODO: 可以根据TrainingGroundManager的具体状态字段来判断
            // 例如：return trainingGroundManager.IsPlaying;
            return true;
        }

        /// <summary>
        /// 检查当前是否在训练场环境中
        /// </summary>
        /// <returns>在训练场返回true，否则返回false</returns>
        public static bool IsInTrainingGround()
        {
            var trainingGroundManager = Object.FindFirstObjectByType<TrainingGroundManager>();
            bool result = trainingGroundManager != null;

            if (EnableDebugLog)
            {
                Debug.Log($"[ExecutionEnvironmentDetector] IsInTrainingGround: {result}");
            }

            return result;
        }

        /// <summary>
        /// 检查当前场景是否为训练场场景（基于场景名称�?        /// 这是一个备选的检测方案，作为补充检测手�?        /// </summary>
        /// <returns>是训练场场景返回true，否则返回false</returns>
        private static bool IsInTrainingGroundScene()
        {
            try
            {
                var sceneName = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;
                bool isTrainingScene = sceneName.Contains("Training") ||
                                      sceneName.Contains("TrainingGround") ||
                                      sceneName.ToLower().Contains("training");

                if (EnableDebugLog && isTrainingScene)
                {
                    Debug.Log($"[ExecutionEnvironmentDetector] 检测到训练场场�? {sceneName}");
                }

                return isTrainingScene;
            }
            catch (System.Exception ex)
            {
                if (EnableDebugLog)
                {
                    Debug.LogWarning($"[ExecutionEnvironmentDetector] 场景名称检测失�? {ex.Message}");
                }
                return false;
            }
        }
    }
}
