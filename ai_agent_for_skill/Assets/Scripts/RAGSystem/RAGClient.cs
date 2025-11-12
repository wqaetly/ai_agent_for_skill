using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace SkillSystem.RAG
{
    /// <summary>
    /// RAG服务HTTP客户�?
    /// 负责与Python RAG服务通信
    /// </summary>
    public class RAGClient
    {
        private string baseUrl;
        private int timeout;

        /// <summary>
        /// 构造函�?
        /// </summary>
        /// <param name="host">服务器地址</param>
        /// <param name="port">服务器端�?/param>
        /// <param name="timeout">请求超时时间（秒�?/param>
        public RAGClient(string host = "127.0.0.1", int port = 8765, int timeout = 30)
        {
            this.baseUrl = $"http://{host}:{port}";
            this.timeout = timeout;
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

        #endregion

        #region API方法

        /// <summary>
        /// 健康检�?
        /// </summary>
        public IEnumerator CheckHealth(Action<bool, string> callback)
        {
            string url = $"{baseUrl}/health";

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                request.timeout = timeout;
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        var response = JsonUtility.FromJson<HealthResponse>(request.downloadHandler.text);
                        callback?.Invoke(true, response.status);
                    }
                    catch (Exception e)
                    {
                        callback?.Invoke(false, $"Parse error: {e.Message}");
                    }
                }
                else
                {
                    callback?.Invoke(false, $"Connection error: {request.error}");
                }
            }
        }

        /// <summary>
        /// 搜索技�?
        /// </summary>
        public IEnumerator SearchSkills(
            string query,
            int? topK = null,
            bool returnDetails = false,
            Action<bool, SearchResponse, string> callback = null)
        {
            string url = $"{baseUrl}/search?q={UnityWebRequest.EscapeURL(query)}";

            if (topK.HasValue)
                url += $"&top_k={topK.Value}";

            if (returnDetails)
                url += "&details=true";

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                request.timeout = timeout;
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        string json = request.downloadHandler.text;
                        var response = JsonUtility.FromJson<SearchResponse>(json);
                        callback?.Invoke(true, response, null);
                    }
                    catch (Exception e)
                    {
                        callback?.Invoke(false, null, $"Parse error: {e.Message}");
                    }
                }
                else
                {
                    callback?.Invoke(false, null, $"Request error: {request.error}");
                }
            }
        }

        /// <summary>
        /// 推荐Action
        /// </summary>
        public IEnumerator RecommendActions(
            string context,
            int topK = 3,
            Action<bool, RecommendResponse, string> callback = null)
        {
            string url = $"{baseUrl}/recommend";

            var requestData = new RecommendRequest
            {
                context = context,
                top_k = topK
            };

            string json = JsonUtility.ToJson(requestData);
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.timeout = timeout;

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        string responseJson = request.downloadHandler.text;
                        var response = JsonUtility.FromJson<RecommendResponse>(responseJson);
                        callback?.Invoke(true, response, null);
                    }
                    catch (Exception e)
                    {
                        callback?.Invoke(false, null, $"Parse error: {e.Message}");
                    }
                }
                else
                {
                    callback?.Invoke(false, null, $"Request error: {request.error}");
                }
            }
        }

        /// <summary>
        /// 触发索引
        /// </summary>
        public IEnumerator TriggerIndex(
            bool forceRebuild = false,
            Action<bool, IndexResponse, string> callback = null)
        {
            string url = $"{baseUrl}/index";

            var requestData = new IndexRequest
            {
                force_rebuild = forceRebuild
            };

            string json = JsonUtility.ToJson(requestData);
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.timeout = timeout;

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        string responseJson = request.downloadHandler.text;
                        var response = JsonUtility.FromJson<IndexResponse>(responseJson);
                        callback?.Invoke(true, response, null);
                    }
                    catch (Exception e)
                    {
                        callback?.Invoke(false, null, $"Parse error: {e.Message}");
                    }
                }
                else
                {
                    callback?.Invoke(false, null, $"Request error: {request.error}");
                }
            }
        }

        /// <summary>
        /// 获取统计信息
        /// </summary>
        public IEnumerator GetStatistics(Action<bool, StatsResponse, string> callback)
        {
            string url = $"{baseUrl}/stats";

            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                request.timeout = timeout;
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        string json = request.downloadHandler.text;
                        var response = JsonUtility.FromJson<StatsResponse>(json);
                        callback?.Invoke(true, response, null);
                    }
                    catch (Exception e)
                    {
                        callback?.Invoke(false, null, $"Parse error: {e.Message}");
                    }
                }
                else
                {
                    callback?.Invoke(false, null, $"Request error: {request.error}");
                }
            }
        }

        /// <summary>
        /// 清空缓存
        /// </summary>
        public IEnumerator ClearCache(Action<bool, string> callback)
        {
            string url = $"{baseUrl}/clear-cache";

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                request.downloadHandler = new DownloadHandlerBuffer();
                request.timeout = timeout;

                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    callback?.Invoke(true, "Cache cleared successfully");
                }
                else
                {
                    callback?.Invoke(false, $"Request error: {request.error}");
                }
            }
        }

        #endregion
    }
}
