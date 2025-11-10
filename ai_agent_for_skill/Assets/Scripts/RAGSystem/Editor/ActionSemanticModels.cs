using System;
using System.Collections.Generic;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Action语义本体模型 - "用途-效果-依赖"三层结构
    /// </summary>
    [Serializable]
    public class ActionSemanticInfo
    {
        // 基础信息
        public string actionType;              // Action类型名（如DamageAction）
        public string displayName;             // 显示名称
        public string category;                // 分类

        // 用途层：描述Action的使用场景和意图
        public ActionPurpose purpose;

        // 效果层：描述Action产生的具体效果
        public ActionEffect effect;

        // 依赖层：描述Action的前置条件和后置约束
        public ActionDependency dependency;

        // 业务优先级
        public float businessPriority = 1.0f;  // 业务优先级权重（0-2）
    }

    /// <summary>
    /// Action用途定义
    /// </summary>
    [Serializable]
    public class ActionPurpose
    {
        public List<string> intents;          // 意图标签（如"造成伤害"、"位移"、"防护"）
        public List<string> scenarios;         // 适用场景（如"攻击技能"、"逃生技能"）
        public List<string> keywords;          // 关键词（用于语义匹配增强）
    }

    /// <summary>
    /// Action效果定义
    /// </summary>
    [Serializable]
    public class ActionEffect
    {
        public string primaryEffect;          // 主要效果（Damage/Heal/Shield/Movement/Control）
        public List<string> secondaryEffects; // 次要效果
        public string targetType;              // 目标类型（Self/Enemy/Ally/All）
        public string rangeType;               // 范围类型（Single/Area/Global）
        public bool instantaneous;             // 是否瞬时生效
    }

    /// <summary>
    /// Action依赖关系定义
    /// </summary>
    [Serializable]
    public class ActionDependency
    {
        public List<string> prerequisites;     // 前置Action（必须在此Action之前）
        public List<string> incompatibles;     // 互斥Action（不能同时存在）
        public List<string> synergies;         // 协同Action（推荐组合）
        public List<string> followUps;         // 后续推荐Action
    }

    /// <summary>
    /// 组合约束规则
    /// </summary>
    [Serializable]
    public class ActionCombinationRule
    {
        public string ruleName;                // 规则名称
        public string ruleType;                // 规则类型（Exclusive/Prerequisite/Synergy）
        public List<string> actionTypes;       // 涉及的Action类型
        public string description;             // 规则描述（用于解释）
        public int priority;                   // 规则优先级（数字越大优先级越高）
        public bool enabled = true;            // 是否启用
    }

    /// <summary>
    /// Action推荐增强结果
    /// </summary>
    [Serializable]
    public class EnhancedActionRecommendation
    {
        // 原始推荐信息
        public string action_type;
        public string display_name;
        public string category;
        public string description;
        public float semantic_similarity;      // 原始语义相似度

        // 增强评分信息
        public float business_score;           // 业务优先级得分
        public float final_score;              // 最终综合得分

        // 约束验证结果
        public bool is_valid;                  // 是否通过约束验证
        public List<string> validation_issues; // 验证问题列表

        // 推荐解释
        public List<string> reasons;           // 推荐理由
        public List<string> warnings;          // 警告信息
        public List<string> suggestions;       // 使用建议
        public List<string> reference_skills;  // 参考技能示例

        public EnhancedActionRecommendation()
        {
            validation_issues = new List<string>();
            reasons = new List<string>();
            warnings = new List<string>();
            suggestions = new List<string>();
            reference_skills = new List<string>();
        }
    }

    /// <summary>
    /// 语义配置根对象
    /// </summary>
    [Serializable]
    public class ActionSemanticConfig
    {
        public string version;                 // 配置版本
        public string lastModified;            // 最后修改时间
        public List<ActionSemanticInfo> actions; // Action语义列表
        public List<ActionCombinationRule> rules; // 组合规则列表

        public ActionSemanticConfig()
        {
            actions = new List<ActionSemanticInfo>();
            rules = new List<ActionCombinationRule>();
        }
    }
}
