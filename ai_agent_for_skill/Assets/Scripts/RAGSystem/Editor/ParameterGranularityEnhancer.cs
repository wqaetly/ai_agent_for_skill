using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using SkillSystem.Data;
using Sirenix.Serialization;

namespace SkillSystem.RAG
{
    /// <summary>
    /// 参数粒度增强器 - REQ-02 主门面类
    /// 整合上下文装配、参数推理、依赖验证、类型序列化等功能
    /// 提供完整的参数填充粒度增强服务
    /// </summary>
    public class ParameterGranularityEnhancer
    {
        private static ParameterGranularityEnhancer instance;
        public static ParameterGranularityEnhancer Instance
        {
            get
            {
                if (instance == null)
                {
                    instance = new ParameterGranularityEnhancer();
                }
                return instance;
            }
        }

        private ParameterInferencer inferencer;
        private ActionParameterDependencyGraph dependencyGraph;

        private ParameterGranularityEnhancer()
        {
            inferencer = new ParameterInferencer();
            dependencyGraph = new ActionParameterDependencyGraph();
            Debug.Log("[ParameterGranularityEnhancer] Initialized");
        }

        /// <summary>
        /// 增强Action推荐结果，添加参数推断信息
        /// 这是主要的对外接口
        /// </summary>
        /// <param name="recommendation">RAG推荐的Action</param>
        /// <param name="skillData">技能数据（用于提取上下文）</param>
        /// <returns>增强后的推荐结果，包含参数推断</returns>
        public EnhancedParameterRecommendation EnhanceActionRecommendation(
            EnhancedActionRecommendation recommendation,
            SkillData skillData)
        {
            Debug.Log($"[ParameterGranularityEnhancer] Enhancing action: {recommendation.action_type}");

            // 1. 组装技能上下文
            var context = SkillContextAssembler.AssembleContext(skillData);

            // 2. 推断参数
            var inferenceResult = inferencer.InferParameters(
                recommendation.action_type,
                context,
                recommendation.reference_skills
            );

            // 3. 构建增强结果
            var enhanced = new EnhancedParameterRecommendation
            {
                // 复制原始推荐信息
                actionType = recommendation.action_type,
                displayName = recommendation.display_name,
                category = recommendation.category,
                description = recommendation.description,
                semanticSimilarity = recommendation.semantic_similarity,
                finalScore = recommendation.final_score,

                // 技能上下文
                skillContext = context,

                // 参数推断结果
                parameterInferences = inferenceResult.parameterInferences,

                // 依赖验证结果
                dependencyValidation = inferenceResult.validationResult,

                // 生成时间戳
                timestamp = DateTime.Now
            };

            // 4. 生成Odin友好的输出
            enhanced.odinFriendlyParameters = GenerateOdinOutput(inferenceResult);

            // 5. 生成推荐摘要
            enhanced.recommendationSummary = GenerateSummary(enhanced);

            Debug.Log($"[ParameterGranularityEnhancer] Enhanced with {enhanced.parameterInferences.Count} parameter inferences");

            return enhanced;
        }

        /// <summary>
        /// 批量增强多个Action推荐
        /// </summary>
        public List<EnhancedParameterRecommendation> EnhanceMultipleRecommendations(
            List<EnhancedActionRecommendation> recommendations,
            SkillData skillData)
        {
            var results = new List<EnhancedParameterRecommendation>();

            foreach (var rec in recommendations)
            {
                var enhanced = EnhanceActionRecommendation(rec, skillData);
                results.Add(enhanced);
            }

            return results;
        }

        /// <summary>
        /// 生成Odin友好的参数输出
        /// </summary>
        private Dictionary<string, object> GenerateOdinOutput(ParameterInferenceResult inferenceResult)
        {
            var output = new Dictionary<string, object>();

            foreach (var paramInference in inferenceResult.parameterInferences)
            {
                if (paramInference.recommendedValue == null)
                    continue;

                // Odin原生支持所有Unity类型，直接输出对象即可
                output[paramInference.parameterName] = paramInference.recommendedValue;
            }

            return output;
        }

        /// <summary>
        /// 生成推荐摘要文本
        /// </summary>
        private string GenerateSummary(EnhancedParameterRecommendation enhanced)
        {
            var summary = $"【{enhanced.displayName}】参数推荐\n\n";

            // 高置信度参数
            var highConfidence = enhanced.parameterInferences.Where(p => p.confidence >= 0.7f).ToList();
            if (highConfidence.Count > 0)
            {
                summary += $"✓ 高置信度参数 ({highConfidence.Count}个):\n";
                foreach (var param in highConfidence)
                {
                    var valueStr = FormatParameterValue(param);
                    summary += $"  • {param.parameterName} = {valueStr} (置信度: {param.confidence:P0})\n";
                }
                summary += "\n";
            }

            // 需要确认的参数
            var needsConfirmation = enhanced.parameterInferences.Where(p => p.requiresManualConfirmation).ToList();
            if (needsConfirmation.Count > 0)
            {
                summary += $"⚠ 需要人工确认 ({needsConfirmation.Count}个):\n";
                foreach (var param in needsConfirmation)
                {
                    var valueStr = FormatParameterValue(param);
                    summary += $"  • {param.parameterName} = {valueStr}\n";
                    summary += $"    原因: {param.inferenceReason}\n";
                }
                summary += "\n";
            }

            // 依赖关系警告
            if (enhanced.dependencyValidation != null && enhanced.dependencyValidation.issues.Count > 0)
            {
                summary += $"⚡ 依赖关系提示 ({enhanced.dependencyValidation.issues.Count}个):\n";
                foreach (var issue in enhanced.dependencyValidation.issues)
                {
                    string icon = issue.severity == IssueSeverity.Error ? "❌" : "⚠";
                    summary += $"  {icon} {issue.message}\n";
                }
                summary += "\n";
            }

            return summary;
        }

        /// <summary>
        /// 格式化参数值显示
        /// </summary>
        private string FormatParameterValue(ParameterInference param)
        {
            if (param.recommendedValue == null)
                return "null";

            if (param.isUnityType)
            {
                // Unity类型使用原生ToString()，已经足够清晰
                var value = param.recommendedValue;

                // 针对特殊类型添加语义化描述
                if (value is Vector3 v3)
                {
                    string desc = v3.ToString("F2");
                    if (v3 == Vector3.zero) desc += " [原点]";
                    else if (v3 == Vector3.forward) desc += " [向前]";
                    else if (v3 == Vector3.up) desc += " [向上]";
                    return desc;
                }
                else if (value is Color color)
                {
                    string desc = $"RGBA({color.r:F2}, {color.g:F2}, {color.b:F2}, {color.a:F2})";
                    if (color == Color.red) desc += " [红色]";
                    else if (color == Color.blue) desc += " [蓝色]";
                    else if (color == Color.green) desc += " [绿色]";
                    return desc;
                }
                else if (value is Quaternion q)
                {
                    return $"Euler{q.eulerAngles.ToString("F1")}";
                }

                return value.ToString();
            }

            return param.recommendedValue.ToString();
        }

        /// <summary>
        /// 获取参数的依赖关系报告
        /// </summary>
        public string GetDependencyReport(string actionType)
        {
            return dependencyGraph.GenerateDependencyReport(actionType);
        }

        /// <summary>
        /// 验证参数配置
        /// </summary>
        public ValidationResult ValidateParameters(string actionType, Dictionary<string, object> parameters)
        {
            return dependencyGraph.ValidateParameters(actionType, parameters);
        }

        /// <summary>
        /// 获取参数推荐的详细说明
        /// </summary>
        public string GetParameterRecommendationDetail(ParameterInference param)
        {
            var detail = $"参数: {param.parameterName}\n";
            detail += $"类型: {param.parameterType}\n";
            detail += $"推荐值: {FormatParameterValue(param)}\n";
            detail += $"置信度: {param.confidence:P0}\n";

            if (param.alternativeValues.Count > 0)
            {
                detail += "\n备选值:\n";
                foreach (var altValue in param.alternativeValues)
                {
                    detail += $"  • {altValue}\n";
                }
            }

            if (!string.IsNullOrEmpty(param.inferenceReason))
            {
                detail += $"\n推理依据: {param.inferenceReason}\n";
            }

            if (param.referenceSkills.Count > 0)
            {
                detail += $"\n参考技能: {string.Join(", ", param.referenceSkills)}\n";
            }

            return detail;
        }

        /// <summary>
        /// 导出推荐结果为JSON（用于外部工具）
        /// 使用Odin Serializer与SkillDataSerializer保持一致
        /// </summary>
        public string ExportToJson(EnhancedParameterRecommendation enhanced)
        {
            if (enhanced == null)
            {
                Debug.LogError("Cannot export null recommendation!");
                return string.Empty;
            }

            try
            {
                byte[] bytes = SerializationUtility.SerializeValue(enhanced, DataFormat.JSON);
                return System.Text.Encoding.UTF8.GetString(bytes);
            }
            catch (Exception e)
            {
                Debug.LogError($"Failed to export recommendation: {e.Message}");
                return string.Empty;
            }
        }

        /// <summary>
        /// 批量导出推荐结果为JSON
        /// </summary>
        public string ExportMultipleToJson(List<EnhancedParameterRecommendation> recommendations)
        {
            if (recommendations == null || recommendations.Count == 0)
            {
                Debug.LogError("Cannot export empty recommendations!");
                return string.Empty;
            }

            try
            {
                byte[] bytes = SerializationUtility.SerializeValue(recommendations, DataFormat.JSON);
                return System.Text.Encoding.UTF8.GetString(bytes);
            }
            catch (Exception e)
            {
                Debug.LogError($"Failed to export recommendations: {e.Message}");
                return string.Empty;
            }
        }

        /// <summary>
        /// 健康检查
        /// </summary>
        public bool HealthCheck(out string message)
        {
            try
            {
                if (inferencer == null || dependencyGraph == null)
                {
                    message = "组件未初始化";
                    return false;
                }

                message = "参数粒度增强器运行正常";
                return true;
            }
            catch (Exception e)
            {
                message = $"错误: {e.Message}";
                return false;
            }
        }
    }

    /// <summary>
    /// 增强的参数推荐结果
    /// 包含完整的参数推理、依赖验证、上下文信息
    /// </summary>
    [Serializable]
    public class EnhancedParameterRecommendation
    {
        // 基础Action信息
        public string actionType;
        public string displayName;
        public string category;
        public string description;

        // 评分信息
        public float semanticSimilarity;
        public float finalScore;

        // 技能上下文
        public SkillContextFeatures skillContext;

        // 参数推断结果
        public List<ParameterInference> parameterInferences = new List<ParameterInference>();

        // 依赖验证结果
        public ValidationResult dependencyValidation;

        // Odin友好的输出
        public Dictionary<string, object> odinFriendlyParameters = new Dictionary<string, object>();

        // 推荐摘要
        public string recommendationSummary;

        // 时间戳
        public DateTime timestamp;

        /// <summary>
        /// 获取高置信度参数数量
        /// </summary>
        public int GetHighConfidenceParameterCount()
        {
            return parameterInferences.Count(p => p.confidence >= 0.7f);
        }

        /// <summary>
        /// 获取需要人工确认的参数数量
        /// </summary>
        public int GetManualConfirmationCount()
        {
            return parameterInferences.Count(p => p.requiresManualConfirmation);
        }

        /// <summary>
        /// 是否通过验证
        /// </summary>
        public bool IsValid()
        {
            return dependencyValidation == null || dependencyValidation.isValid;
        }
    }
}
