using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using UnityEngine.Networking;

namespace RAG
{
    /// <summary>
    /// 系统架构分析器
    /// 通过 AI 分析项目源码，自动生成系统架构理解 Prompt
    /// 支持两种模式：
    /// 1. AI分析模式：配置源码路径 → DeepSeek 分析 → 生成 Prompt
    /// 2. 自定义模式：用户配置自定义 Prompt 文件路径
    ///
    /// 注意：分析 Prompt 模板已移至 RAGConfig 中配置，可在编辑器中自定义。
    /// </summary>
    public static class SystemArchitectureAnalyzer
    {
        /// <summary>
        /// 使用 AI 分析技能系统源码生成架构 Prompt
        /// </summary>
        public static async Task<string> AnalyzeSkillSystemWithAI(RAGConfig config)
        {
            // 1. 检查自定义 Prompt 文件
            if (!string.IsNullOrEmpty(config.customSkillArchitecturePromptPath))
            {
                string customPrompt = LoadCustomPromptFile(config.customSkillArchitecturePromptPath);
                if (!string.IsNullOrEmpty(customPrompt))
                {
                    Debug.Log("[SystemArchitectureAnalyzer] 使用自定义技能系统架构 Prompt 文件");
                    return customPrompt;
                }
            }

            // 2. 检查源码路径配置
            if (config.skillSystemSourcePaths == null || config.skillSystemSourcePaths.Count == 0)
            {
                return "⚠️ 未配置技能系统源码路径，请在 RAGConfig 中设置 skillSystemSourcePaths";
            }

            // 3. 收集源码
            string sourceCode = config.CollectSourceCode(config.skillSystemSourcePaths);
            if (string.IsNullOrEmpty(sourceCode))
            {
                return "⚠️ 未找到任何 C# 源码文件，请检查配置的路径是否正确";
            }

            // 4. 构建分析 Prompt（使用 RAGConfig 中的模板）
            string analysisPrompt = string.Format(config.skillArchitectureAnalysisPromptTemplate, sourceCode);

            // 5. 调用 DeepSeek API
            string result = await CallDeepSeekForAnalysis(config, analysisPrompt);

            return result;
        }

        /// <summary>
        /// 使用 AI 分析 Buff 系统源码生成架构 Prompt
        /// </summary>
        public static async Task<string> AnalyzeBuffSystemWithAI(RAGConfig config)
        {
            // 1. 检查自定义 Prompt 文件
            if (!string.IsNullOrEmpty(config.customBuffArchitecturePromptPath))
            {
                string customPrompt = LoadCustomPromptFile(config.customBuffArchitecturePromptPath);
                if (!string.IsNullOrEmpty(customPrompt))
                {
                    Debug.Log("[SystemArchitectureAnalyzer] 使用自定义 Buff 系统架构 Prompt 文件");
                    return customPrompt;
                }
            }

            // 2. 检查源码路径配置
            if (config.buffSystemSourcePaths == null || config.buffSystemSourcePaths.Count == 0)
            {
                return "⚠️ 未配置 Buff 系统源码路径，请在 RAGConfig 中设置 buffSystemSourcePaths";
            }

            // 3. 收集源码
            string sourceCode = config.CollectSourceCode(config.buffSystemSourcePaths);
            if (string.IsNullOrEmpty(sourceCode))
            {
                return "⚠️ 未找到任何 C# 源码文件，请检查配置的路径是否正确";
            }

            // 4. 构建分析 Prompt（使用 RAGConfig 中的模板）
            string analysisPrompt = string.Format(config.buffArchitectureAnalysisPromptTemplate, sourceCode);

            // 5. 调用 DeepSeek API
            string result = await CallDeepSeekForAnalysis(config, analysisPrompt);

            return result;
        }

        /// <summary>
        /// 加载自定义 Prompt 文件
        /// </summary>
        private static string LoadCustomPromptFile(string relativePath)
        {
            if (string.IsNullOrEmpty(relativePath))
                return null;

            string fullPath = relativePath;
            if (relativePath.StartsWith("Assets/"))
            {
                fullPath = Path.Combine(Application.dataPath, relativePath.Substring(7));
            }

            if (File.Exists(fullPath))
            {
                return File.ReadAllText(fullPath, Encoding.UTF8);
            }

            Debug.LogWarning($"[SystemArchitectureAnalyzer] 自定义 Prompt 文件不存在: {fullPath}");
            return null;
        }

        /// <summary>
        /// 调用 DeepSeek API 进行源码分析
        /// </summary>
        private static async Task<string> CallDeepSeekForAnalysis(RAGConfig config, string prompt)
        {
            string apiKey = RAGConfig.DeepSeekApiKey;
            if (string.IsNullOrEmpty(apiKey))
            {
                throw new Exception("未配置 DeepSeek API Key，请在 RAGConfig 设置窗口中配置");
            }

            var requestBody = new ChatCompletionRequest
            {
                model = config.deepSeekModel,
                messages = new ChatMessage[]
                {
                    new ChatMessage { role = "user", content = prompt }
                },
                temperature = config.architectureAnalysisTemperature, // 使用配置中的温度
                max_tokens = config.architectureAnalysisMaxTokens     // 使用配置中的最大 Token 数
            };

            string jsonBody = JsonUtility.ToJson(requestBody);

            using (UnityWebRequest request = new UnityWebRequest(config.deepSeekApiUrl, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.SetRequestHeader("Authorization", $"Bearer {apiKey}");

                var operation = request.SendWebRequest();

                var tcs = new TaskCompletionSource<bool>();
                operation.completed += _ => tcs.SetResult(true);
                await tcs.Task;

                if (request.result != UnityWebRequest.Result.Success)
                {
                    throw new Exception($"DeepSeek API 调用失败: {request.error}\n{request.downloadHandler.text}");
                }

                // 解析响应
                var response = JsonUtility.FromJson<DeepSeekResponse>(request.downloadHandler.text);
                return response.choices[0].message.content;
            }
        }

        /// <summary>
        /// 异步生成并保存系统架构 Prompt
        /// </summary>
        public static async Task GenerateAndSaveArchitecturePromptsAsync(RAGConfig config)
        {
            try
            {
                // 分析技能系统
                EditorUtility.DisplayProgressBar("AI 分析系统架构", "正在分析技能系统源码...", 0.2f);
                config.skillSystemArchitecturePrompt = await AnalyzeSkillSystemWithAI(config);

                // 分析 Buff 系统
                EditorUtility.DisplayProgressBar("AI 分析系统架构", "正在分析 Buff 系统源码...", 0.6f);
                config.buffSystemArchitecturePrompt = await AnalyzeBuffSystemWithAI(config);

                // 更新元信息
                config.architecturePromptGeneratedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                config.architecturePromptSource = DeterminePromptSource(config);

                // 保存配置
                EditorUtility.DisplayProgressBar("AI 分析系统架构", "保存配置...", 0.9f);
                config.Save();

                EditorUtility.ClearProgressBar();

                Debug.Log($"[SystemArchitectureAnalyzer] 系统架构分析完成");
                Debug.Log($"  - 来源: {config.architecturePromptSource}");
                Debug.Log($"  - 技能系统 Prompt: {config.skillSystemArchitecturePrompt.Length} 字符");
                Debug.Log($"  - Buff 系统 Prompt: {config.buffSystemArchitecturePrompt.Length} 字符");
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Debug.LogError($"[SystemArchitectureAnalyzer] 分析失败: {e.Message}");
                throw;
            }
        }

        /// <summary>
        /// 确定 Prompt 来源描述
        /// </summary>
        private static string DeterminePromptSource(RAGConfig config)
        {
            bool skillFromCustom = !string.IsNullOrEmpty(config.customSkillArchitecturePromptPath);
            bool buffFromCustom = !string.IsNullOrEmpty(config.customBuffArchitecturePromptPath);

            if (skillFromCustom && buffFromCustom)
                return "自定义文件";
            else if (skillFromCustom || buffFromCustom)
                return "混合（部分自定义）";
            else
                return "AI 分析源码";
        }

        /// <summary>
        /// 菜单项：使用 AI 分析系统架构
        /// </summary>
        [MenuItem("Tools/RAG System/AI 分析系统架构 (Analyze with AI)", priority = 103)]
        public static async void AnalyzeArchitectureWithAIMenu()
        {
            var config = RAGConfig.Instance;
            if (config == null)
            {
                EditorUtility.DisplayDialog("错误", "未找到 RAG 配置文件", "确定");
                return;
            }

            // 检查配置
            bool hasSkillPaths = config.skillSystemSourcePaths != null && config.skillSystemSourcePaths.Count > 0;
            bool hasBuffPaths = config.buffSystemSourcePaths != null && config.buffSystemSourcePaths.Count > 0;
            bool hasCustomSkill = !string.IsNullOrEmpty(config.customSkillArchitecturePromptPath);
            bool hasCustomBuff = !string.IsNullOrEmpty(config.customBuffArchitecturePromptPath);

            if (!hasSkillPaths && !hasBuffPaths && !hasCustomSkill && !hasCustomBuff)
            {
                EditorUtility.DisplayDialog("配置缺失",
                    "请先配置以下至少一项：\n\n" +
                    "• 技能系统源码路径 (skillSystemSourcePaths)\n" +
                    "• Buff 系统源码路径 (buffSystemSourcePaths)\n" +
                    "• 自定义技能架构 Prompt 文件\n" +
                    "• 自定义 Buff 架构 Prompt 文件\n\n" +
                    "请打开 RAGConfig 设置窗口进行配置。",
                    "确定");
                return;
            }

            string message = "将使用以下方式生成系统架构 Prompt：\n\n";

            if (hasCustomSkill)
                message += "• 技能系统：使用自定义文件\n";
            else if (hasSkillPaths)
                message += "• 技能系统：AI 分析源码\n";
            else
                message += "• 技能系统：跳过（未配置）\n";

            if (hasCustomBuff)
                message += "• Buff 系统：使用自定义文件\n";
            else if (hasBuffPaths)
                message += "• Buff 系统：AI 分析源码\n";
            else
                message += "• Buff 系统：跳过（未配置）\n";

            message += "\n这将帮助 AI 更准确地理解参数含义。是否继续？";

            if (EditorUtility.DisplayDialog("AI 分析系统架构", message, "开始分析", "取消"))
            {
                try
                {
                    await GenerateAndSaveArchitecturePromptsAsync(config);

                    EditorUtility.DisplayDialog("完成",
                        $"系统架构分析完成！\n\n" +
                        $"来源: {config.architecturePromptSource}\n" +
                        $"生成时间: {config.architecturePromptGeneratedTime}\n" +
                        $"技能系统 Prompt: {config.skillSystemArchitecturePrompt.Length} 字符\n" +
                        $"Buff 系统 Prompt: {config.buffSystemArchitecturePrompt.Length} 字符",
                        "确定");
                }
                catch (Exception e)
                {
                    EditorUtility.DisplayDialog("错误", $"分析失败：\n{e.Message}", "确定");
                }
            }
        }

        #region 数据结构

        [Serializable]
        private class ChatCompletionRequest
        {
            public string model;
            public ChatMessage[] messages;
            public float temperature;
            public int max_tokens;
        }

        [Serializable]
        private class ChatMessage
        {
            public string role;
            public string content;
        }

        [Serializable]
        private class DeepSeekResponse
        {
            public Choice[] choices;
        }

        [Serializable]
        private class Choice
        {
            public Message message;
        }

        [Serializable]
        private class Message
        {
            public string content;
        }

        #endregion
    }
}

