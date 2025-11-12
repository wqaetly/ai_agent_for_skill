using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Action推荐评分系统
    /// 实现综合评分：语义相似度 + 业务优先�?    /// </summary>
    public class ActionRecommendationScorer
    {
        private ActionSemanticRegistry registry;
        private ActionConstraintValidator validator;

        // 评分权重配置
        public float semanticWeight = 0.7f;       // 语义相似度权�?        public float businessWeight = 0.3f;        // 业务优先级权�?
        public ActionRecommendationScorer()
        {
            registry = ActionSemanticRegistry.Instance;
            validator = new ActionConstraintValidator();
        }

        /// <summary>
        /// 对推荐列表进行增强评�?        /// </summary>
        /// <param name="recommendations">原始推荐列表</param>
        /// <param name="context">查询上下�?/param>
        /// <param name="existingActions">已存在的Action类型（用于约束检查）</param>
        /// <returns>增强后的推荐列表</returns>
        public List<EnhancedActionRecommendation> ScoreRecommendations(
            List<EditorRAGClient.ActionRecommendation> recommendations,
            string context,
            List<string> existingActions = null)
        {
            var enhanced = new List<EnhancedActionRecommendation>();

            if (recommendations == null || recommendations.Count == 0)
            {
                return enhanced;
            }

            foreach (var rec in recommendations)
            {
                var enhancedRec = new EnhancedActionRecommendation
                {
                    action_type = rec.action_type,
                    display_name = rec.display_name,
                    category = rec.category,
                    description = rec.description,
                    semantic_similarity = rec.semantic_similarity
                };

                // 计算业务得分
                enhancedRec.business_score = CalculateBusinessScore(rec.action_type);

                // 计算最终得�?                enhancedRec.final_score = CalculateFinalScore(
                    rec.semantic_similarity,
                    enhancedRec.business_score);

                // 约束验证
                ValidateRecommendation(enhancedRec, context, existingActions);

                enhanced.Add(enhancedRec);
            }

            // 按最终得分排�?            enhanced = enhanced.OrderByDescending(e => e.final_score).ToList();

            return enhanced;
        }

        /// <summary>
        /// 计算业务优先级得�?        /// </summary>
        private float CalculateBusinessScore(string actionType)
        {
            var semanticInfo = registry.GetSemanticInfo(actionType);
            if (semanticInfo != null)
            {
                return semanticInfo.businessPriority;
            }

            return 1.0f; // 默认优先�?        }

        /// <summary>
        /// 计算最终综合得�?        /// 公式：语义相似度 × 语义权重 + 业务优先�?× 业务权重
        /// </summary>
        private float CalculateFinalScore(float semanticSimilarity, float businessScore)
        {
            // 语义部分
            float semanticPart = semanticSimilarity * semanticWeight;

            // 业务部分：归一化到0-1范围后应用权�?            float businessPart = (businessScore / 2f) * businessWeight; // businessPriority范围�?-2

            float finalScore = semanticPart + businessPart;

            return Mathf.Clamp01(finalScore);
        }

        /// <summary>
        /// 验证推荐的合理�?        /// </summary>
        private void ValidateRecommendation(
            EnhancedActionRecommendation recommendation,
            string context,
            List<string> existingActions)
        {
            // 单独验证
            var issues = new List<string>();
            bool isValid = validator.ValidateSingle(recommendation.action_type, context, out issues);
            recommendation.validation_issues.AddRange(issues);

            // 如果有已存在的Action，检查组合约�?            if (existingActions != null && existingActions.Count > 0)
            {
                var combinedActions = new List<string>(existingActions) { recommendation.action_type };
                var combinationIssues = new List<string>();
                bool combinationValid = validator.ValidateCombination(combinedActions, out combinationIssues);

                if (!combinationValid)
                {
                    recommendation.validation_issues.AddRange(combinationIssues);
                    isValid = false;
                }
            }

            recommendation.is_valid = isValid;

            // 如果验证失败，降低得�?            if (!isValid)
            {
                recommendation.final_score *= 0.5f; // 惩罚系数
            }
        }

        /// <summary>
        /// 过滤并重排推荐列�?        /// </summary>
        /// <param name="recommendations">增强推荐列表</param>
        /// <param name="filterInvalid">是否过滤掉无效推�?/param>
        /// <param name="maxResults">最大返回数�?/param>
        /// <returns>过滤后的推荐列表</returns>
        public List<EnhancedActionRecommendation> FilterAndRank(
            List<EnhancedActionRecommendation> recommendations,
            bool filterInvalid = false,
            int maxResults = 5)
        {
            var filtered = recommendations;

            // 过滤无效推荐
            if (filterInvalid)
            {
                filtered = filtered.Where(r => r.is_valid).ToList();
            }

            // 按最终得分排�?            filtered = filtered.OrderByDescending(r => r.final_score).ToList();

            // 限制返回数量
            if (maxResults > 0 && filtered.Count > maxResults)
            {
                filtered = filtered.Take(maxResults).ToList();
            }

            // 计算互斥比例（用于验收标准）
            float exclusiveRatio = CalculateExclusiveRatio(filtered);
            Debug.Log($"[ActionRecommendationScorer] Exclusive ratio in top-{filtered.Count}: {exclusiveRatio:P1}");

            return filtered;
        }

        /// <summary>
        /// 计算推荐列表中的互斥比例
        /// </summary>
        private float CalculateExclusiveRatio(List<EnhancedActionRecommendation> recommendations)
        {
            if (recommendations.Count <= 1)
            {
                return 0f;
            }

            int exclusiveCount = 0;
            int totalPairs = 0;

            for (int i = 0; i < recommendations.Count; i++)
            {
                for (int j = i + 1; j < recommendations.Count; j++)
                {
                    totalPairs++;

                    var actionTypes = new List<string>
                    {
                        recommendations[i].action_type,
                        recommendations[j].action_type
                    };

                    var issues = new List<string>();
                    bool isValid = validator.ValidateCombination(actionTypes, out issues);

                    if (!isValid && issues.Any(issue => issue.Contains("互斥")))
                    {
                        exclusiveCount++;
                    }
                }
            }

            return totalPairs > 0 ? (float)exclusiveCount / totalPairs : 0f;
        }

        /// <summary>
        /// 调整评分权重
        /// </summary>
        public void SetWeights(float semanticWeight, float businessWeight)
        {
            // 归一化权�?            float total = semanticWeight + businessWeight;
            if (total > 0)
            {
                this.semanticWeight = semanticWeight / total;
                this.businessWeight = businessWeight / total;
            }
        }

        /// <summary>
        /// 获取推荐统计信息
        /// </summary>
        public Dictionary<string, object> GetStatistics(List<EnhancedActionRecommendation> recommendations)
        {
            var stats = new Dictionary<string, object>();

            if (recommendations == null || recommendations.Count == 0)
            {
                return stats;
            }

            stats["total_count"] = recommendations.Count;
            stats["valid_count"] = recommendations.Count(r => r.is_valid);
            stats["invalid_count"] = recommendations.Count(r => !r.is_valid);
            stats["avg_semantic_similarity"] = recommendations.Average(r => r.semantic_similarity);
            stats["avg_final_score"] = recommendations.Average(r => r.final_score);
            stats["avg_business_score"] = recommendations.Average(r => r.business_score);
            stats["exclusive_ratio"] = CalculateExclusiveRatio(recommendations);

            return stats;
        }
    }
}
