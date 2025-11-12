using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Action参数依赖�?- 管理参数间的依赖、互斥、条件必填关�?    /// </summary>
    public class ActionParameterDependencyGraph
    {
        private Dictionary<string, List<ParameterDependencyRule>> rulesByActionType;
        private Dictionary<string, ParameterConstraint> parameterConstraints;

        public ActionParameterDependencyGraph()
        {
            rulesByActionType = new Dictionary<string, List<ParameterDependencyRule>>();
            parameterConstraints = new Dictionary<string, ParameterConstraint>();
            InitializeDefaultRules();
        }

        /// <summary>
        /// 初始化默认依赖规�?        /// </summary>
        private void InitializeDefaultRules()
        {
            // DamageAction规则
            RegisterRule(new ParameterDependencyRule
            {
                actionType = "DamageAction",
                ruleType = DependencyRuleType.ConditionalRequired,
                sourceParameter = "damageType",
                sourceValue = "Physical",
                targetParameter = "lifeStealPercentage",
                explanation = "物理伤害类型时，生命偷取才有�?
            });

            RegisterRule(new ParameterDependencyRule
            {
                actionType = "DamageAction",
                ruleType = DependencyRuleType.ConditionalRequired,
                sourceParameter = "damageType",
                sourceValue = "Magical",
                targetParameter = "spellVampPercentage",
                explanation = "魔法伤害类型时，法术吸血才有�?
            });

            RegisterRule(new ParameterDependencyRule
            {
                actionType = "DamageAction",
                ruleType = DependencyRuleType.Exclusive,
                sourceParameter = "damageType",
                sourceValue = "Physical",
                targetParameter = "spellVampPercentage",
                explanation = "物理伤害不能使用法术吸血"
            });

            RegisterRule(new ParameterDependencyRule
            {
                actionType = "DamageAction",
                ruleType = DependencyRuleType.RangeConstraint,
                targetParameter = "baseDamage",
                minValue = 1f,
                maxValue = 10000f,
                explanation = "基础伤害应在合理范围�?
            });

            // MovementAction规则
            RegisterRule(new ParameterDependencyRule
            {
                actionType = "MovementAction",
                ruleType = DependencyRuleType.ConditionalRequired,
                sourceParameter = "movementType",
                sourceValue = "Arc",
                targetParameter = "arcHeight",
                explanation = "弧线移动类型必须设置弧线高度"
            });

            RegisterRule(new ParameterDependencyRule
            {
                actionType = "MovementAction",
                ruleType = DependencyRuleType.ConditionalRequired,
                sourceParameter = "movementType",
                sourceValue = "Curve",
                targetParameter = "movementCurve",
                explanation = "曲线移动类型必须设置移动曲线"
            });

            RegisterRule(new ParameterDependencyRule
            {
                actionType = "MovementAction",
                ruleType = DependencyRuleType.Exclusive,
                sourceParameter = "movementType",
                sourceValue = "Instant",
                targetParameter = "movementSpeed",
                explanation = "瞬移类型不需要设置移动速度"
            });

            RegisterRule(new ParameterDependencyRule
            {
                actionType = "MovementAction",
                ruleType = DependencyRuleType.RangeConstraint,
                targetParameter = "movementSpeed",
                minValue = 0f,
                maxValue = 2000f,
                explanation = "移动速度应在合理范围�?
            });

            // HealAction规则
            RegisterRule(new ParameterDependencyRule
            {
                actionType = "HealAction",
                ruleType = DependencyRuleType.RangeConstraint,
                targetParameter = "healAmount",
                minValue = 1f,
                maxValue = 5000f,
                explanation = "治疗量应在合理范围内"
            });

            // ShieldAction规则
            RegisterRule(new ParameterDependencyRule
            {
                actionType = "ShieldAction",
                ruleType = DependencyRuleType.RangeConstraint,
                targetParameter = "shieldAmount",
                minValue = 1f,
                maxValue = 5000f,
                explanation = "护盾量应在合理范围内"
            });

            Debug.Log("[ActionParameterDependencyGraph] Initialized with default rules");
        }

        /// <summary>
        /// 注册依赖规则
        /// </summary>
        public void RegisterRule(ParameterDependencyRule rule)
        {
            if (!rulesByActionType.ContainsKey(rule.actionType))
            {
                rulesByActionType[rule.actionType] = new List<ParameterDependencyRule>();
            }
            rulesByActionType[rule.actionType].Add(rule);
        }

        /// <summary>
        /// 获取指定Action类型的所有依赖规�?        /// </summary>
        public List<ParameterDependencyRule> GetRulesForAction(string actionType)
        {
            if (rulesByActionType.ContainsKey(actionType))
            {
                return rulesByActionType[actionType];
            }
            return new List<ParameterDependencyRule>();
        }

        /// <summary>
        /// 验证参数配置是否满足依赖规则
        /// </summary>
        public ValidationResult ValidateParameters(string actionType, Dictionary<string, object> parameters)
        {
            var result = new ValidationResult { isValid = true };
            var rules = GetRulesForAction(actionType);

            foreach (var rule in rules)
            {
                var issue = ValidateRule(rule, parameters);
                if (issue != null)
                {
                    result.isValid = false;
                    result.issues.Add(issue);
                }
            }

            return result;
        }

        /// <summary>
        /// 验证单条规则
        /// </summary>
        private ValidationIssue ValidateRule(ParameterDependencyRule rule, Dictionary<string, object> parameters)
        {
            switch (rule.ruleType)
            {
                case DependencyRuleType.ConditionalRequired:
                    return ValidateConditionalRequired(rule, parameters);

                case DependencyRuleType.Exclusive:
                    return ValidateExclusive(rule, parameters);

                case DependencyRuleType.RangeConstraint:
                    return ValidateRangeConstraint(rule, parameters);

                case DependencyRuleType.DefaultValue:
                    // 默认值规则不产生验证错误，仅用于补全
                    return null;

                default:
                    return null;
            }
        }

        /// <summary>
        /// 验证条件必填规则
        /// </summary>
        private ValidationIssue ValidateConditionalRequired(ParameterDependencyRule rule, Dictionary<string, object> parameters)
        {
            // 检查源参数是否存在且等于指定�?            if (parameters.ContainsKey(rule.sourceParameter))
            {
                var sourceValue = parameters[rule.sourceParameter];
                if (sourceValue != null && sourceValue.ToString() == rule.sourceValue)
                {
                    // 条件满足，检查目标参数是否存�?                    if (!parameters.ContainsKey(rule.targetParameter) || parameters[rule.targetParameter] == null)
                    {
                        return new ValidationIssue
                        {
                            severity = IssueSeverity.Error,
                            parameterName = rule.targetParameter,
                            message = $"当{rule.sourceParameter}={rule.sourceValue}时，{rule.targetParameter}为必填项",
                            explanation = rule.explanation
                        };
                    }
                }
            }

            return null;
        }

        /// <summary>
        /// 验证互斥规则
        /// </summary>
        private ValidationIssue ValidateExclusive(ParameterDependencyRule rule, Dictionary<string, object> parameters)
        {
            // 检查源参数是否存在且等于指定�?            if (parameters.ContainsKey(rule.sourceParameter))
            {
                var sourceValue = parameters[rule.sourceParameter];
                if (sourceValue != null && sourceValue.ToString() == rule.sourceValue)
                {
                    // 条件满足，检查目标参数是否不应该有�?                    if (parameters.ContainsKey(rule.targetParameter))
                    {
                        var targetValue = parameters[rule.targetParameter];
                        // 对于数值类型，检查是否不�?
                        if (targetValue != null && !IsZeroValue(targetValue))
                        {
                            return new ValidationIssue
                            {
                                severity = IssueSeverity.Warning,
                                parameterName = rule.targetParameter,
                                message = $"当{rule.sourceParameter}={rule.sourceValue}时，{rule.targetParameter}应该�?或不设置",
                                explanation = rule.explanation
                            };
                        }
                    }
                }
            }

            return null;
        }

        /// <summary>
        /// 验证范围约束规则
        /// </summary>
        private ValidationIssue ValidateRangeConstraint(ParameterDependencyRule rule, Dictionary<string, object> parameters)
        {
            if (parameters.ContainsKey(rule.targetParameter))
            {
                var value = parameters[rule.targetParameter];
                if (value != null)
                {
                    try
                    {
                        float numValue = Convert.ToSingle(value);
                        if (rule.minValue.HasValue && numValue < rule.minValue.Value)
                        {
                            return new ValidationIssue
                            {
                                severity = IssueSeverity.Warning,
                                parameterName = rule.targetParameter,
                                message = $"{rule.targetParameter}的值{numValue}低于推荐最小值{rule.minValue.Value}",
                                explanation = rule.explanation
                            };
                        }
                        if (rule.maxValue.HasValue && numValue > rule.maxValue.Value)
                        {
                            return new ValidationIssue
                            {
                                severity = IssueSeverity.Warning,
                                parameterName = rule.targetParameter,
                                message = $"{rule.targetParameter}的值{numValue}超出推荐最大值{rule.maxValue.Value}",
                                explanation = rule.explanation
                            };
                        }
                    }
                    catch
                    {
                        // 无法转换为数值，跳过验证
                    }
                }
            }

            return null;
        }

        /// <summary>
        /// 检查值是否为零�?        /// </summary>
        private bool IsZeroValue(object value)
        {
            if (value == null)
                return true;

            try
            {
                float numValue = Convert.ToSingle(value);
                return Math.Abs(numValue) < 0.0001f;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 获取参数的默认值建�?        /// </summary>
        public object GetDefaultValue(string actionType, string parameterName)
        {
            var rules = GetRulesForAction(actionType);
            var defaultRule = rules.FirstOrDefault(r =>
                r.ruleType == DependencyRuleType.DefaultValue &&
                r.targetParameter == parameterName);

            return defaultRule?.defaultValue;
        }

        /// <summary>
        /// 获取参数的推荐范�?        /// </summary>
        public (float? min, float? max) GetRecommendedRange(string actionType, string parameterName)
        {
            var rules = GetRulesForAction(actionType);
            var rangeRule = rules.FirstOrDefault(r =>
                r.ruleType == DependencyRuleType.RangeConstraint &&
                r.targetParameter == parameterName);

            if (rangeRule != null)
            {
                return (rangeRule.minValue, rangeRule.maxValue);
            }

            return (null, null);
        }

        /// <summary>
        /// 生成依赖关系的可视化文本
        /// </summary>
        public string GenerateDependencyReport(string actionType)
        {
            var rules = GetRulesForAction(actionType);
            if (rules.Count == 0)
            {
                return $"Action '{actionType}' 没有定义依赖规则";
            }

            var report = $"=== {actionType} 参数依赖规则 ===\n\n";

            var groupedRules = rules.GroupBy(r => r.ruleType);
            foreach (var group in groupedRules)
            {
                report += $"【{GetRuleTypeDisplayName(group.Key)}】\n";
                foreach (var rule in group)
                {
                    report += $"  - {rule.explanation}\n";
                }
                report += "\n";
            }

            return report;
        }

        private string GetRuleTypeDisplayName(DependencyRuleType type)
        {
            switch (type)
            {
                case DependencyRuleType.ConditionalRequired: return "条件必填";
                case DependencyRuleType.Exclusive: return "互斥约束";
                case DependencyRuleType.RangeConstraint: return "范围约束";
                case DependencyRuleType.DefaultValue: return "默认�?;
                default: return type.ToString();
            }
        }
    }

    /// <summary>
    /// 参数依赖规则
    /// </summary>
    [Serializable]
    public class ParameterDependencyRule
    {
        public string actionType;                   // Action类型
        public DependencyRuleType ruleType;         // 规则类型
        public string sourceParameter;              // 源参数名
        public string sourceValue;                  // 源参数值（条件�?        public string targetParameter;              // 目标参数�?        public object defaultValue;                 // 默认值（用于DefaultValue类型�?        public float? minValue;                     // 最小值（用于RangeConstraint类型�?        public float? maxValue;                     // 最大值（用于RangeConstraint类型�?        public string explanation;                  // 规则说明
    }

    /// <summary>
    /// 依赖规则类型
    /// </summary>
    public enum DependencyRuleType
    {
        ConditionalRequired,    // 条件必填：当A=x时，B必填
        Exclusive,              // 互斥：当A=x时，B应该为空�?
        DefaultValue,           // 默认值：B未设置时，使用默认�?        RangeConstraint         // 范围约束：B应在[min, max]范围�?    }

    /// <summary>
    /// 参数约束信息
    /// </summary>
    [Serializable]
    public class ParameterConstraint
    {
        public string parameterName;
        public Type parameterType;
        public bool isRequired;
        public object defaultValue;
        public float? minValue;
        public float? maxValue;
        public List<string> allowedValues;          // 枚举类型的允许�?    }

    /// <summary>
    /// 验证结果
    /// </summary>
    [Serializable]
    public class ValidationResult
    {
        public bool isValid;
        public List<ValidationIssue> issues = new List<ValidationIssue>();
    }

    /// <summary>
    /// 验证问题
    /// </summary>
    [Serializable]
    public class ValidationIssue
    {
        public IssueSeverity severity;
        public string parameterName;
        public string message;
        public string explanation;
    }

    /// <summary>
    /// 问题严重程度
    /// </summary>
    public enum IssueSeverity
    {
        Info,       // 信息
        Warning,    // 警告
        Error       // 错误
    }
}
