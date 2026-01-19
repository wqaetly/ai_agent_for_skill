using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace RAGSystem.Editor
{
    /// <summary>
    /// DeepSeek API客户端
    /// 用于调用DeepSeek生成Action描述
    /// 配置从 RAGConfig 获取
    /// </summary>
    public class DeepSeekClient
    {
        private readonly string apiKey;
        private readonly RAGConfig config;

        public DeepSeekClient(string apiKey)
        {
            this.apiKey = apiKey;
            this.config = RAGConfig.Instance;
        }

        /// <summary>
        /// 生成Action描述
        /// </summary>
        /// <param name="actionTypeName">Action类型名</param>
        /// <param name="actionCode">Action源代码</param>
        /// <param name="existingDisplayName">现有的显示名称（如果有）</param>
        /// <param name="existingCategory">现有的分类（如果有）</param>
        /// <returns>生成的描述数据</returns>
        public async Task<ActionDescriptionResult> GenerateActionDescriptionAsync(
            string actionTypeName,
            string actionCode,
            string existingDisplayName = null,
            string existingCategory = null)
        {
            // 使用配置中的Prompt模板构建提示词
            string prompt = config.BuildPrompt(actionTypeName, actionCode, existingDisplayName, existingCategory);

            // 调用API
            string response = await CallDeepSeekAPI(prompt);

            // 解析响应
            return ParseResponse(response, actionTypeName);
        }

        private async Task<string> CallDeepSeekAPI(string prompt)
        {
            // 从配置获取参数
            var requestBody = new ChatCompletionRequest
            {
                model = config.deepSeekModel,
                messages = new ChatMessage[]
                {
                    new ChatMessage { role = "user", content = prompt }
                },
                temperature = config.deepSeekTemperature,
                max_tokens = config.deepSeekMaxTokens
            };

            string jsonBody = JsonUtility.ToJson(requestBody);

            // 创建请求
            using (UnityWebRequest request = new UnityWebRequest(config.deepSeekApiUrl, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.SetRequestHeader("Authorization", $"Bearer {apiKey}");

                // 发送请求
                var operation = request.SendWebRequest();

                // 等待完成（使用TaskCompletionSource实现async/await）
                var tcs = new TaskCompletionSource<bool>();
                operation.completed += _ => tcs.SetResult(true);
                await tcs.Task;

                // 检查错误
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
