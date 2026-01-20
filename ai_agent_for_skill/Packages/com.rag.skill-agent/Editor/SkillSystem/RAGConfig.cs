using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;

namespace RAG
{
    /// <summary>
    /// 技能系统类型配置 - 用于适配不同项目的技能架构
    /// </summary>
    [Serializable]
    public class SkillSystemTypeConfig
    {
        [Header("基类配置")]
        [Tooltip("Action基类的完整类型名（如：SkillSystem.Actions.ISkillAction）")]
        public string baseActionTypeName = "SkillSystem.Actions.ISkillAction";

        [Tooltip("技能数据类的完整类型名（如：SkillSystem.Data.SkillData）")]
        public string skillDataTypeName = "SkillSystem.Data.SkillData";

        [Tooltip("技能轨道类的完整类型名（如：SkillSystem.Data.SkillTrack）")]
        public string skillTrackTypeName = "SkillSystem.Data.SkillTrack";

        [Tooltip("程序集名称（如：Assembly-CSharp）")]
        public string assemblyName = "Assembly-CSharp";

        [Header("特性配置")]
        [Tooltip("显示名称特性类名（如：ActionDisplayNameAttribute）")]
        public string displayNameAttributeName = "ActionDisplayNameAttribute";

        [Tooltip("分类特性类名（如：ActionCategoryAttribute）")]
        public string categoryAttributeName = "ActionCategoryAttribute";

        [Tooltip("Odin LabelText特性类名")]
        public string labelTextAttributeName = "LabelTextAttribute";

        [Tooltip("Odin BoxGroup特性类名")]
        public string boxGroupAttributeName = "BoxGroupAttribute";

        [Tooltip("Odin InfoBox特性类名")]
        public string infoBoxAttributeName = "InfoBoxAttribute";

        [Tooltip("Odin MinValue特性类名")]
        public string minValueAttributeName = "MinValueAttribute";

        /// <summary>
        /// 缓存的基类Type
        /// </summary>
        [NonSerialized]
        private Type _cachedBaseActionType;

        [NonSerialized]
        private Type _cachedSkillDataType;

        [NonSerialized]
        private Type _cachedSkillTrackType;

        /// <summary>
        /// 获取Action基类Type（带缓存）
        /// </summary>
        public Type GetBaseActionType()
        {
            if (_cachedBaseActionType == null)
            {
                _cachedBaseActionType = FindTypeByName(baseActionTypeName);
                if (_cachedBaseActionType == null)
                {
                    Debug.LogError($"[SkillSystemTypeConfig] 无法找到基类类型: {baseActionTypeName}");
                }
            }
            return _cachedBaseActionType;
        }

        /// <summary>
        /// 获取技能数据类Type（带缓存）
        /// </summary>
        public Type GetSkillDataType()
        {
            if (_cachedSkillDataType == null)
            {
                _cachedSkillDataType = FindTypeByName(skillDataTypeName);
                if (_cachedSkillDataType == null)
                {
                    Debug.LogError($"[SkillSystemTypeConfig] 无法找到技能数据类型: {skillDataTypeName}");
                }
            }
            return _cachedSkillDataType;
        }

        /// <summary>
        /// 获取技能轨道类Type（带缓存）
        /// </summary>
        public Type GetSkillTrackType()
        {
            if (_cachedSkillTrackType == null)
            {
                _cachedSkillTrackType = FindTypeByName(skillTrackTypeName);
                if (_cachedSkillTrackType == null)
                {
                    Debug.LogError($"[SkillSystemTypeConfig] 无法找到技能轨道类型: {skillTrackTypeName}");
                }
            }
            return _cachedSkillTrackType;
        }

        /// <summary>
        /// 通过完整类名查找Type
        /// </summary>
        public static Type FindTypeByName(string fullTypeName)
        {
            if (string.IsNullOrEmpty(fullTypeName)) return null;

            // 首先尝试直接获取
            var type = Type.GetType(fullTypeName);
            if (type != null) return type;

            // 遍历所有已加载的程序集
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                type = assembly.GetType(fullTypeName);
                if (type != null) return type;
            }

            return null;
        }

        /// <summary>
        /// 获取完整的Odin类型字符串
        /// </summary>
        public string GetOdinTypeString(string typeName)
        {
            return $"{typeName}, {assemblyName}";
        }

        /// <summary>
        /// 清除缓存（类型配置变更时调用）
        /// </summary>
        public void ClearCache()
        {
            _cachedBaseActionType = null;
            _cachedSkillDataType = null;
            _cachedSkillTrackType = null;
        }
    }

    /// <summary>
    /// 字段映射配置 - 用于Python端Schema映射
    /// </summary>
    [Serializable]
    public class SchemaFieldMapping
    {
        [Tooltip("Unity字段名")]
        public string unityFieldName;

        [Tooltip("Python Schema字段名")]
        public string pythonFieldName;

        [Tooltip("字段描述")]
        public string description;
    }

    /// <summary>
    /// Buff系统类型配置 - 用于适配不同项目的Buff架构
    /// </summary>
    [Serializable]
    public class BuffSystemTypeConfig
    {
        [Header("基类配置")]
        [Tooltip("Buff模板类的完整类型名")]
        public string buffTemplateTypeName = "BuffSystem.Data.BuffTemplate";

        [Tooltip("Buff效果接口的完整类型名")]
        public string buffEffectTypeName = "BuffSystem.Data.IBuffEffect";

        [Tooltip("Buff触发器接口的完整类型名")]
        public string buffTriggerTypeName = "BuffSystem.Data.IBuffTrigger";

        [Tooltip("程序集名称")]
        public string assemblyName = "Assembly-CSharp";

        [Header("导出配置")]
        [Tooltip("Buff描述数据库路径")]
        public string databasePath = "Assets/Data/BuffDescriptionDatabase.asset";

        [Tooltip("Buff数据导出目录（相对于Unity项目根目录）")]
        public string exportDirectory = "../skill_agent/Data/Buffs";

        /// <summary>
        /// 缓存的类型
        /// </summary>
        [NonSerialized]
        private Type _cachedBuffTemplateType;

        [NonSerialized]
        private Type _cachedBuffEffectType;

        [NonSerialized]
        private Type _cachedBuffTriggerType;

        /// <summary>
        /// 获取Buff模板类Type
        /// </summary>
        public Type GetBuffTemplateType()
        {
            if (_cachedBuffTemplateType == null)
            {
                _cachedBuffTemplateType = SkillSystemTypeConfig.FindTypeByName(buffTemplateTypeName);
            }
            return _cachedBuffTemplateType;
        }

        /// <summary>
        /// 获取Buff效果接口Type
        /// </summary>
        public Type GetBuffEffectType()
        {
            if (_cachedBuffEffectType == null)
            {
                _cachedBuffEffectType = SkillSystemTypeConfig.FindTypeByName(buffEffectTypeName);
            }
            return _cachedBuffEffectType;
        }

        /// <summary>
        /// 获取Buff触发器接口Type
        /// </summary>
        public Type GetBuffTriggerType()
        {
            if (_cachedBuffTriggerType == null)
            {
                _cachedBuffTriggerType = SkillSystemTypeConfig.FindTypeByName(buffTriggerTypeName);
            }
            return _cachedBuffTriggerType;
        }

        /// <summary>
        /// 获取完整的Odin类型字符串
        /// </summary>
        public string GetOdinTypeString(string typeName)
        {
            return $"{typeName}, {assemblyName}";
        }

        /// <summary>
        /// 清除缓存
        /// </summary>
        public void ClearCache()
        {
            _cachedBuffTemplateType = null;
            _cachedBuffEffectType = null;
            _cachedBuffTriggerType = null;
        }
    }

    /// <summary>
    /// RAG系统全局配置
    /// 集中管理所有RAG相关的配置项
    /// </summary>
    [CreateAssetMenu(fileName = "RAGConfig", menuName = "RAG System/Config", order = 1)]
    public class RAGConfig : ScriptableObject
    {
        private const string CONFIG_PATH = "Assets/Data/RAGConfig.asset";
        private const string API_KEY_PREF = "RAGSystem_DeepSeekAPIKey"; // API Key单独存储在EditorPrefs中，不进入版本控制

        private static RAGConfig _instance;
        
        /// <summary>
        /// 获取配置单例
        /// </summary>
        public static RAGConfig Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = AssetDatabase.LoadAssetAtPath<RAGConfig>(CONFIG_PATH);
                    if (_instance == null)
                    {
                        _instance = CreateDefaultConfig();
                    }
                }
                return _instance;
            }
        }

        // ==================== 技能系统类型配置（适配不同项目） ====================
        [Header("技能系统类型配置")]
        [Tooltip("用于适配不同项目的技能架构，配置基类类型、程序集等")]
        public SkillSystemTypeConfig skillSystemConfig = new SkillSystemTypeConfig();

        [Header("Buff系统类型配置")]
        [Tooltip("用于适配不同项目的Buff架构")]
        public BuffSystemTypeConfig buffSystemConfig = new BuffSystemTypeConfig();

        [Header("Schema字段映射（Python端使用）")]
        [Tooltip("Unity字段名到Python Schema字段名的映射")]
        public List<SchemaFieldMapping> schemaFieldMappings = new List<SchemaFieldMapping>
        {
            new SchemaFieldMapping { unityFieldName = "skillName", pythonFieldName = "skillName", description = "技能名称" },
            new SchemaFieldMapping { unityFieldName = "skillDescription", pythonFieldName = "skillDescription", description = "技能描述" },
            new SchemaFieldMapping { unityFieldName = "totalDuration", pythonFieldName = "totalDuration", description = "总时长(帧)" },
            new SchemaFieldMapping { unityFieldName = "frameRate", pythonFieldName = "frameRate", description = "帧率" },
            new SchemaFieldMapping { unityFieldName = "tracks", pythonFieldName = "tracks", description = "技能轨道列表" },
            new SchemaFieldMapping { unityFieldName = "skillId", pythonFieldName = "skillId", description = "技能ID" }
        };

        // ==================== DeepSeek API 配置 ====================
        [Header("DeepSeek API 配置")]
        [Tooltip("DeepSeek API 地址")]
        public string deepSeekApiUrl = "https://api.deepseek.com/v1/chat/completions";
        
        [Tooltip("使用的模型名称")]
        public string deepSeekModel = "deepseek-chat";
        
        [Tooltip("温度参数，越低越稳定（0-2）")]
        [Range(0f, 2f)]
        public float deepSeekTemperature = 0.3f;
        
        [Tooltip("最大token数")]
        public int deepSeekMaxTokens = 1000;
        
        /// <summary>
        /// DeepSeek API Key（存储在EditorPrefs中，不进入版本控制）
        /// </summary>
        public static string DeepSeekApiKey
        {
            get => EditorPrefs.GetString(API_KEY_PREF, "");
            set => EditorPrefs.SetString(API_KEY_PREF, value);
        }

        // ==================== 服务器配置 ====================
        [Header("SkillAgent 服务器配置")]
        [Tooltip("服务器主机地址")]
        public string serverHost = "127.0.0.1";
        
        [Tooltip("服务器端口")]
        public int serverPort = 2024;
        
        [Tooltip("WebUI URL")]
        public string webUIUrl = "http://127.0.0.1:2024";
        
        [Tooltip("服务器启动超时时间（秒）")]
        public int serverStartTimeout = 30;

        // ==================== 路径配置 ====================
        [Header("路径配置")]
        [Tooltip("Action描述数据库路径")]
        public string actionDatabasePath = "Assets/Data/ActionDescriptionDatabase.asset";
        
        [Tooltip("JSON导出目录（相对于Unity项目根目录）")]
        public string exportDirectory = "../skill_agent/Data/Actions";
        
        [Tooltip("Python服务器脚本名")]
        public string serverScriptName = "langgraph_server.py";
        
        [Tooltip("依赖安装脚本名")]
        public string installDepsScriptName = "安装依赖.bat";

        // ==================== Prompt 模板配置 ====================
        [Header("Prompt 模板配置")]
        [TextArea(5, 10)]
        [Tooltip("系统角色描述")]
        public string promptSystemRole = "你是一个Unity技能系统的专家，负责为Action脚本生成高质量的描述文本，用于RAG语义搜索系统。";
        
        [TextArea(10, 20)]
        [Tooltip("输出格式要求")]
        public string promptOutputFormat = @"请以JSON格式输出，包含以下字段：
{
  ""displayName"": ""简短的中文显示名称（2-4个字）"",
  ""category"": ""分类（Movement/Control/Damage/Visual/Audio/Buff等）"",
  ""description"": ""详细的功能描述（150-300字）"",
  ""searchKeywords"": ""逗号分隔的搜索关键词（5-10个）"",
  ""parameterDescriptions"": {
    ""参数名1"": ""参数1的中文描述（20-50字）"",
    ""参数名2"": ""参数2的中文描述（20-50字）""
  }
}";
        
        [TextArea(15, 30)]
        [Tooltip("Description字段编写规范")]
        public string promptDescriptionSpec = @"# description字段编写规范
1. **核心功能**：用1-2句话概括Action的核心功能
2. **详细说明**：说明支持的主要参数、模式、配置项
3. **使用场景**：列举3-5个典型的使用场景或示例技能
4. **关键区别**：强调与其他相似Action的区别（例如""纯粹位移，不包含伤害和控制效果""）
5. **中英混合**：关键术语使用中英文混合（如""线性移动(Linear)""），提高搜索匹配率";
        
        [TextArea(10, 20)]
        [Tooltip("SearchKeywords字段编写规范")]
        public string promptKeywordsSpec = @"# searchKeywords字段编写规范
包含：
- 功能相关的中文词汇（如：位移、移动、冲刺、闪现）
- 英文术语（如：movement、teleport、dash）
- 典型技能名称（如：闪现、跳斩、冲锋）
- DOTA2/LOL中的类似技能";
        
        [TextArea(10, 20)]
        [Tooltip("参数描述编写规范")]
        public string promptParameterDescSpec = @"# parameterDescriptions字段编写规范
为源代码中每个public字段生成描述：
1. 描述该参数的作用和用途
2. 说明参数的取值范围或典型值（如有）
3. 举例说明不同取值对技能效果的影响
4. 使用中文，关键术语可中英混合
5. 每个参数描述控制在20-50字
6. 参数名必须与源代码中的字段名完全一致";
        
        [TextArea(8, 15)]
        [Tooltip("注意事项")]
        public string promptNotes = @"# 注意事项
- description必须包含足够的关键词，确保RAG搜索时能准确匹配
- 如果Action名称包含控制类型（如ControlAction有Stun/Silence/Root等），必须全部列举
- 强调Action的独特性，避免与其他Action混淆
- 使用中文为主，关键术语中英混合
- 请直接输出JSON，不要包含其他解释文字。";

        // ==================== 其他配置 ====================
        [Header("其他配置")]
        [Tooltip("导出后自动通知服务器重建索引")]
        public bool autoNotifyRebuild = true;
        
        [Tooltip("AI生成请求间隔时间（毫秒），用于限流")]
        public int aiRequestInterval = 1000;

        /// <summary>
        /// 构建完整的Prompt
        /// </summary>
        /// <param name="typeName">Action类型名</param>
        /// <param name="code">源代码</param>
        /// <param name="existingDisplayName">现有显示名称</param>
        /// <param name="existingCategory">现有分类</param>
        /// <returns>完整的prompt字符串</returns>
        public string BuildPrompt(string typeName, string code, string existingDisplayName = null, string existingCategory = null)
        {
            var sb = new System.Text.StringBuilder();
            
            sb.AppendLine(promptSystemRole);
            sb.AppendLine();
            sb.AppendLine("# 任务");
            sb.AppendLine($"分析以下Action类的源代码，生成结构化的描述信息：");
            sb.AppendLine();
            sb.AppendLine("# Action源代码");
            sb.AppendLine("```csharp");
            sb.AppendLine(code);
            sb.AppendLine("```");
            sb.AppendLine();
            sb.AppendLine("# 输出要求");
            sb.AppendLine(promptOutputFormat);
            sb.AppendLine();
            sb.AppendLine(promptDescriptionSpec);
            sb.AppendLine();
            sb.AppendLine(promptKeywordsSpec);
            sb.AppendLine();
            sb.AppendLine(promptParameterDescSpec);
            sb.AppendLine();
            
            if (!string.IsNullOrEmpty(existingDisplayName))
            {
                sb.AppendLine("# 现有信息（可参考但不强制使用）");
                sb.AppendLine($"- 显示名称：{existingDisplayName}");
                if (!string.IsNullOrEmpty(existingCategory))
                {
                    sb.AppendLine($"- 分类：{existingCategory}");
                }
                sb.AppendLine();
            }
            
            sb.AppendLine(promptNotes);
            
            return sb.ToString();
        }

        /// <summary>
        /// 获取完整的导出目录路径
        /// </summary>
        public string GetFullExportPath()
        {
            return Path.GetFullPath(exportDirectory);
        }

        /// <summary>
        /// 获取服务器完整URL
        /// </summary>
        public string GetServerUrl(string endpoint = "")
        {
            string baseUrl = $"http://{serverHost}:{serverPort}";
            return string.IsNullOrEmpty(endpoint) ? baseUrl : $"{baseUrl}/{endpoint.TrimStart('/')}";
        }

        /// <summary>
        /// 创建默认配置
        /// </summary>
        private static RAGConfig CreateDefaultConfig()
        {
            // 确保目录存在
            string directory = Path.GetDirectoryName(CONFIG_PATH);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            var config = CreateInstance<RAGConfig>();
            AssetDatabase.CreateAsset(config, CONFIG_PATH);
            AssetDatabase.SaveAssets();
            Debug.Log($"[RAGConfig] 已创建默认配置文件: {CONFIG_PATH}");
            return config;
        }

        /// <summary>
        /// 保存配置
        /// </summary>
        public void Save()
        {
            EditorUtility.SetDirty(this);
            AssetDatabase.SaveAssets();
        }

        /// <summary>
        /// 导出技能系统适配配置到JSON文件（供Python端使用）
        /// </summary>
        /// <param name="outputPath">输出路径，默认为skill_agent/Data/skill_system_config.json</param>
        public void ExportSkillSystemConfig(string outputPath = null)
        {
            if (string.IsNullOrEmpty(outputPath))
            {
                outputPath = Path.GetFullPath(Path.Combine(exportDirectory, "../skill_system_config.json"));
            }

            var config = new Dictionary<string, object>
            {
                ["project"] = new Dictionary<string, object>
                {
                    ["name"] = Application.productName,
                    ["assembly"] = skillSystemConfig.assemblyName,
                    ["unity_version"] = Application.unityVersion,
                    ["export_time"] = DateTime.Now.ToString("o")
                },
                ["types"] = new Dictionary<string, object>
                {
                    ["base_action"] = skillSystemConfig.baseActionTypeName,
                    ["skill_data"] = skillSystemConfig.skillDataTypeName,
                    ["skill_track"] = skillSystemConfig.skillTrackTypeName,
                    ["base_action_full"] = skillSystemConfig.GetOdinTypeString(skillSystemConfig.baseActionTypeName),
                    ["skill_data_full"] = skillSystemConfig.GetOdinTypeString(skillSystemConfig.skillDataTypeName),
                    ["skill_track_full"] = skillSystemConfig.GetOdinTypeString(skillSystemConfig.skillTrackTypeName)
                },
                ["attributes"] = new Dictionary<string, object>
                {
                    ["display_name"] = skillSystemConfig.displayNameAttributeName,
                    ["category"] = skillSystemConfig.categoryAttributeName,
                    ["label_text"] = skillSystemConfig.labelTextAttributeName,
                    ["box_group"] = skillSystemConfig.boxGroupAttributeName,
                    ["info_box"] = skillSystemConfig.infoBoxAttributeName,
                    ["min_value"] = skillSystemConfig.minValueAttributeName
                },
                ["schema_mapping"] = schemaFieldMappings.Select(m => new Dictionary<string, object>
                {
                    ["unity"] = m.unityFieldName,
                    ["python"] = m.pythonFieldName,
                    ["description"] = m.description
                }).ToList()
            };

            // 确保目录存在
            string directory = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            string json = JsonUtility.ToJson(new JsonWrapper { data = config }, true);
            // JsonUtility不支持嵌套Dictionary，使用简单的手动构建
            json = BuildConfigJson(config);

            File.WriteAllText(outputPath, json);
            Debug.Log($"[RAGConfig] 已导出技能系统配置到: {outputPath}");
        }

        /// <summary>
        /// 手动构建配置JSON（因为JsonUtility不支持嵌套Dictionary）
        /// </summary>
        private string BuildConfigJson(Dictionary<string, object> config)
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("{");

            var entries = config.ToList();
            for (int i = 0; i < entries.Count; i++)
            {
                var entry = entries[i];
                sb.Append($"  \"{entry.Key}\": ");
                AppendJsonValue(sb, entry.Value, 2);
                if (i < entries.Count - 1) sb.Append(",");
                sb.AppendLine();
            }

            sb.AppendLine("}");
            return sb.ToString();
        }

        private void AppendJsonValue(System.Text.StringBuilder sb, object value, int indent)
        {
            string indentStr = new string(' ', indent * 2);

            if (value is string str)
            {
                sb.Append($"\"{str}\"");
            }
            else if (value is bool b)
            {
                sb.Append(b ? "true" : "false");
            }
            else if (value is int || value is float || value is double)
            {
                sb.Append(value.ToString());
            }
            else if (value is Dictionary<string, object> dict)
            {
                sb.AppendLine("{");
                var dictEntries = dict.ToList();
                for (int i = 0; i < dictEntries.Count; i++)
                {
                    var entry = dictEntries[i];
                    sb.Append($"{indentStr}  \"{entry.Key}\": ");
                    AppendJsonValue(sb, entry.Value, indent + 1);
                    if (i < dictEntries.Count - 1) sb.Append(",");
                    sb.AppendLine();
                }
                sb.Append($"{indentStr}}}");
            }
            else if (value is IEnumerable<object> list)
            {
                sb.AppendLine("[");
                var items = list.ToList();
                for (int i = 0; i < items.Count; i++)
                {
                    sb.Append($"{indentStr}  ");
                    AppendJsonValue(sb, items[i], indent + 1);
                    if (i < items.Count - 1) sb.Append(",");
                    sb.AppendLine();
                }
                sb.Append($"{indentStr}]");
            }
            else if (value is System.Collections.IEnumerable enumerable)
            {
                sb.AppendLine("[");
                var items = enumerable.Cast<object>().ToList();
                for (int i = 0; i < items.Count; i++)
                {
                    sb.Append($"{indentStr}  ");
                    AppendJsonValue(sb, items[i], indent + 1);
                    if (i < items.Count - 1) sb.Append(",");
                    sb.AppendLine();
                }
                sb.Append($"{indentStr}]");
            }
            else
            {
                sb.Append($"\"{value}\"");
            }
        }

        /// <summary>
        /// 临时包装类用于JsonUtility
        /// </summary>
        [Serializable]
        private class JsonWrapper
        {
            public Dictionary<string, object> data;
        }

        /// <summary>
        /// 菜单项：导出技能系统配置
        /// </summary>
        [MenuItem("Tools/RAG System/导出技能系统配置 (Export Skill System Config)", priority = 102)]
        public static void ExportSkillSystemConfigMenu()
        {
            Instance.ExportSkillSystemConfig();
        }

        /// <summary>
        /// 打开配置编辑器窗口
        /// </summary>
        [MenuItem("Tools/RAG System/打开配置 (Open Config)", priority = 100)]
        public static void SelectConfig()
        {
            // 打开 UIElements 编辑器窗口
            RAGConfigEditorWindow.ShowWindow();
        }
        
        /// <summary>
        /// 在 Project 窗口中定位配置文件
        /// </summary>
        [MenuItem("Tools/RAG System/定位配置文件 (Ping Config Asset)", priority = 101)]
        public static void PingConfigAsset()
        {
            var config = Instance;
            Selection.activeObject = config;
            EditorGUIUtility.PingObject(config);
        }

        /// <summary>
        /// 重置为默认值
        /// </summary>
        [ContextMenu("重置为默认值")]
        public void ResetToDefaults()
        {
            // 重置技能系统配置
            skillSystemConfig = new SkillSystemTypeConfig();
            buffSystemConfig = new BuffSystemTypeConfig();

            // 重置字段映射
            schemaFieldMappings = new List<SchemaFieldMapping>
            {
                new SchemaFieldMapping { unityFieldName = "skillName", pythonFieldName = "skillName", description = "技能名称" },
                new SchemaFieldMapping { unityFieldName = "skillDescription", pythonFieldName = "skillDescription", description = "技能描述" },
                new SchemaFieldMapping { unityFieldName = "totalDuration", pythonFieldName = "totalDuration", description = "总时长(帧)" },
                new SchemaFieldMapping { unityFieldName = "frameRate", pythonFieldName = "frameRate", description = "帧率" },
                new SchemaFieldMapping { unityFieldName = "tracks", pythonFieldName = "tracks", description = "技能轨道列表" },
                new SchemaFieldMapping { unityFieldName = "skillId", pythonFieldName = "skillId", description = "技能ID" }
            };

            deepSeekApiUrl = "https://api.deepseek.com/v1/chat/completions";
            deepSeekModel = "deepseek-chat";
            deepSeekTemperature = 0.3f;
            deepSeekMaxTokens = 1000;

            serverHost = "127.0.0.1";
            serverPort = 2024;
            webUIUrl = "http://127.0.0.1:2024";
            serverStartTimeout = 30;

            actionDatabasePath = "Assets/Data/ActionDescriptionDatabase.asset";
            exportDirectory = "../skill_agent/Data/Actions";
            serverScriptName = "langgraph_server.py";
            installDepsScriptName = "安装依赖.bat";

            autoNotifyRebuild = true;
            aiRequestInterval = 1000;
            
            // Reset prompts
            promptSystemRole = "你是一个Unity技能系统的专家，负责为Action脚本生成高质量的描述文本，用于RAG语义搜索系统。";
            
            promptOutputFormat = @"请以JSON格式输出，包含以下字段：
{
  ""displayName"": ""简短的中文显示名称（2-4个字）"",
  ""category"": ""分类（Movement/Control/Damage/Visual/Audio/Buff等）"",
  ""description"": ""详细的功能描述（150-300字）"",
  ""searchKeywords"": ""逗号分隔的搜索关键词（5-10个）"",
  ""parameterDescriptions"": {
    ""参数名1"": ""参数1的中文描述（20-50字）"",
    ""参数名2"": ""参数2的中文描述（20-50字）""
  }
}";
            
            promptDescriptionSpec = @"# description字段编写规范
1. **核心功能**：用1-2句话概括Action的核心功能
2. **详细说明**：说明支持的主要参数、模式、配置项
3. **使用场景**：列举3-5个典型的使用场景或示例技能
4. **关键区别**：强调与其他相似Action的区别（例如""纯粹位移，不包含伤害和控制效果""）
5. **中英混合**：关键术语使用中英文混合（如""线性移动(Linear)""），提高搜索匹配率";
            
            promptKeywordsSpec = @"# searchKeywords字段编写规范
包含：
- 功能相关的中文词汇（如：位移、移动、冲刺、闪现）
- 英文术语（如：movement、teleport、dash）
- 典型技能名称（如：闪现、跳斩、冲锋）
- DOTA2/LOL中的类似技能";
            
            promptParameterDescSpec = @"# parameterDescriptions字段编写规范
为源代码中每个public字段生成描述：
1. 描述该参数的作用和用途
2. 说明参数的取值范围或典型值（如有）
3. 举例说明不同取值对技能效果的影响
4. 使用中文，关键术语可中英混合
5. 每个参数描述控制在20-50字
6. 参数名必须与源代码中的字段名完全一致";
            
            promptNotes = @"# 注意事项
- description必须包含足够的关键词，确保RAG搜索时能准确匹配
- 如果Action名称包含控制类型（如ControlAction有Stun/Silence/Root等），必须全部列举
- 强调Action的独特性，避免与其他Action混淆
- 使用中文为主，关键术语中英混合
- 请直接输出JSON，不要包含其他解释文字。";
            
            Save();
            Debug.Log("[RAGConfig] 已重置为默认值");
        }
    }
}
