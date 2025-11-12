using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// RAG服务HTTP客户�?- Editor专用版本
    /// 使用UniTask进行异步操作，避免Unity线程问题
    /// </summary>
    public class EditorRAGClient: IDisposable
    {
        private readonly HttpClient httpClient;
        private readonly string baseUrl;
        private readonly int timeout;

        /// <summary>
        /// 构造函�?
        /// </summary>
        /// <param name="host">服务器地址</param>
        /// <param name="port">服务器端�?/param>
        /// <param name="timeout">请求超时时间（秒�?/param>
        public EditorRAGClient(string host = "127.0.0.1", int port = 8765, int timeout = 30)
        {
            this.baseUrl = $"http://{host}:{port}";
            this.timeout = timeout;

            // 创建HttpClient实例
            httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(timeout)
            };
        }

        #region 数据模型

        [Serializable]
        public class SearchRequest
        {
            public string query;
            public int? top_k;
            public Dictionary<string, object> filters;
            public bool return_details;
        }

        [Serializable]
        public class SearchResponse
        {
            public List<SearchResult> results;
            public string query;
            public int count;
            public string timestamp;
        }

        [Serializable]
        public class SearchResult
        {
            public string skill_id;
            public string skill_name;
            public string file_name;
            public float similarity;
            public float distance;
            public string file_path;
            public int total_duration;
            public int frame_rate;
            public int num_tracks;
            public int num_actions;
            public string last_modified;
            public string search_text_preview;
        }

        [Serializable]
        public class RecommendRequest
        {
            public string context;
            public int top_k = 3;
        }

        [Serializable]
        public class RecommendResponse
        {
            public List<ActionRecommendation> recommendations;
            public string context;
            public int count;
        }

        [Serializable]
        public class ActionRecommendation
        {
            public string action_type;              // Action类型名（如DamageAction�?
            public string display_name;             // 显示名称（如"伤害"�?
            public string category;                 // 分类（如"Damage"�?
            public string description;              // 功能描述
            public float semantic_similarity;       // 语义相似度（0-1�?
        }

        [Serializable]
        public class IndexRequest
        {
            public bool force_rebuild = false;
        }

        [Serializable]
        public class IndexResponse
        {
            public string status;
            public int count;
            public float? elapsed_time;
            public string message;
        }

        [Serializable]
        public class HealthResponse
        {
            public string status;
            public string timestamp;
        }

        [Serializable]
        public class StatsResponse
        {
            public Dictionary<string, object> statistics;
            public string timestamp;
        }

        // ========== REQ-04 数据模型 ==========

        [Serializable]
        public class ActionContext
        {
            public string skill_name;
            public string track_name;
            public int track_index;
            public int frame;
            public List<ExistingActionInfo> existing_actions;
        }

        [Serializable]
        public class ExistingActionInfo
        {
            public string action_type;
            public int frame;
            public int duration;
        }

        [Serializable]
        public class RecommendParametersRequest
        {
            public string action_type;
            public ActionContext context;
            public int top_k;
            public bool include_reasoning;
        }

        [Serializable]
        public class RecommendParametersResponse
        {
            public string action_type;
            public List<ParameterRecommendation> recommendations;
            public int count;
            public string timestamp;
        }

        [Serializable]
        public class ParameterRecommendation
        {
            public string source_skill;
            public string source_file;
            public string json_path;
            public float similarity;
            public Dictionary<string, object> parameters;
            public string reasoning;
        }

        [Serializable]
        public class ValidateParametersRequest
        {
            public string action_type;
            public Dictionary<string, object> parameters;
            public ActionContext context;
        }

        [Serializable]
        public class ValidateParametersResponse
        {
            public bool valid;
            public List<ValidationIssue> warnings;
            public List<ValidationIssue> errors;
            public List<ParameterSuggestion> suggestions;
        }

        [Serializable]
        public class ValidationIssue
        {
            public string field;
            public string level;
            public string message;
        }

        [Serializable]
        public class ParameterSuggestion
        {
            public string field;
            public object current;
            public object suggested;
            public string reason;
        }

        [Serializable]
        public class CompareParametersRequest
        {
            public string action_type;
            public Dictionary<string, object> current_parameters;
            public Dictionary<string, object> recommended_parameters;
        }

        [Serializable]
        public class CompareParametersResponse
        {
            public List<ParameterDifference> differences;
            public int total_changes;
            public string risk_level;
        }

        [Serializable]
        public class ParameterDifference
        {
            public string field;
            public object current;
            public object recommended;
            public string change_type;
            public string significance;
        }

        [Serializable]
        public class LogOperationRequest
        {
            public string operation;
            public string skill_file;
            public int track_index;
            public int action_index;
            public string action_type;
            public Dictionary<string, object> old_parameters;
            public Dictionary<string, object> new_parameters;
            public string user;
            public string session_id;
        }

        [Serializable]
        public class LogOperationResponse
        {
            public string log_id;
            public string status;
            public string message;
        }

        [Serializable]
        public class OperationHistoryResponse
        {
            public List<OperationLog> operations;
            public int count;
            public string timestamp;
        }

        [Serializable]
        public class OperationLog
        {
            public string log_id;
            public string operation;
            public string timestamp;
            public string action_type;
            public string changes_summary;
            public string skill_file;
            public int track_index;
            public int action_index;
        }

        #endregion

        #region 同步API方法

        /// <summary>
        /// 健康检查（同步�?
        /// </summary>
        public bool CheckHealth(out string status)
        {
            try
            {
                status = CheckHealthAsync().GetAwaiter().GetResult();
                return true;
            }
            catch (Exception e)
            {
                status = $"Connection error: {e.Message}";
                return false;
            }
        }

        /// <summary>
        /// 搜索技能（同步�?
        /// </summary>
        public bool SearchSkills(
            string query,
            out SearchResponse response,
            out string error,
            int? topK = null,
            bool returnDetails = false)
        {
            try
            {
                response = SearchSkillsAsync(query, topK, returnDetails).GetAwaiter().GetResult();
                error = null;
                return true;
            }
            catch (Exception e)
            {
                response = null;
                error = $"Request error: {e.Message}";
                return false;
            }
        }

        /// <summary>
        /// 推荐Action（同步）
        /// </summary>
        public bool RecommendActions(
            string context,
            out RecommendResponse response,
            out string error,
            int topK = 3)
        {
            try
            {
                response = RecommendActionsAsync(context, topK).GetAwaiter().GetResult();
                error = null;
                return true;
            }
            catch (Exception e)
            {
                response = null;
                error = $"Request error: {e.Message}";
                return false;
            }
        }

        /// <summary>
        /// 触发索引（同步）
        /// </summary>
        public bool TriggerIndex(
            bool forceRebuild,
            out IndexResponse response,
            out string error)
        {
            try
            {
                response = TriggerIndexAsync(forceRebuild).GetAwaiter().GetResult();
                error = null;
                return true;
            }
            catch (Exception e)
            {
                response = null;
                error = $"Request error: {e.Message}";
                return false;
            }
        }

        /// <summary>
        /// 获取统计信息（同步）
        /// </summary>
        public bool GetStatistics(out StatsResponse response, out string error)
        {
            try
            {
                response = GetStatisticsAsync().GetAwaiter().GetResult();
                error = null;
                return true;
            }
            catch (Exception e)
            {
                response = null;
                error = $"Request error: {e.Message}";
                return false;
            }
        }

        /// <summary>
        /// 清空缓存（同步）
        /// </summary>
        public bool ClearCache(out string message)
        {
            try
            {
                ClearCacheAsync().GetAwaiter().GetResult();
                message = "Cache cleared successfully";
                return true;
            }
            catch (Exception e)
            {
                message = $"Request error: {e.Message}";
                return false;
            }
        }

        #endregion

        #region 异步API方法

        /// <summary>
        /// 健康检查（异步�?
        /// </summary>
        public async UniTask<string> CheckHealthAsync()
        {
            string url = $"{baseUrl}/health";

            var response = await httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();

            string json = await response.Content.ReadAsStringAsync();
            var healthResponse = JsonUtility.FromJson<HealthResponse>(json);
            return healthResponse.status;
        }

        /// <summary>
        /// 搜索技能（异步�?
        /// </summary>
        public async UniTask<SearchResponse> SearchSkillsAsync(
            string query,
            int? topK = null,
            bool returnDetails = false)
        {
            string url = $"{baseUrl}/search?q={Uri.EscapeDataString(query)}";

            if (topK.HasValue)
                url += $"&top_k={topK.Value}";

            if (returnDetails)
                url += "&details=true";

            var response = await httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();

            string json = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<SearchResponse>(json);
        }

        /// <summary>
        /// 推荐Action（异步）
        /// </summary>
        public async UniTask<RecommendResponse> RecommendActionsAsync(
            string context,
            int topK = 3)
        {
            string url = $"{baseUrl}/recommend";

            var requestData = new RecommendRequest
            {
                context = context,
                top_k = topK
            };

            string json = JsonUtility.ToJson(requestData);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(url, content);
            response.EnsureSuccessStatusCode();

            string responseJson = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<RecommendResponse>(responseJson);
        }

        /// <summary>
        /// 触发索引（异步）
        /// </summary>
        public async UniTask<IndexResponse> TriggerIndexAsync(bool forceRebuild = false)
        {
            string url = $"{baseUrl}/index";

            var requestData = new IndexRequest
            {
                force_rebuild = forceRebuild
            };

            string json = JsonUtility.ToJson(requestData);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(url, content);
            response.EnsureSuccessStatusCode();

            string responseJson = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<IndexResponse>(responseJson);
        }

        /// <summary>
        /// 获取统计信息（异步）
        /// </summary>
        public async UniTask<StatsResponse> GetStatisticsAsync()
        {
            string url = $"{baseUrl}/stats";

            var response = await httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();

            string json = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<StatsResponse>(json);
        }

        /// <summary>
        /// 清空缓存（异步）
        /// </summary>
        public async UniTask ClearCacheAsync()
        {
            string url = $"{baseUrl}/clear-cache";

            var content = new StringContent("", Encoding.UTF8, "application/json");
            var response = await httpClient.PostAsync(url, content);
            response.EnsureSuccessStatusCode();
        }

        #endregion

        #region REQ-04 异步API方法

        /// <summary>
        /// 推荐Action参数（异步）
        /// </summary>
        public async UniTask<RecommendParametersResponse> RecommendParametersAsync(
            string actionType,
            ActionContext context,
            int topK = 5,
            bool includeReasoning = true)
        {
            string url = $"{baseUrl}/recommend_parameters";

            var requestData = new RecommendParametersRequest
            {
                action_type = actionType,
                context = context,
                top_k = topK,
                include_reasoning = includeReasoning
            };

            string json = JsonUtility.ToJson(requestData);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(url, content);
            response.EnsureSuccessStatusCode();

            string responseJson = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<RecommendParametersResponse>(responseJson);
        }

        /// <summary>
        /// 验证Action参数（异步）
        /// </summary>
        public async UniTask<ValidateParametersResponse> ValidateParametersAsync(
            string actionType,
            Dictionary<string, object> parameters,
            ActionContext context = null)
        {
            string url = $"{baseUrl}/validate_parameters";

            var requestData = new ValidateParametersRequest
            {
                action_type = actionType,
                parameters = parameters,
                context = context
            };

            string json = JsonUtility.ToJson(requestData);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(url, content);
            response.EnsureSuccessStatusCode();

            string responseJson = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<ValidateParametersResponse>(responseJson);
        }

        /// <summary>
        /// 对比参数差异（异步）
        /// </summary>
        public async UniTask<CompareParametersResponse> CompareParametersAsync(
            string actionType,
            Dictionary<string, object> currentParameters,
            Dictionary<string, object> recommendedParameters)
        {
            string url = $"{baseUrl}/compare_parameters";

            var requestData = new CompareParametersRequest
            {
                action_type = actionType,
                current_parameters = currentParameters,
                recommended_parameters = recommendedParameters
            };

            string json = JsonUtility.ToJson(requestData);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(url, content);
            response.EnsureSuccessStatusCode();

            string responseJson = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<CompareParametersResponse>(responseJson);
        }

        /// <summary>
        /// 记录操作日志（异步）
        /// </summary>
        public async UniTask<LogOperationResponse> LogOperationAsync(
            string operation,
            string skillFile = null,
            int? trackIndex = null,
            int? actionIndex = null,
            string actionType = null,
            Dictionary<string, object> oldParameters = null,
            Dictionary<string, object> newParameters = null,
            string user = "Unity Editor",
            string sessionId = null)
        {
            string url = $"{baseUrl}/log_operation";

            var requestData = new LogOperationRequest
            {
                operation = operation,
                skill_file = skillFile,
                track_index = trackIndex ?? -1,
                action_index = actionIndex ?? -1,
                action_type = actionType,
                old_parameters = oldParameters,
                new_parameters = newParameters,
                user = user,
                session_id = sessionId
            };

            string json = JsonUtility.ToJson(requestData);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(url, content);
            response.EnsureSuccessStatusCode();

            string responseJson = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<LogOperationResponse>(responseJson);
        }

        /// <summary>
        /// 获取操作历史（异步）
        /// </summary>
        public async UniTask<OperationHistoryResponse> GetOperationHistoryAsync(
            string skillFile = null,
            int limit = 20,
            string sessionId = null)
        {
            string url = $"{baseUrl}/operation_history?limit={limit}";

            if (!string.IsNullOrEmpty(skillFile))
                url += $"&skill_file={Uri.EscapeDataString(skillFile)}";

            if (!string.IsNullOrEmpty(sessionId))
                url += $"&session_id={Uri.EscapeDataString(sessionId)}";

            var response = await httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();

            string json = await response.Content.ReadAsStringAsync();
            return JsonUtility.FromJson<OperationHistoryResponse>(json);
        }

        #endregion

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            httpClient?.Dispose();
        }
    }
}
