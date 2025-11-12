using System.Collections.Generic;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Action推荐增强服务 - 整合所有增强功能的门面�?    /// 提供一站式的推荐增强、评分、验证和解释生成服务
    /// </summary>
    public class ActionRecommendationEnhancer
    {
        private static ActionRecommendationEnhancer instance;
        public static ActionRecommendationEnhancer Instance
        {
            get
            {
                if (instance == null)
                {
                    instance = new ActionRecommendationEnhancer();
                }
                return instance;
            }
        }

        private ActionSemanticRegistry registry;
        private ActionConstraintValidator validator;
        private ActionRecommendationScorer scorer;
        private ActionRecommendationExplainer explainer;

        private ActionRecommendationEnhancer()
        {
            registry = ActionSemanticRegistry.Instance;
            validator = new ActionConstraintValidator();
            scorer = new ActionRecommendationScorer();
            explainer = new ActionRecommendationExplainer();
        }

        /// <summary>
        /// 增强推荐列表 - 主要入口方法
        /// </summary>
        /// <param name="recommendations">原始RAG推荐列表</param>
        /// <param name="context">查询上下�?/param>
        /// <param name="existingActions">已存在的Action类型</param>
        /// <param name="filterInvalid">是否过滤无效推荐</param>
        /// <param name="maxResults">最大返回数�?/param>
        /// <returns>增强后的推荐列表</returns>
        public List<EnhancedActionRecommendation> EnhanceRecommendations(
            List<EditorRAGClient.ActionRecommendation> recommendations,
            string context,
            List<string> existingActions = null,
            bool filterInvalid = false,
            int maxResults = 5)
        {
            if (recommendations == null || recommendations.Count == 0)
            {
                Debug.LogWarning("[ActionRecommendationEnhancer] No recommendations to enhance");
                return new List<EnhancedActionRecommendation>();
            }

            Debug.Log($"[ActionRecommendationEnhancer] Enhancing {recommendations.Count} recommendations");

            // 步骤1：评分和验证
            var enhanced = scorer.ScoreRecommendations(recommendations, context, existingActions);
            Debug.Log($"[ActionRecommendationEnhancer] Scored {enhanced.Count} recommendations");

            // 步骤2：生成解�?            foreach (var rec in enhanced)
            {
                explainer.GenerateExplanation(rec, context, existingActions);
            }
            Debug.Log($"[ActionRecommendationEnhancer] Generated explanations for all recommendations");

            // 步骤3：过滤和排序
            var filtered = scorer.FilterAndRank(enhanced, filterInvalid, maxResults);
            Debug.Log($"[ActionRecommendationEnhancer] Filtered to {filtered.Count} recommendations");

            // 步骤4：输出统计信�?            var stats = scorer.GetStatistics(filtered);
            LogStatistics(stats);

            return filtered;
        }

        /// <summary>
        /// 快速过滤互斥Action（用于实时推荐）
        /// </summary>
        public List<EditorRAGClient.ActionRecommendation> QuickFilterExclusive(
            List<EditorRAGClient.ActionRecommendation> recommendations)
        {
            return validator.FilterExclusiveActions(recommendations);
        }

        /// <summary>
        /// 验证Action组合的合理�?        /// </summary>
        public bool ValidateActionCombination(List<string> actionTypes, out List<string> issues)
        {
            return validator.ValidateCombination(actionTypes, out issues);
        }

        /// <summary>
        /// 获取协同推荐
        /// </summary>
        public List<string> GetSynergyRecommendations(string actionType)
        {
            return validator.GetSynergyRecommendations(actionType);
        }

        /// <summary>
        /// 获取后续推荐
        /// </summary>
        public List<string> GetFollowUpRecommendations(string actionType)
        {
            return validator.GetFollowUpRecommendations(actionType);
        }

        /// <summary>
        /// 重新加载配置
        /// </summary>
        public bool ReloadConfiguration()
        {
            Debug.Log("[ActionRecommendationEnhancer] Reloading configuration...");
            return registry.ReloadConfig();
        }

        /// <summary>
        /// 获取配置路径
        /// </summary>
        public string GetConfigPath()
        {
            return registry.GetConfigPath();
        }

        /// <summary>
        /// 调整评分权重
        /// </summary>
        public void SetScoringWeights(float semanticWeight, float businessWeight)
        {
            scorer.SetWeights(semanticWeight, businessWeight);
            Debug.Log($"[ActionRecommendationEnhancer] Updated weights: semantic={semanticWeight:F2}, business={businessWeight:F2}");
        }

        /// <summary>
        /// 生成推荐摘要文本
        /// </summary>
        public string GenerateSummary(EnhancedActionRecommendation recommendation)
        {
            return explainer.GenerateSummaryText(recommendation);
        }

        /// <summary>
        /// 输出统计信息到日�?        /// </summary>
        private void LogStatistics(Dictionary<string, object> stats)
        {
            if (stats == null || stats.Count == 0)
            {
                return;
            }

            Debug.Log("=== Action Recommendation Statistics ===");
            foreach (var kvp in stats)
            {
                string valueStr;
                if (kvp.Value is float f)
                {
                    valueStr = f.ToString("F4");
                }
                else if (kvp.Value is double d)
                {
                    valueStr = d.ToString("F4");
                }
                else
                {
                    valueStr = kvp.Value.ToString();
                }

                Debug.Log($"  {kvp.Key}: {valueStr}");
            }
            Debug.Log("========================================");
        }

        /// <summary>
        /// 获取Action语义信息（调试用�?        /// </summary>
        public ActionSemanticInfo GetSemanticInfo(string actionType)
        {
            return registry.GetSemanticInfo(actionType);
        }

        /// <summary>
        /// 获取所有已注册的Action
        /// </summary>
        public List<ActionSemanticInfo> GetAllRegisteredActions()
        {
            return registry.GetAllSemanticInfo();
        }

        /// <summary>
        /// 健康检�?- 验证所有组件是否正常工�?        /// </summary>
        public bool HealthCheck(out string message)
        {
            try
            {
                // 检查注册表
                var actions = registry.GetAllSemanticInfo();
                var rules = registry.GetEnabledRules();

                if (actions.Count == 0)
                {
                    message = "Warning: No semantic info registered. Default config may need to be created.";
                    return true; // 不算错误，只是警�?                }

                // 检查各组件
                if (validator == null || scorer == null || explainer == null)
                {
                    message = "Error: One or more components not initialized";
                    return false;
                }

                message = $"OK: {actions.Count} actions, {rules.Count} rules registered";
                return true;
            }
            catch (System.Exception e)
            {
                message = $"Error: {e.Message}";
                return false;
            }
        }
    }
}
