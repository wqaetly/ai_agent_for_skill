using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// RAG服务HTTP客户端 - Editor专用版本
    /// 使用标准.NET HttpClient，支持async/await，可靠性更高
    /// </summary>
    public class EditorRAGClient
    {
        private readonly HttpClient httpClient;
        private readonly string baseUrl;
        private readonly int timeout;

        /// <summary>
        /// 构造函数
        /// </summary>
        /// <param name="host">服务器地址</param>
        /// <param name="port">服务器端口</param>
        /// <param name="timeout">请求超时时间（秒）</param>
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
            public string action_type;
            public int frequency;
            public List<ActionExample> examples;
        }

        [Serializable]
        public class ActionExample
        {
            public string skill_name;
            public Dictionary<string, object> parameters;
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

        #endregion

        #region 同步API方法

        /// <summary>
        /// 健康检查（同步）
        /// </summary>
        public bool CheckHealth(out string status)
        {
            try
            {
                var task = CheckHealthAsync();
                task.Wait();
                status = task.Result;
                return true;
            }
            catch (Exception e)
            {
                status = $"Connection error: {e.Message}";
                return false;
            }
        }

        /// <summary>
        /// 搜索技能（同步）
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
                var task = SearchSkillsAsync(query, topK, returnDetails);
                task.Wait();
                response = task.Result;
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
                var task = RecommendActionsAsync(context, topK);
                task.Wait();
                response = task.Result;
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
                var task = TriggerIndexAsync(forceRebuild);
                task.Wait();
                response = task.Result;
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
                var task = GetStatisticsAsync();
                task.Wait();
                response = task.Result;
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
                var task = ClearCacheAsync();
                task.Wait();
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
        /// 健康检查（异步）
        /// </summary>
        public async Task<string> CheckHealthAsync()
        {
            string url = $"{baseUrl}/health";

            var response = await httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();

            string json = await response.Content.ReadAsStringAsync();
            var healthResponse = JsonUtility.FromJson<HealthResponse>(json);
            return healthResponse.status;
        }

        /// <summary>
        /// 搜索技能（异步）
        /// </summary>
        public async Task<SearchResponse> SearchSkillsAsync(
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
        public async Task<RecommendResponse> RecommendActionsAsync(
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
        public async Task<IndexResponse> TriggerIndexAsync(bool forceRebuild = false)
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
        public async Task<StatsResponse> GetStatisticsAsync()
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
        public async Task ClearCacheAsync()
        {
            string url = $"{baseUrl}/clear-cache";

            var content = new StringContent("", Encoding.UTF8, "application/json");
            var response = await httpClient.PostAsync(url, content);
            response.EnsureSuccessStatusCode();
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
