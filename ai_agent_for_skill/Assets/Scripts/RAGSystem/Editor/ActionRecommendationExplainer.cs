using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Action推荐解释生成�?    /// 为每个推荐生成可读的理由、警告和建议
    /// </summary>
    public class ActionRecommendationExplainer
    {
        private ActionSemanticRegistry registry;
        private ActionConstraintValidator validator;

        // 相似度阈值配�?        private const float HIGH_SIMILARITY_THRESHOLD = 0.7f;
        private const float MEDIUM_SIMILARITY_THRESHOLD = 0.4f;

        public ActionRecommendationExplainer()
        {
            registry = ActionSemanticRegistry.Instance;
            validator = new ActionConstraintValidator();
        }

        /// <summary>
        /// 为推荐生成完整解�?        /// </summary>
        public void GenerateExplanation(
            EnhancedActionRecommendation recommendation,
            string context,
            List<string> existingActions = null)
        {
            // 清空现有解释
            recommendation.reasons.Clear();
            recommendation.warnings.Clear();
            recommendation.suggestions.Clear();
            recommendation.reference_skills.Clear();

            // 生成推荐理由
            GenerateReasons(recommendation, context);

            // 生成警告信息
            GenerateWarnings(recommendation, existingActions);

            // 生成使用建议
            GenerateSuggestions(recommendation, existingActions);

            // 添加参考技�?            GenerateReferenceSkills(recommendation);
        }

        /// <summary>
        /// 生成推荐理由
        /// </summary>
        private void GenerateReasons(EnhancedActionRecommendation recommendation, string context)
        {
            var semanticInfo = registry.GetSemanticInfo(recommendation.action_type);

            // 理由1：语义相似度
            if (recommendation.semantic_similarity >= HIGH_SIMILARITY_THRESHOLD)
            {
                recommendation.reasons.Add($"高语义相似度（{recommendation.semantic_similarity:P0}），非常匹配查询意图");
            }
            else if (recommendation.semantic_similarity >= MEDIUM_SIMILARITY_THRESHOLD)
            {
                recommendation.reasons.Add($"中等语义相似度（{recommendation.semantic_similarity:P0}），基本匹配查询意图");
            }
            else
            {
                recommendation.reasons.Add($"低语义相似度（{recommendation.semantic_similarity:P0}），可能不完全匹配查询意�?);
            }

            // 理由2：分类匹�?            if (semanticInfo != null)
            {
                string categoryDesc = GetCategoryDescription(semanticInfo.category);
                if (!string.IsNullOrEmpty(categoryDesc))
                {
                    recommendation.reasons.Add($"属于{categoryDesc}，{GetCategoryUsage(semanticInfo.category)}");
                }

                // 理由3：关键词匹配
                if (semanticInfo.purpose?.keywords != null && !string.IsNullOrEmpty(context))
                {
                    var matchedKeywords = semanticInfo.purpose.keywords
                        .Where(k => context.ToLower().Contains(k.ToLower()))
                        .ToList();

                    if (matchedKeywords.Count > 0)
                    {
                        recommendation.reasons.Add($"匹配关键词：{string.Join("�?, matchedKeywords)}");
                    }
                }

                // 理由4：业务优先级
                if (semanticInfo.businessPriority > 1.0f)
                {
                    recommendation.reasons.Add($"该Action具有较高业务优先级（{semanticInfo.businessPriority:F1}），推荐使用");
                }

                // 理由5：协同效�?                if (semanticInfo.dependency?.synergies != null && semanticInfo.dependency.synergies.Count > 0)
                {
                    var synergyNames = semanticInfo.dependency.synergies
                        .Select(s => GetActionDisplayName(s))
                        .Where(n => !string.IsNullOrEmpty(n))
                        .ToList();

                    if (synergyNames.Count > 0)
                    {
                        recommendation.reasons.Add($"可与{string.Join("�?, synergyNames)}协同使用");
                    }
                }
            }

            // 如果没有生成任何理由，添加默认理�?            if (recommendation.reasons.Count == 0)
            {
                recommendation.reasons.Add("基于语义检索推�?);
            }
        }

        /// <summary>
        /// 生成警告信息
        /// </summary>
        private void GenerateWarnings(EnhancedActionRecommendation recommendation, List<string> existingActions)
        {
            var semanticInfo = registry.GetSemanticInfo(recommendation.action_type);

            // 警告1：验证问�?            if (recommendation.validation_issues != null && recommendation.validation_issues.Count > 0)
            {
                foreach (var issue in recommendation.validation_issues)
                {
                    recommendation.warnings.Add($"�?{issue}");
                }
            }

            // 警告2：互斥关�?            if (existingActions != null && existingActions.Count > 0 && semanticInfo != null)
            {
                var incompatibles = semanticInfo.dependency?.incompatibles ?? new List<string>();
                var conflicts = existingActions.Where(ea => incompatibles.Contains(ea)).ToList();

                if (conflicts.Count > 0)
                {
                    var conflictNames = conflicts.Select(c => GetActionDisplayName(c)).Where(n => !string.IsNullOrEmpty(n));
                    recommendation.warnings.Add($"�?与已有Action存在互斥：{string.Join("�?, conflictNames)}");
                }
            }

            // 警告3：缺少前�?            if (semanticInfo?.dependency?.prerequisites != null && semanticInfo.dependency.prerequisites.Count > 0)
            {
                var missingPrereqs = semanticInfo.dependency.prerequisites;
                if (existingActions != null)
                {
                    missingPrereqs = missingPrereqs.Where(p => !existingActions.Contains(p)).ToList();
                }

                if (missingPrereqs.Count > 0)
                {
                    var prereqNames = missingPrereqs.Select(p => GetActionDisplayName(p)).Where(n => !string.IsNullOrEmpty(n));
                    recommendation.warnings.Add($"�?建议先添加：{string.Join("�?, prereqNames)}");
                }
            }

            // 警告4：低相似�?            if (recommendation.semantic_similarity < MEDIUM_SIMILARITY_THRESHOLD)
            {
                recommendation.warnings.Add("�?语义相似度较低，请确认是否符合需�?);
            }
        }

        /// <summary>
        /// 生成使用建议
        /// </summary>
        private void GenerateSuggestions(EnhancedActionRecommendation recommendation, List<string> existingActions)
        {
            var semanticInfo = registry.GetSemanticInfo(recommendation.action_type);

            if (semanticInfo == null)
            {
                return;
            }

            // 建议1：协同Action
            var synergyRecommendations = validator.GetSynergyRecommendations(recommendation.action_type);
            if (synergyRecommendations.Count > 0)
            {
                var suggestions = synergyRecommendations
                    .Select(s => GetActionDisplayName(s))
                    .Where(n => !string.IsNullOrEmpty(n))
                    .Take(3)
                    .ToList();

                if (suggestions.Count > 0)
                {
                    recommendation.suggestions.Add($"💡 推荐搭配：{string.Join("�?, suggestions)}");
                }
            }

            // 建议2：后续Action
            var followUps = validator.GetFollowUpRecommendations(recommendation.action_type);
            if (followUps.Count > 0)
            {
                var followUpNames = followUps
                    .Select(f => GetActionDisplayName(f))
                    .Where(n => !string.IsNullOrEmpty(n))
                    .Take(2)
                    .ToList();

                if (followUpNames.Count > 0)
                {
                    recommendation.suggestions.Add($"💡 后续可添加：{string.Join("�?, followUpNames)}");
                }
            }

            // 建议3：使用场�?            if (semanticInfo.purpose?.scenarios != null && semanticInfo.purpose.scenarios.Count > 0)
            {
                var scenariosText = string.Join("�?, semanticInfo.purpose.scenarios.Take(3));
                recommendation.suggestions.Add($"💡 适用场景：{scenariosText}");
            }

            // 建议4：参数配置提�?            AddParameterSuggestions(recommendation);
        }

        /// <summary>
        /// 添加参数配置建议
        /// </summary>
        private void AddParameterSuggestions(EnhancedActionRecommendation recommendation)
        {
            switch (recommendation.action_type)
            {
                case "DamageAction":
                    recommendation.suggestions.Add("💡 注意配置：伤害类型、伤害值、目标筛�?);
                    break;
                case "MovementAction":
                    recommendation.suggestions.Add("💡 注意配置：移动类型、移动速度、目标位�?);
                    break;
                case "ShieldAction":
                    recommendation.suggestions.Add("💡 注意配置：护盾类型、护盾值、持续时�?);
                    break;
                case "HealAction":
                    recommendation.suggestions.Add("💡 注意配置：治疗值、目标筛选、是否瞬时生�?);
                    break;
                case "ControlAction":
                    recommendation.suggestions.Add("💡 注意配置：控制类型、持续时间、是否可被打�?);
                    break;
                case "BuffAction":
                    recommendation.suggestions.Add("💡 注意配置：Buff类型、属性加成、持续时间、是否可叠加");
                    break;
            }
        }

        /// <summary>
        /// 生成参考技能示�?        /// </summary>
        private void GenerateReferenceSkills(EnhancedActionRecommendation recommendation)
        {
            // 这里可以从技能数据库中查询使用了该Action的技能作为参�?            // 当前先添加一些通用的参考说�?            var semanticInfo = registry.GetSemanticInfo(recommendation.action_type);

            if (semanticInfo?.purpose?.scenarios != null && semanticInfo.purpose.scenarios.Count > 0)
            {
                // 基于场景推荐参考技�?                foreach (var scenario in semanticInfo.purpose.scenarios.Take(2))
                {
                    recommendation.reference_skills.Add($"参考{scenario}的实现方�?);
                }
            }
        }

        /// <summary>
        /// 获取分类描述
        /// </summary>
        private string GetCategoryDescription(string category)
        {
            var descriptions = new Dictionary<string, string>
            {
                { "Damage", "伤害类Action" },
                { "Heal", "治疗类Action" },
                { "Shield", "防护类Action" },
                { "Defense", "防御类Action" },
                { "Movement", "位移类Action" },
                { "Control", "控制类Action" },
                { "Buff", "增益类Action" },
                { "Debuff", "减益类Action" },
                { "Summon", "召唤类Action" },
                { "Visual", "视觉效果类Action" },
                { "Audio", "音频效果类Action" }
            };

            return descriptions.TryGetValue(category, out var desc) ? desc : category;
        }

        /// <summary>
        /// 获取分类用途描�?        /// </summary>
        private string GetCategoryUsage(string category)
        {
            var usages = new Dictionary<string, string>
            {
                { "Damage", "用于造成伤害的技能效�? },
                { "Heal", "用于恢复生命值的技能效�? },
                { "Shield", "用于提供护盾保护的技能效�? },
                { "Defense", "用于防御和保护的技能效�? },
                { "Movement", "用于改变角色位置的技能效�? },
                { "Control", "用于控制目标行为的技能效�? },
                { "Buff", "用于提升属性的技能效�? },
                { "Debuff", "用于降低属性的技能效�? },
                { "Summon", "用于召唤单位的技能效�? },
                { "Visual", "用于视觉表现的技能效�? },
                { "Audio", "用于音频表现的技能效�? }
            };

            return usages.TryGetValue(category, out var usage) ? usage : "";
        }

        /// <summary>
        /// 获取Action显示名称
        /// </summary>
        private string GetActionDisplayName(string actionType)
        {
            var semanticInfo = registry.GetSemanticInfo(actionType);
            return semanticInfo?.displayName ?? actionType;
        }

        /// <summary>
        /// 生成推荐摘要文本（用于UI展示�?        /// </summary>
        public string GenerateSummaryText(EnhancedActionRecommendation recommendation)
        {
            var parts = new List<string>();

            // 得分信息
            parts.Add($"得分：{recommendation.final_score:P0}");

            // 主要理由（取�?条）
            if (recommendation.reasons.Count > 0)
            {
                parts.Add($"理由：{string.Join("�?, recommendation.reasons.Take(2))}");
            }

            // 警告（如果有�?            if (recommendation.warnings.Count > 0)
            {
                parts.Add($"警告：{recommendation.warnings.Count}�?);
            }

            return string.Join(" | ", parts);
        }
    }
}
