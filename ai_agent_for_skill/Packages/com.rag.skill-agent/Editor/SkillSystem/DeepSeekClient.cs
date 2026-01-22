using System;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace RAG
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
            // 使用配置中的Prompt模板构建提示词（Action使用技能系统架构Prompt）
            string prompt = config.BuildPrompt(actionTypeName, actionCode, existingDisplayName, existingCategory, isBuffEffect: false);

            // 调用API
            string response = await CallDeepSeekAPI(prompt);

            // 解析响应
            return ParseResponse(response, actionTypeName);
        }

        /// <summary>
        /// 生成Buff效果描述
        /// </summary>
        /// <param name="buffTypeName">Buff效果类型名</param>
        /// <param name="buffCode">Buff效果源代码</param>
        /// <param name="existingDisplayName">现有的显示名称（如果有）</param>
        /// <param name="existingCategory">现有的分类（如果有）</param>
        /// <returns>生成的描述数据</returns>
        public async Task<ActionDescriptionResult> GenerateBuffDescriptionAsync(
            string buffTypeName,
            string buffCode,
            string existingDisplayName = null,
            string existingCategory = null)
        {
            // 使用配置中的Prompt模板构建提示词（Buff使用Buff系统架构Prompt）
            string prompt = config.BuildPrompt(buffTypeName, buffCode, existingDisplayName, existingCategory, isBuffEffect: true);

            // 调用API
            string response = await CallDeepSeekAPI(prompt);

            // 解析响应
            return ParseResponse(response, buffTypeName);
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
                
                // 手动解析parameterDescriptions字典
                result.RawParameterDescriptionsJson = ExtractParameterDescriptionsJson(content);
                
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
        
        /// <summary>
        /// 从JSON字符串中提取parameterDescriptions部分
        /// </summary>
        private string ExtractParameterDescriptionsJson(string jsonContent)
        {
            try
            {
                // 找到 "parameterDescriptions": { 的位置
                int startIndex = jsonContent.IndexOf("\"parameterDescriptions\"");
                if (startIndex < 0) return null;
                
                // 找到第一个 { 的位置
                int braceStart = jsonContent.IndexOf('{', startIndex);
                if (braceStart < 0) return null;
                
                // 找到匹配的 } 的位置
                int braceCount = 1;
                int braceEnd = braceStart + 1;
                while (braceEnd < jsonContent.Length && braceCount > 0)
                {
                    if (jsonContent[braceEnd] == '{') braceCount++;
                    else if (jsonContent[braceEnd] == '}') braceCount--;
                    braceEnd++;
                }
                
                if (braceCount == 0)
                {
                    return jsonContent.Substring(braceStart, braceEnd - braceStart);
                }
            }
            catch { }
            
            return null;
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
        
        /// <summary>
        /// 原始的参数描述JSON字符串（用于手动解析）
        /// </summary>
        [NonSerialized]
        public string RawParameterDescriptionsJson;
        
        /// <summary>
        /// 获取指定参数的描述
        /// </summary>
        /// <param name="parameterName">参数名</param>
        /// <returns>参数描述，如果不存在则返回null</returns>
        public string GetParameterDescription(string parameterName)
        {
            if (string.IsNullOrEmpty(RawParameterDescriptionsJson))
                return null;
                
            try
            {
                // 查找 "parameterName": "description" 模式
                string searchPattern = $"\"{parameterName}\"";
                int keyIndex = RawParameterDescriptionsJson.IndexOf(searchPattern);
                if (keyIndex < 0) return null;
                
                // 找到冒号后的引号
                int colonIndex = RawParameterDescriptionsJson.IndexOf(':', keyIndex);
                if (colonIndex < 0) return null;
                
                int valueStartQuote = RawParameterDescriptionsJson.IndexOf('"', colonIndex);
                if (valueStartQuote < 0) return null;
                
                // 找到结束引号（需要处理转义引号）
                int valueEndQuote = valueStartQuote + 1;
                while (valueEndQuote < RawParameterDescriptionsJson.Length)
                {
                    if (RawParameterDescriptionsJson[valueEndQuote] == '"' && 
                        RawParameterDescriptionsJson[valueEndQuote - 1] != '\\')
                    {
                        break;
                    }
                    valueEndQuote++;
                }
                
                if (valueEndQuote > valueStartQuote + 1)
                {
                    string value = RawParameterDescriptionsJson.Substring(
                        valueStartQuote + 1, 
                        valueEndQuote - valueStartQuote - 1);
                    // 处理转义字符
                    return value.Replace("\\\"", "\"").Replace("\\n", "\n");
                }
            }
            catch { }
            
            return null;
        }
        
        /// <summary>
        /// 获取所有参数描述
        /// </summary>
        /// <returns>参数名到描述的字典</returns>
        public System.Collections.Generic.Dictionary<string, string> GetAllParameterDescriptions()
        {
            var result = new System.Collections.Generic.Dictionary<string, string>();
            
            if (string.IsNullOrEmpty(RawParameterDescriptionsJson))
                return result;
                
            try
            {
                // 简单的JSON解析：找所有的 "key": "value" 模式
                int index = 0;
                while (index < RawParameterDescriptionsJson.Length)
                {
                    // 找到下一个key的开始引号
                    int keyStart = RawParameterDescriptionsJson.IndexOf('"', index);
                    if (keyStart < 0) break;
                    
                    int keyEnd = RawParameterDescriptionsJson.IndexOf('"', keyStart + 1);
                    if (keyEnd < 0) break;
                    
                    string key = RawParameterDescriptionsJson.Substring(keyStart + 1, keyEnd - keyStart - 1);
                    
                    // 找到冒号后的值
                    int colonIndex = RawParameterDescriptionsJson.IndexOf(':', keyEnd);
                    if (colonIndex < 0) break;
                    
                    int valueStart = RawParameterDescriptionsJson.IndexOf('"', colonIndex);
                    if (valueStart < 0) break;
                    
                    int valueEnd = valueStart + 1;
                    while (valueEnd < RawParameterDescriptionsJson.Length)
                    {
                        if (RawParameterDescriptionsJson[valueEnd] == '"' && 
                            RawParameterDescriptionsJson[valueEnd - 1] != '\\')
                        {
                            break;
                        }
                        valueEnd++;
                    }
                    
                    if (valueEnd > valueStart + 1)
                    {
                        string value = RawParameterDescriptionsJson.Substring(
                            valueStart + 1, 
                            valueEnd - valueStart - 1);
                        value = value.Replace("\\\"", "\"").Replace("\\n", "\n");
                        result[key] = value;
                    }
                    
                    index = valueEnd + 1;
                }
            }
            catch { }
            
            return result;
        }
    }
}
