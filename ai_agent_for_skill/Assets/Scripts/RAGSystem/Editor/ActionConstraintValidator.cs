using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Action组合约束校验�?    /// 负责检查Action推荐的合理性，包括互斥关系、前置依赖等
    /// </summary>
    public class ActionConstraintValidator
    {
        private ActionSemanticRegistry registry;

        public ActionConstraintValidator()
        {
            registry = ActionSemanticRegistry.Instance;
        }

        /// <summary>
        /// 验证单个Action推荐是否合理
        /// </summary>
        /// <param name="actionType">被验证的Action类型</param>
        /// <param name="context">上下文描�?/param>
        /// <param name="issues">输出：验证问题列�?/param>
        /// <returns>是否通过验证</returns>
        public bool ValidateSingle(string actionType, string context, out List<string> issues)
        {
            issues = new List<string>();

            var semanticInfo = registry.GetSemanticInfo(actionType);
            if (semanticInfo == null)
            {
                // 没有语义信息的Action，降级为通过（向后兼容）
                return true;
            }

            // 检查是否匹配上下文意图
            if (!string.IsNullOrEmpty(context))
            {
                bool matchesIntent = CheckIntentMatch(semanticInfo, context);
                if (!matchesIntent)
                {
                    issues.Add($"Action意图可能与查询不匹配");
                }
            }

            return issues.Count == 0;
        }

        /// <summary>
        /// 验证Action组合是否合理
        /// </summary>
        /// <param name="actionTypes">Action类型列表</param>
        /// <param name="issues">输出：验证问题列�?/param>
        /// <returns>是否通过验证</returns>
        public bool ValidateCombination(List<string> actionTypes, out List<string> issues)
        {
            issues = new List<string>();

            if (actionTypes == null || actionTypes.Count == 0)
            {
                return true;
            }

            // 检查互斥规�?            CheckExclusiveRules(actionTypes, issues);

            // 检查前置依�?            CheckPrerequisites(actionTypes, issues);

            // 检查Action间的语义依赖
            CheckSemanticDependencies(actionTypes, issues);

            return issues.Count == 0;
        }

        /// <summary>
        /// 检查推荐列表中的互斥问�?        /// </summary>
        /// <param name="recommendations">推荐列表</param>
        /// <returns>过滤后的推荐列表</returns>
        public List<EditorRAGClient.ActionRecommendation> FilterExclusiveActions(
            List<EditorRAGClient.ActionRecommendation> recommendations)
        {
            if (recommendations == null || recommendations.Count <= 1)
            {
                return recommendations;
            }

            var filtered = new List<EditorRAGClient.ActionRecommendation>();
            var actionTypes = new List<string>();

            foreach (var recommendation in recommendations)
            {
                bool isExclusive = false;

                // 检查与已添加的Action是否互斥
                foreach (var existingType in actionTypes)
                {
                    if (AreActionsExclusive(recommendation.action_type, existingType))
                    {
                        Debug.Log($"[ActionConstraintValidator] Filtered exclusive action: {recommendation.action_type} (conflicts with {existingType})");
                        isExclusive = true;
                        break;
                    }
                }

                if (!isExclusive)
                {
                    filtered.Add(recommendation);
                    actionTypes.Add(recommendation.action_type);
                }
            }

            return filtered;
        }

        /// <summary>
        /// 检查两个Action是否互斥
        /// </summary>
        private bool AreActionsExclusive(string actionType1, string actionType2)
        {
            // 检查规则表中的互斥规则
            var exclusiveRules = registry.GetRulesByType("Exclusive");
            foreach (var rule in exclusiveRules)
            {
                if (rule.actionTypes.Contains(actionType1) && rule.actionTypes.Contains(actionType2))
                {
                    return true;
                }
            }

            // 检查语义依赖中的互斥关�?            var semantic1 = registry.GetSemanticInfo(actionType1);
            if (semantic1?.dependency?.incompatibles != null &&
                semantic1.dependency.incompatibles.Contains(actionType2))
            {
                return true;
            }

            var semantic2 = registry.GetSemanticInfo(actionType2);
            if (semantic2?.dependency?.incompatibles != null &&
                semantic2.dependency.incompatibles.Contains(actionType1))
            {
                return true;
            }

            return false;
        }

        /// <summary>
        /// 检查互斥规�?        /// </summary>
        private void CheckExclusiveRules(List<string> actionTypes, List<string> issues)
        {
            var exclusiveRules = registry.GetRulesByType("Exclusive");

            foreach (var rule in exclusiveRules)
            {
                // 统计规则中涉及的Action有多少个出现在列表中
                int matchCount = actionTypes.Count(at => rule.actionTypes.Contains(at));

                if (matchCount > 1)
                {
                    string actionList = string.Join(", ", actionTypes.Where(at => rule.actionTypes.Contains(at)));
                    issues.Add($"互斥冲突：{actionList} - {rule.description}");
                }
            }
        }

        /// <summary>
        /// 检查前置依�?        /// </summary>
        private void CheckPrerequisites(List<string> actionTypes, List<string> issues)
        {
            foreach (var actionType in actionTypes)
            {
                var semanticInfo = registry.GetSemanticInfo(actionType);
                if (semanticInfo?.dependency?.prerequisites != null)
                {
                    foreach (var prerequisite in semanticInfo.dependency.prerequisites)
                    {
                        if (!actionTypes.Contains(prerequisite))
                        {
                            issues.Add($"{actionType}缺少前置Action：{prerequisite}");
                        }
                    }
                }
            }
        }

        /// <summary>
        /// 检查语义依�?        /// </summary>
        private void CheckSemanticDependencies(List<string> actionTypes, List<string> issues)
        {
            // 检查每对Action的语义兼容�?            for (int i = 0; i < actionTypes.Count; i++)
            {
                for (int j = i + 1; j < actionTypes.Count; j++)
                {
                    var semantic1 = registry.GetSemanticInfo(actionTypes[i]);
                    var semantic2 = registry.GetSemanticInfo(actionTypes[j]);

                    if (semantic1 != null && semantic2 != null)
                    {
                        // 检查互�?                        if (semantic1.dependency?.incompatibles != null &&
                            semantic1.dependency.incompatibles.Contains(actionTypes[j]))
                        {
                            issues.Add($"{actionTypes[i]}与{actionTypes[j]}互斥");
                        }
                    }
                }
            }
        }

        /// <summary>
        /// 检查意图匹�?        /// </summary>
        private bool CheckIntentMatch(ActionSemanticInfo semanticInfo, string context)
        {
            if (semanticInfo.purpose?.keywords == null || semanticInfo.purpose.keywords.Count == 0)
            {
                return true; // 没有关键词约束，默认匹配
            }

            string lowerContext = context.ToLower();

            // 检查关键词是否在上下文中出�?            foreach (var keyword in semanticInfo.purpose.keywords)
            {
                if (lowerContext.Contains(keyword.ToLower()))
                {
                    return true;
                }
            }

            // 检查意图标�?            if (semanticInfo.purpose.intents != null)
            {
                foreach (var intent in semanticInfo.purpose.intents)
                {
                    if (lowerContext.Contains(intent.ToLower()))
                    {
                        return true;
                    }
                }
            }

            return false; // 没有匹配的关键词或意�?        }

        /// <summary>
        /// 获取协同推荐
        /// </summary>
        /// <param name="actionType">当前Action类型</param>
        /// <returns>推荐的协同Action列表</returns>
        public List<string> GetSynergyRecommendations(string actionType)
        {
            var recommendations = new List<string>();

            var semanticInfo = registry.GetSemanticInfo(actionType);
            if (semanticInfo?.dependency?.synergies != null)
            {
                recommendations.AddRange(semanticInfo.dependency.synergies);
            }

            // 从规则中查找协同关系
            var synergyRules = registry.GetRulesByType("Synergy");
            foreach (var rule in synergyRules)
            {
                if (rule.actionTypes.Contains(actionType))
                {
                    recommendations.AddRange(rule.actionTypes.Where(at => at != actionType));
                }
            }

            return recommendations.Distinct().ToList();
        }

        /// <summary>
        /// 获取后续推荐
        /// </summary>
        public List<string> GetFollowUpRecommendations(string actionType)
        {
            var semanticInfo = registry.GetSemanticInfo(actionType);
            return semanticInfo?.dependency?.followUps ?? new List<string>();
        }
    }
}
