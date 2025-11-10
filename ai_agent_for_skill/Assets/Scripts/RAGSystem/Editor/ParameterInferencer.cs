using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// 参数推理引擎 - 基于上下文和统计推断参数值
    /// 核心功能：统计推理、置信度计算、多备选值、Unity类型支持
    /// </summary>
    public class ParameterInferencer
    {
        private ActionParameterDependencyGraph dependencyGraph;
        private ParameterStatisticsCache statisticsCache;

        public ParameterInferencer()
        {
            dependencyGraph = new ActionParameterDependencyGraph();
            statisticsCache = new ParameterStatisticsCache();
        }

        /// <summary>
        /// 推断Action的所有参数
        /// </summary>
        /// <param name="actionType">Action类型</param>
        /// <param name="context">技能上下文</param>
        /// <param name="referenceSkills">参考技能列表（可选）</param>
        /// <returns>参数推断结果</returns>
        public ParameterInferenceResult InferParameters(
            string actionType,
            SkillContextFeatures context,
            List<string> referenceSkills = null)
        {
            Debug.Log($"[ParameterInferencer] Inferring parameters for {actionType}");

            var result = new ParameterInferenceResult
            {
                actionType = actionType,
                timestamp = DateTime.Now
            };

            // 获取Action类型的所有字段
            Type type = FindActionType(actionType);
            if (type == null)
            {
                Debug.LogError($"[ParameterInferencer] Action type '{actionType}' not found");
                return result;
            }

            var fields = type.GetFields(BindingFlags.Public | BindingFlags.Instance);

            foreach (var field in fields)
            {
                // 跳过基类字段
                if (field.DeclaringType == typeof(SkillSystem.Actions.ISkillAction))
                    continue;

                var paramInference = InferSingleParameter(
                    actionType,
                    field.Name,
                    field.FieldType,
                    context,
                    referenceSkills
                );

                result.parameterInferences.Add(paramInference);
            }

            // 验证参数配置
            var parameters = result.parameterInferences.ToDictionary(
                p => p.parameterName,
                p => p.recommendedValue
            );
            result.validationResult = dependencyGraph.ValidateParameters(actionType, parameters);

            Debug.Log($"[ParameterInferencer] Inferred {result.parameterInferences.Count} parameters with {result.parameterInferences.Count(p => p.confidence >= 0.7f)} high-confidence values");

            return result;
        }

        /// <summary>
        /// 推断单个参数
        /// </summary>
        private ParameterInference InferSingleParameter(
            string actionType,
            string parameterName,
            Type parameterType,
            SkillContextFeatures context,
            List<string> referenceSkills)
        {
            var inference = new ParameterInference
            {
                parameterName = parameterName,
                parameterType = parameterType.Name,
                isUnityType = IsUnitySpecialType(parameterType)
            };

            // 从统计数据推断
            var stats = statisticsCache.GetStatistics(actionType, parameterName);
            if (stats != null && stats.sampleCount > 0)
            {
                inference = InferFromStatistics(inference, stats, context);
            }
            else
            {
                // 无统计数据，使用默认值或规则
                inference = InferFromRules(inference, actionType, parameterName, parameterType, context);
            }

            // 获取推荐范围
            var (min, max) = dependencyGraph.GetRecommendedRange(actionType, parameterName);
            if (min.HasValue) inference.recommendedMin = min.Value;
            if (max.HasValue) inference.recommendedMax = max.Value;

            // 添加参考技能
            if (referenceSkills != null && referenceSkills.Count > 0)
            {
                inference.referenceSkills.AddRange(referenceSkills.Take(3));
            }

            return inference;
        }

        /// <summary>
        /// 基于统计数据推断
        /// </summary>
        private ParameterInference InferFromStatistics(
            ParameterInference inference,
            ParameterStatistics stats,
            SkillContextFeatures context)
        {
            // 推荐值使用中位数
            inference.recommendedValue = stats.median;
            inference.alternativeValues = new List<object>
            {
                stats.percentile25,
                stats.median,
                stats.percentile75
            };

            // 置信度计算：样本量越大越可信
            float sampleConfidence = Mathf.Clamp01(stats.sampleCount / 20f);
            float varianceConfidence = 1f - Mathf.Clamp01(stats.standardDeviation / (stats.max - stats.min + 0.001f));
            inference.confidence = (sampleConfidence * 0.6f + varianceConfidence * 0.4f);

            // 推理理由
            inference.inferenceReason = $"基于{stats.sampleCount}个样本的统计分析，中位数为{stats.median:F2}";

            // 如果置信度低，标注需要人工确认
            if (inference.confidence < 0.7f)
            {
                inference.requiresManualConfirmation = true;
                inference.inferenceReason += $"（置信度{inference.confidence:P0}较低，建议人工确认）";
            }

            return inference;
        }

        /// <summary>
        /// 基于规则推断
        /// </summary>
        private ParameterInference InferFromRules(
            ParameterInference inference,
            string actionType,
            string parameterName,
            Type parameterType,
            SkillContextFeatures context)
        {
            // 获取默认值
            var defaultValue = dependencyGraph.GetDefaultValue(actionType, parameterName);
            if (defaultValue != null)
            {
                inference.recommendedValue = defaultValue;
                inference.confidence = 0.5f;
                inference.inferenceReason = "使用系统默认值";
            }
            else
            {
                // 根据类型设置默认值
                inference.recommendedValue = GetTypeDefaultValue(parameterType);
                inference.confidence = 0.3f;
                inference.inferenceReason = "使用类型默认值（无统计数据）";
                inference.requiresManualConfirmation = true;
            }

            // 对于Unity特殊类型，提供示例值
            if (IsUnitySpecialType(parameterType))
            {
                inference.alternativeValues = GetUnityTypeExamples(parameterType);
            }

            return inference;
        }

        /// <summary>
        /// 检查是否为Unity特殊类型
        /// </summary>
        private bool IsUnitySpecialType(Type type)
        {
            return type == typeof(Vector3) ||
                   type == typeof(Vector2) ||
                   type == typeof(Color) ||
                   type == typeof(AnimationCurve) ||
                   type == typeof(Quaternion);
        }

        /// <summary>
        /// 获取Unity类型的示例值
        /// </summary>
        private List<object> GetUnityTypeExamples(Type type)
        {
            if (type == typeof(Vector3))
            {
                return new List<object>
                {
                    new Vector3(0, 0, 1),   // 向前
                    new Vector3(0, 0, 5),   // 向前5米
                    new Vector3(0, 0, 10)   // 向前10米
                };
            }
            else if (type == typeof(Vector2))
            {
                return new List<object>
                {
                    new Vector2(0, 0),
                    new Vector2(1, 1)
                };
            }
            else if (type == typeof(Color))
            {
                return new List<object>
                {
                    Color.red,
                    Color.yellow,
                    Color.white
                };
            }
            else if (type == typeof(AnimationCurve))
            {
                return new List<object>
                {
                    AnimationCurve.EaseInOut(0, 0, 1, 1),
                    AnimationCurve.Linear(0, 0, 1, 1)
                };
            }

            return new List<object>();
        }

        /// <summary>
        /// 获取类型的默认值
        /// </summary>
        private object GetTypeDefaultValue(Type type)
        {
            if (type == typeof(float)) return 0f;
            if (type == typeof(int)) return 0;
            if (type == typeof(bool)) return false;
            if (type == typeof(string)) return "";
            if (type == typeof(Vector3)) return Vector3.zero;
            if (type == typeof(Vector2)) return Vector2.zero;
            if (type == typeof(Color)) return Color.white;
            if (type == typeof(AnimationCurve)) return AnimationCurve.Linear(0, 0, 1, 1);
            if (type.IsEnum) return Enum.GetValues(type).GetValue(0);

            return null;
        }

        /// <summary>
        /// 查找Action类型
        /// </summary>
        private Type FindActionType(string actionType)
        {
            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (var assembly in assemblies)
            {
                var type = assembly.GetType($"SkillSystem.Actions.{actionType}");
                if (type != null)
                    return type;
            }

            // 尝试不带命名空间的查找
            foreach (var assembly in assemblies)
            {
                foreach (var type in assembly.GetTypes())
                {
                    if (type.Name == actionType)
                        return type;
                }
            }

            return null;
        }

        /// <summary>
        /// 批量推断多个Action的参数
        /// </summary>
        public List<ParameterInferenceResult> InferParametersForActions(
            List<string> actionTypes,
            SkillContextFeatures context)
        {
            var results = new List<ParameterInferenceResult>();

            foreach (var actionType in actionTypes)
            {
                var result = InferParameters(actionType, context);
                results.Add(result);
            }

            return results;
        }
    }

    /// <summary>
    /// 参数推理结果
    /// </summary>
    [Serializable]
    public class ParameterInferenceResult
    {
        public string actionType;
        public DateTime timestamp;
        public List<ParameterInference> parameterInferences = new List<ParameterInference>();
        public ValidationResult validationResult;
    }

    /// <summary>
    /// 单个参数的推理结果
    /// </summary>
    [Serializable]
    public class ParameterInference
    {
        public string parameterName;                        // 参数名
        public string parameterType;                        // 参数类型
        public object recommendedValue;                     // 推荐值
        public List<object> alternativeValues = new List<object>();  // 备选值
        public float confidence;                            // 置信度（0-1）
        public float recommendedMin;                        // 推荐最小值
        public float recommendedMax;                        // 推荐最大值
        public string inferenceReason;                      // 推理理由
        public bool requiresManualConfirmation;             // 是否需要人工确认
        public bool isUnityType;                            // 是否为Unity特殊类型
        public List<string> referenceSkills = new List<string>(); // 参考技能
    }

    /// <summary>
    /// 参数统计缓存 - 存储历史技能的参数统计信息
    /// 在实际应用中应从文件或数据库加载
    /// </summary>
    public class ParameterStatisticsCache
    {
        private Dictionary<string, ParameterStatistics> cache;

        public ParameterStatisticsCache()
        {
            cache = new Dictionary<string, ParameterStatistics>();
            InitializeMockData();
        }

        /// <summary>
        /// 初始化模拟统计数据
        /// </summary>
        private void InitializeMockData()
        {
            // DamageAction.baseDamage 统计
            cache["DamageAction.baseDamage"] = new ParameterStatistics
            {
                actionType = "DamageAction",
                parameterName = "baseDamage",
                sampleCount = 50,
                mean = 150f,
                median = 120f,
                standardDeviation = 80f,
                min = 20f,
                max = 500f,
                percentile25 = 80f,
                percentile75 = 200f
            };

            // MovementAction.movementSpeed 统计
            cache["MovementAction.movementSpeed"] = new ParameterStatistics
            {
                actionType = "MovementAction",
                parameterName = "movementSpeed",
                sampleCount = 30,
                mean = 600f,
                median = 500f,
                standardDeviation = 200f,
                min = 200f,
                max = 1500f,
                percentile25 = 400f,
                percentile75 = 800f
            };

            // HealAction.healAmount 统计
            cache["HealAction.healAmount"] = new ParameterStatistics
            {
                actionType = "HealAction",
                parameterName = "healAmount",
                sampleCount = 25,
                mean = 100f,
                median = 80f,
                standardDeviation = 50f,
                min = 20f,
                max = 300f,
                percentile25 = 60f,
                percentile75 = 120f
            };

            Debug.Log($"[ParameterStatisticsCache] Initialized with {cache.Count} mock statistics");
        }

        /// <summary>
        /// 获取统计信息
        /// </summary>
        public ParameterStatistics GetStatistics(string actionType, string parameterName)
        {
            string key = $"{actionType}.{parameterName}";
            if (cache.ContainsKey(key))
            {
                return cache[key];
            }
            return null;
        }

        /// <summary>
        /// 更新统计信息（用于学习新样本）
        /// </summary>
        public void UpdateStatistics(string actionType, string parameterName, float value)
        {
            string key = $"{actionType}.{parameterName}";
            // TODO: 实现增量统计更新逻辑
        }

        /// <summary>
        /// 从文件加载统计数据
        /// </summary>
        public bool LoadFromFile(string filePath)
        {
            // TODO: 实现从JSON文件加载
            return false;
        }

        /// <summary>
        /// 保存统计数据到文件
        /// </summary>
        public bool SaveToFile(string filePath)
        {
            // TODO: 实现保存到JSON文件
            return false;
        }
    }

    /// <summary>
    /// 参数统计信息
    /// </summary>
    [Serializable]
    public class ParameterStatistics
    {
        public string actionType;
        public string parameterName;
        public int sampleCount;                 // 样本数量
        public float mean;                      // 平均值
        public float median;                    // 中位数
        public float standardDeviation;         // 标准差
        public float min;                       // 最小值
        public float max;                       // 最大值
        public float percentile25;              // 25%分位数（P25）
        public float percentile75;              // 75%分位数（P75）
    }
}
