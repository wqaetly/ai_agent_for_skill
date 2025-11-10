using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Action语义注册表 - 管理Action语义信息和约束规则
    /// 支持配置文件热更新
    /// </summary>
    public class ActionSemanticRegistry
    {
        private static ActionSemanticRegistry instance;
        public static ActionSemanticRegistry Instance
        {
            get
            {
                if (instance == null)
                {
                    instance = new ActionSemanticRegistry();
                }
                return instance;
            }
        }

        private ActionSemanticConfig config;
        private Dictionary<string, ActionSemanticInfo> semanticMap;
        private Dictionary<string, ActionCombinationRule> ruleMap;
        private string configPath;
        private DateTime lastLoadTime;

        private ActionSemanticRegistry()
        {
            semanticMap = new Dictionary<string, ActionSemanticInfo>();
            ruleMap = new Dictionary<string, ActionCombinationRule>();
            configPath = Path.Combine(Application.dataPath, "RAGSystem", "ActionSemanticConfig.json");
            LoadConfig();
        }

        /// <summary>
        /// 加载配置文件
        /// </summary>
        public bool LoadConfig()
        {
            try
            {
                // 如果配置文件不存在，创建默认配置
                if (!File.Exists(configPath))
                {
                    Debug.LogWarning($"[ActionSemanticRegistry] Config file not found at {configPath}, creating default config");
                    CreateDefaultConfig();
                    return true;
                }

                // 读取并解析配置文件
                string json = File.ReadAllText(configPath);
                config = JsonUtility.FromJson<ActionSemanticConfig>(json);

                if (config == null)
                {
                    Debug.LogError("[ActionSemanticRegistry] Failed to parse config file");
                    return false;
                }

                // 构建索引
                semanticMap.Clear();
                foreach (var action in config.actions)
                {
                    semanticMap[action.actionType] = action;
                }

                ruleMap.Clear();
                foreach (var rule in config.rules)
                {
                    ruleMap[rule.ruleName] = rule;
                }

                lastLoadTime = DateTime.Now;
                Debug.Log($"[ActionSemanticRegistry] Loaded config: {config.actions.Count} actions, {config.rules.Count} rules");
                return true;
            }
            catch (Exception e)
            {
                Debug.LogError($"[ActionSemanticRegistry] Error loading config: {e.Message}\n{e.StackTrace}");
                return false;
            }
        }

        /// <summary>
        /// 保存配置文件
        /// </summary>
        public bool SaveConfig()
        {
            try
            {
                // 确保目录存在
                string directory = Path.GetDirectoryName(configPath);
                if (!Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                config.lastModified = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

                // 序列化并保存
                string json = JsonUtility.ToJson(config, true);
                File.WriteAllText(configPath, json);

                Debug.Log($"[ActionSemanticRegistry] Config saved to {configPath}");
                return true;
            }
            catch (Exception e)
            {
                Debug.LogError($"[ActionSemanticRegistry] Error saving config: {e.Message}");
                return false;
            }
        }

        /// <summary>
        /// 重新加载配置（热更新）
        /// </summary>
        public bool ReloadConfig()
        {
            Debug.Log("[ActionSemanticRegistry] Reloading config...");
            return LoadConfig();
        }

        /// <summary>
        /// 获取Action语义信息
        /// </summary>
        public ActionSemanticInfo GetSemanticInfo(string actionType)
        {
            if (semanticMap.TryGetValue(actionType, out var info))
            {
                return info;
            }
            return null;
        }

        /// <summary>
        /// 获取所有语义信息
        /// </summary>
        public List<ActionSemanticInfo> GetAllSemanticInfo()
        {
            return config?.actions ?? new List<ActionSemanticInfo>();
        }

        /// <summary>
        /// 获取组合规则
        /// </summary>
        public ActionCombinationRule GetRule(string ruleName)
        {
            if (ruleMap.TryGetValue(ruleName, out var rule))
            {
                return rule;
            }
            return null;
        }

        /// <summary>
        /// 获取所有启用的规则
        /// </summary>
        public List<ActionCombinationRule> GetEnabledRules()
        {
            return config?.rules?.Where(r => r.enabled).ToList() ?? new List<ActionCombinationRule>();
        }

        /// <summary>
        /// 获取特定类型的规则
        /// </summary>
        public List<ActionCombinationRule> GetRulesByType(string ruleType)
        {
            return config?.rules?.Where(r => r.enabled && r.ruleType == ruleType).ToList()
                ?? new List<ActionCombinationRule>();
        }

        /// <summary>
        /// 获取涉及特定Action的规则
        /// </summary>
        public List<ActionCombinationRule> GetRulesForAction(string actionType)
        {
            return config?.rules?.Where(r => r.enabled && r.actionTypes.Contains(actionType)).ToList()
                ?? new List<ActionCombinationRule>();
        }

        /// <summary>
        /// 创建默认配置
        /// </summary>
        private void CreateDefaultConfig()
        {
            config = new ActionSemanticConfig
            {
                version = "1.0.0",
                lastModified = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };

            // 添加一些示例语义定义
            AddDefaultSemanticInfo();

            // 添加一些示例规则
            AddDefaultRules();

            // 保存配置
            SaveConfig();
        }

        /// <summary>
        /// 添加默认语义信息
        /// </summary>
        private void AddDefaultSemanticInfo()
        {
            // DamageAction语义定义
            config.actions.Add(new ActionSemanticInfo
            {
                actionType = "DamageAction",
                displayName = "伤害",
                category = "Damage",
                purpose = new ActionPurpose
                {
                    intents = new List<string> { "造成伤害", "攻击", "输出" },
                    scenarios = new List<string> { "攻击技能", "伤害技能", "输出技能" },
                    keywords = new List<string> { "伤害", "攻击", "打击", "damage", "attack" }
                },
                effect = new ActionEffect
                {
                    primaryEffect = "Damage",
                    secondaryEffects = new List<string>(),
                    targetType = "Enemy",
                    rangeType = "Single",
                    instantaneous = true
                },
                dependency = new ActionDependency
                {
                    prerequisites = new List<string>(),
                    incompatibles = new List<string> { "HealAction" }, // 同一时刻不应该既造成伤害又治疗
                    synergies = new List<string> { "ControlAction", "BuffAction" },
                    followUps = new List<string> { "BuffAction", "AnimationAction" }
                },
                businessPriority = 1.2f
            });

            // MovementAction语义定义
            config.actions.Add(new ActionSemanticInfo
            {
                actionType = "MovementAction",
                displayName = "位移",
                category = "Movement",
                purpose = new ActionPurpose
                {
                    intents = new List<string> { "位移", "移动", "改变位置" },
                    scenarios = new List<string> { "冲刺技能", "闪现", "位移技能", "跳跃" },
                    keywords = new List<string> { "位移", "移动", "冲刺", "闪现", "跳跃", "movement", "dash", "blink" }
                },
                effect = new ActionEffect
                {
                    primaryEffect = "Movement",
                    secondaryEffects = new List<string>(),
                    targetType = "Self",
                    rangeType = "Single",
                    instantaneous = false
                },
                dependency = new ActionDependency
                {
                    prerequisites = new List<string>(),
                    incompatibles = new List<string> { "ControlAction" }, // 被控制时无法移动
                    synergies = new List<string> { "DamageAction", "AnimationAction" },
                    followUps = new List<string> { "DamageAction" }
                },
                businessPriority = 1.0f
            });

            // ShieldAction语义定义
            config.actions.Add(new ActionSemanticInfo
            {
                actionType = "ShieldAction",
                displayName = "护盾",
                category = "Defense",
                purpose = new ActionPurpose
                {
                    intents = new List<string> { "防护", "保护", "吸收伤害" },
                    scenarios = new List<string> { "防御技能", "保护技能", "护盾技能" },
                    keywords = new List<string> { "护盾", "防护", "保护", "吸收", "shield", "protect" }
                },
                effect = new ActionEffect
                {
                    primaryEffect = "Shield",
                    secondaryEffects = new List<string>(),
                    targetType = "Self",
                    rangeType = "Single",
                    instantaneous = true
                },
                dependency = new ActionDependency
                {
                    prerequisites = new List<string>(),
                    incompatibles = new List<string>(),
                    synergies = new List<string> { "HealAction", "BuffAction" },
                    followUps = new List<string> { "DamageAction" } // 护盾后可能有反击伤害
                },
                businessPriority = 1.1f
            });

            // HealAction语义定义
            config.actions.Add(new ActionSemanticInfo
            {
                actionType = "HealAction",
                displayName = "治疗",
                category = "Heal",
                purpose = new ActionPurpose
                {
                    intents = new List<string> { "治疗", "恢复", "回血" },
                    scenarios = new List<string> { "治疗技能", "恢复技能", "回血技能" },
                    keywords = new List<string> { "治疗", "恢复", "回血", "heal", "restore" }
                },
                effect = new ActionEffect
                {
                    primaryEffect = "Heal",
                    secondaryEffects = new List<string>(),
                    targetType = "Self",
                    rangeType = "Single",
                    instantaneous = true
                },
                dependency = new ActionDependency
                {
                    prerequisites = new List<string>(),
                    incompatibles = new List<string> { "DamageAction" },
                    synergies = new List<string> { "ShieldAction", "BuffAction" },
                    followUps = new List<string>()
                },
                businessPriority = 1.0f
            });
        }

        /// <summary>
        /// 添加默认规则
        /// </summary>
        private void AddDefaultRules()
        {
            // 互斥规则：同一时刻不应该既造成伤害又治疗
            config.rules.Add(new ActionCombinationRule
            {
                ruleName = "Damage_Heal_Exclusive",
                ruleType = "Exclusive",
                actionTypes = new List<string> { "DamageAction", "HealAction" },
                description = "同一技能不应该同时对同一目标造成伤害和治疗",
                priority = 10,
                enabled = true
            });

            // 互斥规则：MovementAction不应该与击退混淆
            config.rules.Add(new ActionCombinationRule
            {
                ruleName = "Movement_Not_Knockback",
                ruleType = "Exclusive",
                actionTypes = new List<string> { "MovementAction" },
                description = "MovementAction是自主位移，不是被动击退。如需击退效果，应使用ControlAction或专门的击退Action",
                priority = 9,
                enabled = true
            });

            // 协同规则：伤害+控制效果
            config.rules.Add(new ActionCombinationRule
            {
                ruleName = "Damage_Control_Synergy",
                ruleType = "Synergy",
                actionTypes = new List<string> { "DamageAction", "ControlAction" },
                description = "伤害和控制效果是常见的协同组合，如晕眩+伤害",
                priority = 5,
                enabled = true
            });

            // 协同规则：护盾+治疗
            config.rules.Add(new ActionCombinationRule
            {
                ruleName = "Shield_Heal_Synergy",
                ruleType = "Synergy",
                actionTypes = new List<string> { "ShieldAction", "HealAction" },
                description = "护盾和治疗是常见的防御组合",
                priority = 5,
                enabled = true
            });

            // 前置规则：特效需要先有实际效果
            config.rules.Add(new ActionCombinationRule
            {
                ruleName = "Effect_Before_Visual",
                ruleType = "Prerequisite",
                actionTypes = new List<string> { "DamageAction", "AnimationAction" },
                description = "动画和特效应该配合实际的技能效果，建议先添加功能Action再添加表现Action",
                priority = 3,
                enabled = true
            });
        }

        /// <summary>
        /// 获取配置路径
        /// </summary>
        public string GetConfigPath()
        {
            return configPath;
        }

        /// <summary>
        /// 获取最后加载时间
        /// </summary>
        public DateTime GetLastLoadTime()
        {
            return lastLoadTime;
        }
    }
}
