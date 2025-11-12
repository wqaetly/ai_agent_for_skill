using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;
using SkillSystem.Data;
using SkillSystem.Actions;

namespace SkillSystem.RAG
{
    /// <summary>
    /// 技能上下文装配器 - 从技能数据中提取特征用于参数推理
    /// 负责提取描述、标签、帧位、已有Action等上下文信息
    /// </summary>
    public class SkillContextAssembler
    {
        /// <summary>
        /// 组装完整的技能上下文
        /// </summary>
        /// <param name="skillData">技能数据</param>
        /// <returns>技能上下文特征</returns>
        public static SkillContextFeatures AssembleContext(SkillData skillData)
        {
            if (skillData == null)
            {
                Debug.LogWarning("[SkillContextAssembler] SkillData is null");
                return new SkillContextFeatures();
            }

            var context = new SkillContextFeatures
            {
                skillId = skillData.skillId,
                skillName = skillData.skillName,
                skillDescription = skillData.skillDescription,
                totalDuration = skillData.totalDuration,
                frameRate = skillData.frameRate,
                durationInSeconds = skillData.GetDurationInSeconds()
            };

            // 提取标签（从描述中）
            context.tags = ExtractTagsFromDescription(skillData.skillDescription);

            // 提取已有的Action信息
            context.existingActions = ExtractExistingActions(skillData);

            // 分析技能阶段分布
            context.phaseDistribution = AnalyzePhaseDistribution(context.existingActions, skillData.totalDuration);

            // 统计Action类型使用频率
            context.actionTypeFrequency = CountActionTypeFrequency(context.existingActions);

            // 分析技能意图（从描述和Action组合推断）
            context.inferredIntents = InferSkillIntents(skillData.skillDescription, context.existingActions);

            Debug.Log($"[SkillContextAssembler] Assembled context for skill '{context.skillName}': {context.existingActions.Count} actions, {context.tags.Count} tags");

            return context;
        }

        /// <summary>
        /// 从描述中提取标签关键词
        /// </summary>
        private static List<string> ExtractTagsFromDescription(string description)
        {
            if (string.IsNullOrEmpty(description))
                return new List<string>();

            var tags = new List<string>();
            var keywords = new[]
            {
                "伤害", "治疗", "护盾", "位移", "控制", "增益", "减益",
                "召唤", "buff", "debuff", "dot", "aoe", "单体", "群体",
                "物理", "魔法", "纯粹", "暴击", "吸血", "冲刺", "闪现",
                "眩晕", "减速", "沉默", "击退", "击飞", "隐身", "无敌"
            };

            foreach (var keyword in keywords)
            {
                if (description.Contains(keyword))
                {
                    tags.Add(keyword);
                }
            }

            return tags;
        }

        /// <summary>
        /// 提取已存在的Action信息
        /// </summary>
        private static List<ExistingActionInfo> ExtractExistingActions(SkillData skillData)
        {
            var result = new List<ExistingActionInfo>();

            if (skillData.tracks == null)
                return result;

            foreach (var track in skillData.tracks)
            {
                if (!track.enabled || track.actions == null)
                    continue;

                foreach (var action in track.actions)
                {
                    if (action == null || !action.enabled)
                        continue;

                    var actionInfo = new ExistingActionInfo
                    {
                        actionType = action.GetType().Name,
                        displayName = action.GetDisplayName(),
                        frame = action.frame,
                        duration = action.duration,
                        trackName = track.trackName,
                        parameters = ExtractActionParameters(action)
                    };

                    result.Add(actionInfo);
                }
            }

            // 按帧位排序
            result = result.OrderBy(a => a.frame).ToList();

            return result;
        }

        /// <summary>
        /// 提取Action的参数信息
        /// </summary>
        private static Dictionary<string, object> ExtractActionParameters(ISkillAction action)
        {
            var parameters = new Dictionary<string, object>();
            var type = action.GetType();
            var fields = type.GetFields(BindingFlags.Public | BindingFlags.Instance);

            foreach (var field in fields)
            {
                // 跳过基类字段
                if (field.DeclaringType == typeof(ISkillAction))
                    continue;

                try
                {
                    var value = field.GetValue(action);
                    if (value != null)
                    {
                        parameters[field.Name] = value;
                    }
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[SkillContextAssembler] Failed to extract parameter {field.Name}: {e.Message}");
                }
            }

            return parameters;
        }

        /// <summary>
        /// 分析技能阶段分布
        /// 将技能时间线分为前期(0-33%)、中期(33-66%)、后期(66-100%)
        /// </summary>
        private static Dictionary<string, int> AnalyzePhaseDistribution(List<ExistingActionInfo> actions, int totalDuration)
        {
            var distribution = new Dictionary<string, int>
            {
                { "early", 0 },
                { "mid", 0 },
                { "late", 0 }
            };

            if (totalDuration == 0)
                return distribution;

            foreach (var action in actions)
            {
                float progress = (float)action.frame / totalDuration;
                if (progress < 0.33f)
                    distribution["early"]++;
                else if (progress < 0.66f)
                    distribution["mid"]++;
                else
                    distribution["late"]++;
            }

            return distribution;
        }

        /// <summary>
        /// 统计Action类型使用频率
        /// </summary>
        private static Dictionary<string, int> CountActionTypeFrequency(List<ExistingActionInfo> actions)
        {
            var frequency = new Dictionary<string, int>();

            foreach (var action in actions)
            {
                if (!frequency.ContainsKey(action.actionType))
                    frequency[action.actionType] = 0;
                frequency[action.actionType]++;
            }

            return frequency;
        }

        /// <summary>
        /// 推断技能意图（攻击型/防御型/辅助型/控制型/位移型）
        /// </summary>
        private static List<string> InferSkillIntents(string description, List<ExistingActionInfo> actions)
        {
            var intents = new HashSet<string>();

            // 从描述推断
            if (!string.IsNullOrEmpty(description))
            {
                if (description.Contains("伤害") || description.Contains("攻击"))
                    intents.Add("攻击型");
                if (description.Contains("治疗") || description.Contains("恢复"))
                    intents.Add("防御型");
                if (description.Contains("护盾") || description.Contains("防御"))
                    intents.Add("防御型");
                if (description.Contains("位移") || description.Contains("冲刺") || description.Contains("闪现"))
                    intents.Add("位移型");
                if (description.Contains("控制") || description.Contains("眩晕") || description.Contains("减速"))
                    intents.Add("控制型");
                if (description.Contains("增益") || description.Contains("buff"))
                    intents.Add("辅助型");
            }

            // 从Action类型推断
            foreach (var action in actions)
            {
                if (action.actionType.Contains("Damage"))
                    intents.Add("攻击型");
                if (action.actionType.Contains("Heal"))
                    intents.Add("防御型");
                if (action.actionType.Contains("Shield"))
                    intents.Add("防御型");
                if (action.actionType.Contains("Movement") || action.actionType.Contains("Teleport"))
                    intents.Add("位移型");
                if (action.actionType.Contains("Control") || action.actionType.Contains("Stun"))
                    intents.Add("控制型");
                if (action.actionType.Contains("Buff"))
                    intents.Add("辅助型");
            }

            return intents.ToList();
        }

        /// <summary>
        /// 组装用于查询的上下文摘要文本
        /// </summary>
        public static string BuildContextSummaryForQuery(SkillContextFeatures context)
        {
            var summary = $"技能名称: {context.skillName}\n";
            summary += $"技能描述: {context.skillDescription}\n";
            summary += $"持续时间: {context.durationInSeconds:F2}秒 ({context.totalDuration}帧)\n";

            if (context.tags.Count > 0)
            {
                summary += $"标签: {string.Join(", ", context.tags)}\n";
            }

            if (context.inferredIntents.Count > 0)
            {
                summary += $"技能类型: {string.Join(", ", context.inferredIntents)}\n";
            }

            if (context.existingActions.Count > 0)
            {
                summary += $"\n已有Action ({context.existingActions.Count}个):\n";
                foreach (var action in context.existingActions)
                {
                    summary += $"  - [{action.frame}帧] {action.displayName} (持续{action.duration}帧)\n";
                }
            }

            return summary;
        }
    }

    /// <summary>
    /// 技能上下文特征数据
    /// </summary>
    [Serializable]
    public class SkillContextFeatures
    {
        // 基础信息
        public string skillId;
        public string skillName;
        public string skillDescription;

        // 时间线信息
        public int totalDuration;           // 总帧数
        public int frameRate;               // 帧率
        public float durationInSeconds;     // 总秒数

        // 语义特征
        public List<string> tags = new List<string>();              // 标签关键词
        public List<string> inferredIntents = new List<string>();   // 推断的技能意图

        // 已有Action信息
        public List<ExistingActionInfo> existingActions = new List<ExistingActionInfo>();

        // 统计特征
        public Dictionary<string, int> phaseDistribution = new Dictionary<string, int>();       // 阶段分布
        public Dictionary<string, int> actionTypeFrequency = new Dictionary<string, int>();     // Action类型频率
    }

    /// <summary>
    /// 已存在的Action信息
    /// </summary>
    [Serializable]
    public class ExistingActionInfo
    {
        public string actionType;                           // Action类型名
        public string displayName;                          // 显示名称
        public int frame;                                   // 起始帧
        public int duration;                                // 持续帧数
        public string trackName;                            // 所在轨道名称
        public Dictionary<string, object> parameters;       // 参数值
    }
}
