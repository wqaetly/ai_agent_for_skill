using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace RAGSystem.Editor
{
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
  ""searchKeywords"": ""逗号分隔的搜索关键词（5-10个）""
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
  ""searchKeywords"": ""逗号分隔的搜索关键词（5-10个）""
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
