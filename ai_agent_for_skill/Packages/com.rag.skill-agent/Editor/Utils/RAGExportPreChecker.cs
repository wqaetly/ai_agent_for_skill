using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace RAG
{
    /// <summary>
    /// RAG导出预检查工具
    /// 在执行导出操作前验证所有配置是否正确
    /// </summary>
    public static class RAGExportPreChecker
    {
        /// <summary>
        /// 预检查结果
        /// </summary>
        public class PreCheckResult
        {
            public List<string> Errors { get; } = new List<string>();
            public List<string> Warnings { get; } = new List<string>();
            public List<string> InfoMessages { get; } = new List<string>();

            public bool HasErrors => Errors.Count > 0;
            public bool HasWarnings => Warnings.Count > 0;
            public bool IsSuccess => !HasErrors;
        }

        /// <summary>
        /// 菜单项：执行导出预检查
        /// </summary>
        [MenuItem("Tools/RAG System/导出预检查 (Pre-Check)", priority = 50)]
        public static void RunPreCheck()
        {
            var result = PerformFullPreCheck();
            ShowPreCheckDialog(result);
        }

        /// <summary>
        /// 执行完整的预检查
        /// </summary>
        public static PreCheckResult PerformFullPreCheck()
        {
            var result = new PreCheckResult();
            var config = RAGConfig.Instance;

            if (config == null)
            {
                result.Errors.Add("无法加载 RAGConfig 配置文件");
                return result;
            }

            // 1. 检查 API Key
            CheckAPIKey(config, result);

            // 2. 检查技能系统基类配置
            CheckSkillSystemConfig(config, result);

            // 3. 检查 Buff 系统基类配置
            CheckBuffSystemConfig(config, result);

            // 4. 检查源码路径配置
            CheckSourcePaths(config, result);

            // 5. 检查导出目录
            CheckExportDirectories(config, result);

            // 6. 检查数据库文件
            CheckDatabaseFiles(config, result);

            // 7. 统计已导出文件数量
            CountExportedFiles(config, result);

            return result;
        }

        private static void CheckAPIKey(RAGConfig config, PreCheckResult result)
        {
            if (string.IsNullOrEmpty(config.deepSeekApiKey))
            {
                result.Warnings.Add("DeepSeek API Key 未配置（AI描述生成功能将不可用）");
            }
            else if (config.deepSeekApiKey.Length < 20)
            {
                result.Warnings.Add("DeepSeek API Key 长度异常，请确认是否正确");
            }
            else
            {
                result.InfoMessages.Add("✅ DeepSeek API Key 已配置");
            }
        }

        private static void CheckSkillSystemConfig(RAGConfig config, PreCheckResult result)
        {
            var typeConfig = config.skillSystemConfig;

            var baseType = typeConfig.GetBaseActionType();
            if (baseType == null)
            {
                result.Errors.Add($"技能系统: 无法找到基类类型 '{typeConfig.baseActionTypeName}'");
            }
            else
            {
                result.InfoMessages.Add($"✅ 技能基类类型: {baseType.Name}");
            }

            var skillDataType = typeConfig.GetSkillDataType();
            if (skillDataType == null)
            {
                result.Warnings.Add($"技能系统: 无法找到技能数据类型 '{typeConfig.skillDataTypeName}'");
            }

            var skillTrackType = typeConfig.GetSkillTrackType();
            if (skillTrackType == null)
            {
                result.Warnings.Add($"技能系统: 无法找到技能轨道类型 '{typeConfig.skillTrackTypeName}'");
            }
        }

        private static void CheckBuffSystemConfig(RAGConfig config, PreCheckResult result)
        {
            var buffConfig = config.buffSystemConfig;

            var effectType = buffConfig.GetBuffEffectType();
            if (effectType == null)
            {
                result.Errors.Add($"Buff系统: 无法找到效果接口 '{buffConfig.buffEffectTypeName}'");
            }
            else
            {
                result.InfoMessages.Add($"✅ Buff效果接口: {effectType.Name}");
            }

            var triggerType = buffConfig.GetBuffTriggerType();
            if (triggerType == null)
            {
                result.Errors.Add($"Buff系统: 无法找到触发器接口 '{buffConfig.buffTriggerTypeName}'");
            }
            else
            {
                result.InfoMessages.Add($"✅ Buff触发器接口: {triggerType.Name}");
            }
        }

        private static void CheckSourcePaths(RAGConfig config, PreCheckResult result)
        {
            // 检查技能系统源码路径
            if (config.skillSystemSourcePaths == null || config.skillSystemSourcePaths.Count == 0)
            {
                result.Warnings.Add("技能系统源码路径未配置（AI架构分析将跳过）");
            }
            else
            {
                int validPaths = 0;
                foreach (var path in config.skillSystemSourcePaths)
                {
                    string fullPath = Path.Combine(Application.dataPath, path.Replace("Assets/", ""));
                    if (Directory.Exists(fullPath))
                    {
                        validPaths++;
                    }
                }
                if (validPaths > 0)
                {
                    result.InfoMessages.Add($"✅ 技能系统源码路径: {validPaths} 个有效目录");
                }
                else
                {
                    result.Warnings.Add("技能系统源码路径: 所有配置的路径都不存在");
                }
            }

            // 检查 Buff 系统源码路径
            if (config.buffSystemSourcePaths == null || config.buffSystemSourcePaths.Count == 0)
            {
                result.Warnings.Add("Buff系统源码路径未配置（AI架构分析将跳过）");
            }
            else
            {
                int validPaths = 0;
                foreach (var path in config.buffSystemSourcePaths)
                {
                    string fullPath = Path.Combine(Application.dataPath, path.Replace("Assets/", ""));
                    if (Directory.Exists(fullPath))
                    {
                        validPaths++;
                    }
                }
                if (validPaths > 0)
                {
                    result.InfoMessages.Add($"✅ Buff系统源码路径: {validPaths} 个有效目录");
                }
            }
        }

        private static void CheckExportDirectories(RAGConfig config, PreCheckResult result)
        {
            // 检查 Action 导出目录
            string actionExportDir = Path.GetFullPath(config.exportDirectory);
            if (!Directory.Exists(actionExportDir))
            {
                result.Warnings.Add($"Action导出目录不存在: {actionExportDir}（首次导出时将自动创建）");
            }
            else
            {
                result.InfoMessages.Add($"✅ Action导出目录: {actionExportDir}");
            }

            // 检查 Buff 导出目录
            string buffExportDir = Path.Combine(Application.dataPath,
                config.buffSystemConfig.exportDirectory ?? "../skill_agent/Data/Buffs");
            buffExportDir = Path.GetFullPath(buffExportDir);
            if (!Directory.Exists(buffExportDir))
            {
                result.Warnings.Add($"Buff导出目录不存在: {buffExportDir}（首次导出时将自动创建）");
            }
            else
            {
                result.InfoMessages.Add($"✅ Buff导出目录: {buffExportDir}");
            }
        }

        private static void CheckDatabaseFiles(RAGConfig config, PreCheckResult result)
        {
            // 检查 Action 数据库
            if (!File.Exists(config.actionDatabasePath))
            {
                result.Warnings.Add("Action描述数据库不存在（首次扫描时将自动创建）");
            }
            else
            {
                result.InfoMessages.Add("✅ Action描述数据库已存在");
            }

            // 检查 Buff 数据库
            string buffDbPath = config.buffSystemConfig.databasePath;
            if (!File.Exists(buffDbPath))
            {
                result.Warnings.Add("Buff描述数据库不存在（首次扫描时将自动创建）");
            }
            else
            {
                result.InfoMessages.Add("✅ Buff描述数据库已存在");
            }
        }

        private static void CountExportedFiles(RAGConfig config, PreCheckResult result)
        {
            // 统计 Action JSON 文件
            string actionDir = Path.GetFullPath(config.exportDirectory);
            if (Directory.Exists(actionDir))
            {
                int actionCount = Directory.GetFiles(actionDir, "*.json", SearchOption.TopDirectoryOnly).Length;
                result.InfoMessages.Add($"📊 已导出 Action JSON: {actionCount} 个文件");
            }

            // 统计 Buff JSON 文件
            string buffDir = Path.Combine(Application.dataPath,
                config.buffSystemConfig.exportDirectory ?? "../skill_agent/Data/Buffs");
            buffDir = Path.GetFullPath(buffDir);

            if (Directory.Exists(buffDir))
            {
                string effectsDir = Path.Combine(buffDir, "Effects");
                string triggersDir = Path.Combine(buffDir, "Triggers");

                int effectCount = Directory.Exists(effectsDir)
                    ? Directory.GetFiles(effectsDir, "*.json").Length : 0;
                int triggerCount = Directory.Exists(triggersDir)
                    ? Directory.GetFiles(triggersDir, "*.json").Length : 0;

                result.InfoMessages.Add($"📊 已导出 Buff Effects: {effectCount} 个文件");
                result.InfoMessages.Add($"📊 已导出 Buff Triggers: {triggerCount} 个文件");

                // 检查枚举文件
                if (File.Exists(Path.Combine(buffDir, "BuffEnums.json")))
                {
                    result.InfoMessages.Add("📊 BuffEnums.json 已存在");
                }
            }

            // 检查 skill_system_config.json
            string configPath = Path.GetFullPath(Path.Combine(config.exportDirectory, "../skill_system_config.json"));
            if (File.Exists(configPath))
            {
                result.InfoMessages.Add("📊 skill_system_config.json 已存在");
            }
            else
            {
                result.Warnings.Add("skill_system_config.json 未导出（建议执行一键导出）");
            }
        }

        private static void ShowPreCheckDialog(PreCheckResult result)
        {
            var sb = new System.Text.StringBuilder();

            // 标题
            if (result.IsSuccess)
            {
                sb.AppendLine("✅ 预检查通过！可以执行导出操作。\n");
            }
            else
            {
                sb.AppendLine("❌ 预检查发现问题，请先修复以下错误：\n");
            }

            // 错误
            if (result.Errors.Count > 0)
            {
                sb.AppendLine("【错误】");
                foreach (var error in result.Errors)
                {
                    sb.AppendLine($"  ❌ {error}");
                }
                sb.AppendLine();
            }

            // 警告
            if (result.Warnings.Count > 0)
            {
                sb.AppendLine("【警告】");
                foreach (var warning in result.Warnings)
                {
                    sb.AppendLine($"  ⚠️ {warning}");
                }
                sb.AppendLine();
            }

            // 信息
            if (result.InfoMessages.Count > 0)
            {
                sb.AppendLine("【状态】");
                foreach (var info in result.InfoMessages)
                {
                    sb.AppendLine($"  {info}");
                }
            }

            string title = result.IsSuccess ? "导出预检查 - 通过" : "导出预检查 - 有问题";
            EditorUtility.DisplayDialog(title, sb.ToString(), "确定");
        }
    }
}
