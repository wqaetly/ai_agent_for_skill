using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace SkillSystem.Editor
{
    /// <summary>
    /// DeepSeek API客户�?
    /// 用于调用DeepSeek生成Action描述
    /// </summary>
    public class DeepSeekClient
    {
        private const string API_URL = "https://api.deepseek.com/v1/chat/completions";
        private readonly string apiKey;

        public DeepSeekClient(string apiKey)
        {
            this.apiKey = apiKey;
        }

        /// <summary>
        /// 生成Action描述
        /// </summary>
        /// <param name="actionTypeName">Action类型�?/param>
        /// <param name="actionCode">Action源代�?/param>
        /// <param name="existingDisplayName">现有的显示名称（如果有）</param>
        /// <param name="existingCategory">现有的分类（如果有）</param>
        /// <returns>生成的描述数�?/returns>
        public async Task<ActionDescriptionResult> GenerateActionDescriptionAsync(
            string actionTypeName,
            string actionCode,
            string existingDisplayName = null,
            string existingCategory = null)
        {
            // 构建提示�?
            string prompt = BuildPrompt(actionTypeName, actionCode, existingDisplayName, existingCategory);

            // 调用API
            string response = await CallDeepSeekAPI(prompt);

            // 解析响应
            return ParseResponse(response, actionTypeName);
        }

        private string BuildPrompt(string typeName, string code, string displayName, string category)
        {
            StringBuilder sb = new StringBuilder();

            sb.AppendLine("你是一个Unity技能系统的专家，负责为Action脚本生成高质量的描述文本，用于RAG语义搜索系统�?);
            sb.AppendLine();
            sb.AppendLine("# 任务");
            sb.AppendLine($"分析以下Action类的源代码，生成结构化的描述信息�?);
            sb.AppendLine();
            sb.AppendLine("# Action源代�?);
            sb.AppendLine("```csharp");
            sb.AppendLine(code);
            sb.AppendLine("```");
            sb.AppendLine();
            sb.AppendLine("# 输出要求");
            sb.AppendLine("请以JSON格式输出，包含以下字段：");
            sb.AppendLine("{");
            sb.AppendLine("  \"displayName\": \"简短的中文显示名称�?-4个字）\",");
            sb.AppendLine("  \"category\": \"分类（Movement/Control/Damage/Visual/Audio/Buff等）\",");
            sb.AppendLine("  \"description\": \"详细的功能描述（150-300字）\",");
            sb.AppendLine("  \"searchKeywords\": \"逗号分隔的搜索关键词�?-10个）\"");
            sb.AppendLine("}");
            sb.AppendLine();
            sb.AppendLine("# description字段编写规范");
            sb.AppendLine("1. **核心功能**：用1-2句话概括Action的核心功�?);
            sb.AppendLine("2. **详细说明**：说明支持的主要参数、模式、配置项");
            sb.AppendLine("3. **使用场景**：列�?-5个典型的使用场景或示例技�?);
            sb.AppendLine("4. **关键区别**：强调与其他相似Action的区别（例如\"纯粹位移，不包含伤害和控制效果\"�?);
            sb.AppendLine("5. **中英混合**：关键术语使用中英文混合（如\"线性移�?Linear)\"），提高搜索匹配�?);
            sb.AppendLine();
            sb.AppendLine("# searchKeywords字段编写规范");
            sb.AppendLine("包含�?);
            sb.AppendLine("- 功能相关的中文词汇（如：位移、移动、冲刺、闪现）");
            sb.AppendLine("- 英文术语（如：movement、teleport、dash�?);
            sb.AppendLine("- 典型技能名称（如：闪现、跳斩、冲锋）");
            sb.AppendLine("- DOTA2/LOL中的类似技�?);
            sb.AppendLine();

            if (!string.IsNullOrEmpty(displayName))
            {
                sb.AppendLine($"# 现有信息（可参考但不强制使用）");
                sb.AppendLine($"- 显示名称：{displayName}");
                if (!string.IsNullOrEmpty(category))
                {
                    sb.AppendLine($"- 分类：{category}");
                }
                sb.AppendLine();
            }

            sb.AppendLine("# 注意事项");
            sb.AppendLine("- description必须包含足够的关键词，确保RAG搜索时能准确匹配");
            sb.AppendLine("- 如果Action名称包含控制类型（如ControlAction有Stun/Silence/Root等），必须全部列�?);
            sb.AppendLine("- 强调Action的独特性，避免与其他Action混淆");
            sb.AppendLine("- 使用中文为主，关键术语中英混�?);
            sb.AppendLine();
            sb.AppendLine("请直接输出JSON，不要包含其他解释文字�?);

            return sb.ToString();
        }

        private async Task<string> CallDeepSeekAPI(string prompt)
        {
            // 构建请求体（使用可序列化的类�?
            var requestBody = new ChatCompletionRequest
            {
                model = "deepseek-chat",
                messages = new ChatMessage[]
                {
                    new ChatMessage { role = "user", content = prompt }
                },
                temperature = 0.3f,  // 较低温度，保证输出稳�?
                max_tokens = 1000
            };

            string jsonBody = JsonUtility.ToJson(requestBody);

            // 创建请求
            using (UnityWebRequest request = new UnityWebRequest(API_URL, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.SetRequestHeader("Authorization", $"Bearer {apiKey}");

                // 发送请�?
                var operation = request.SendWebRequest();

                // 等待完成（使用TaskCompletionSource实现async/await�?
                var tcs = new TaskCompletionSource<bool>();
                operation.completed += _ => tcs.SetResult(true);
                await tcs.Task;

                // 检查错�?
                if (request.result != UnityWebRequest.Result.Success)
                {
                    throw new Exception($"DeepSeek API调用失败: {request.error}\n{request.downloadHandler.text}");
                }

                // 返回响应
                return request.downloadHandler.text;
            }
        }

        private ActionDescriptionResult ParseResponse(string responseJson, string typeName)
        {
            try
            {
                // 解析DeepSeek响应
                var response = JsonUtility.FromJson<DeepSeekResponse>(responseJson);
                string content = response.choices[0].message.content;

                // 提取JSON内容（去除可能的markdown代码块标记）
                content = content.Trim();
                if (content.StartsWith("```json"))
                {
                    content = content.Substring(7);
                }
                if (content.StartsWith("```"))
                {
                    content = content.Substring(3);
                }
                if (content.EndsWith("```"))
                {
                    content = content.Substring(0, content.Length - 3);
                }
                content = content.Trim();

                // 解析Action描述JSON
                var result = JsonUtility.FromJson<ActionDescriptionResult>(content);
                result.success = true;
                return result;
            }
            catch (Exception e)
            {
                Debug.LogError($"解析DeepSeek响应失败: {e.Message}\n原始响应:\n{responseJson}");
                return new ActionDescriptionResult
                {
                    success = false,
                    error = $"解析失败: {e.Message}",
                    displayName = typeName,
                    category = "Other",
                    description = "",
                    searchKeywords = ""
                };
            }
        }

        #region 数据结构

        // 请求相关数据结构
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

        // 响应相关数据结构
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

    /// <summary>
    /// Action描述生成结果
    /// </summary>
    [Serializable]
    public class ActionDescriptionResult
    {
        public bool success;
        public string error;
        public string displayName;
        public string category;
        public string description;
        public string searchKeywords;
    }
}
