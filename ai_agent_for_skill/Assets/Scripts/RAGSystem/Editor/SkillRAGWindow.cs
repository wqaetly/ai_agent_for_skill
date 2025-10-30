using System;
using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// 技能RAG查询窗口
    /// 提供技能搜索和Action推荐功能
    /// </summary>
    public class SkillRAGWindow : EditorWindow
    {
        private EditorRAGClient client;

        // 服务器配置
        private string serverHost = "127.0.0.1";
        private int serverPort = 8765;
        private bool isConnected = false;

        // 搜索相关
        private string searchQuery = "";
        private int searchTopK = 5;
        private bool searchReturnDetails = true;
        private List<EditorRAGClient.SearchResult> searchResults = new List<EditorRAGClient.SearchResult>();
        private Vector2 searchScrollPos;

        // 推荐相关
        private string recommendContext = "";
        private int recommendTopK = 3;
        private List<EditorRAGClient.ActionRecommendation> recommendations = new List<EditorRAGClient.ActionRecommendation>();
        private Vector2 recommendScrollPos;

        // UI状态
        private int selectedTab = 0;
        private string[] tabNames = { "技能搜索", "Action推荐", "管理" };
        private string statusMessage = "";
        private bool isLoading = false;

        [MenuItem("技能系统/RAG查询窗口", false, 102)]
        public static void ShowWindow()
        {
            var window = GetWindow<SkillRAGWindow>("技能RAG");
            window.minSize = new Vector2(600, 400);
            window.Show();
        }

        private void OnEnable()
        {
            client = new EditorRAGClient(serverHost, serverPort);
            // 延迟执行连接检查，避免阻塞主线程
            EditorApplication.delayCall += () => CheckConnectionAsync();
        }

        private void OnDisable()
        {
            client?.Dispose();
        }

        private void OnGUI()
        {
            DrawToolbar();

            EditorGUILayout.Space(5);

            // Tab选择
            selectedTab = GUILayout.Toolbar(selectedTab, tabNames);

            EditorGUILayout.Space(10);

            switch (selectedTab)
            {
                case 0:
                    DrawSearchTab();
                    break;
                case 1:
                    DrawRecommendTab();
                    break;
                case 2:
                    DrawManagementTab();
                    break;
            }

            // 状态栏
            DrawStatusBar();
        }

        private void DrawToolbar()
        {
            EditorGUILayout.BeginHorizontal(EditorStyles.toolbar);

            // 连接状态
            GUIStyle statusStyle = new GUIStyle(EditorStyles.label);
            statusStyle.normal.textColor = isConnected ? Color.green : Color.red;
            GUILayout.Label(isConnected ? "● 已连接" : "● 未连接", statusStyle);

            GUILayout.FlexibleSpace();

            // 服务器配置
            GUILayout.Label("服务器:", GUILayout.Width(45));
            serverHost = EditorGUILayout.TextField(serverHost, GUILayout.Width(100));
            serverPort = EditorGUILayout.IntField(serverPort, GUILayout.Width(50));

            if (GUILayout.Button("连接", EditorStyles.toolbarButton, GUILayout.Width(50)))
            {
                client?.Dispose();
                client = new EditorRAGClient(serverHost, serverPort);
                CheckConnectionAsync();
            }

            EditorGUILayout.EndHorizontal();
        }

        private void DrawSearchTab()
        {
            EditorGUILayout.BeginVertical("box");

            EditorGUILayout.LabelField("技能搜索", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            // 搜索输入
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField("搜索查询:", GUILayout.Width(70));
            searchQuery = EditorGUILayout.TextField(searchQuery);
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField("返回数量:", GUILayout.Width(70));
            searchTopK = EditorGUILayout.IntSlider(searchTopK, 1, 20);
            EditorGUILayout.EndHorizontal();

            searchReturnDetails = EditorGUILayout.Toggle("返回详细信息", searchReturnDetails);

            EditorGUILayout.Space(5);

            // 搜索按钮
            GUI.enabled = !isLoading && !string.IsNullOrWhiteSpace(searchQuery) && isConnected;
            if (GUILayout.Button("搜索", GUILayout.Height(30)))
            {
                PerformSearch();
            }
            GUI.enabled = true;

            EditorGUILayout.EndVertical();

            EditorGUILayout.Space(10);

            // 搜索结果
            if (searchResults.Count > 0)
            {
                EditorGUILayout.LabelField($"搜索结果 ({searchResults.Count})", EditorStyles.boldLabel);

                searchScrollPos = EditorGUILayout.BeginScrollView(searchScrollPos);

                foreach (var result in searchResults)
                {
                    DrawSearchResult(result);
                    EditorGUILayout.Space(5);
                }

                EditorGUILayout.EndScrollView();
            }
            else if (!string.IsNullOrEmpty(searchQuery) && !isLoading)
            {
                EditorGUILayout.HelpBox("没有找到匹配的技能", MessageType.Info);
            }
        }

        private void DrawSearchResult(EditorRAGClient.SearchResult result)
        {
            EditorGUILayout.BeginVertical("box");

            // 标题行
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField(result.skill_name, EditorStyles.boldLabel);
            GUILayout.FlexibleSpace();

            // 相似度标签
            Color originalColor = GUI.backgroundColor;
            GUI.backgroundColor = result.similarity >= 0.8f ? Color.green :
                                  result.similarity >= 0.6f ? Color.yellow : Color.red;
            GUILayout.Label($"相似度: {result.similarity:P0}", EditorStyles.miniButton, GUILayout.Width(80));
            GUI.backgroundColor = originalColor;

            EditorGUILayout.EndHorizontal();

            // 详细信息
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField("技能ID:", GUILayout.Width(60));
            EditorGUILayout.SelectableLabel(result.skill_id, GUILayout.Height(16));
            EditorGUILayout.EndHorizontal();

            if (searchReturnDetails)
            {
                EditorGUILayout.BeginHorizontal();
                EditorGUILayout.LabelField("文件:", GUILayout.Width(60));
                EditorGUILayout.SelectableLabel(result.file_name, GUILayout.Height(16));
                EditorGUILayout.EndHorizontal();

                EditorGUILayout.BeginHorizontal();
                EditorGUILayout.LabelField("统计:", GUILayout.Width(60));
                EditorGUILayout.LabelField($"{result.num_tracks} 轨道, {result.num_actions} 动作, {result.total_duration}帧");
                EditorGUILayout.EndHorizontal();
            }

            // 操作按钮
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("打开技能文件", GUILayout.Height(25)))
            {
                OpenSkillFile(result.file_path);
            }
            if (GUILayout.Button("复制ID", GUILayout.Width(80), GUILayout.Height(25)))
            {
                EditorGUIUtility.systemCopyBuffer = result.skill_id;
                ShowNotification(new GUIContent("已复制ID"));
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.EndVertical();
        }

        private void DrawRecommendTab()
        {
            EditorGUILayout.BeginVertical("box");

            EditorGUILayout.LabelField("Action推荐", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            // 上下文输入
            EditorGUILayout.LabelField("描述你想要的效果:", EditorStyles.label);
            recommendContext = EditorGUILayout.TextArea(recommendContext, GUILayout.Height(60));

            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField("推荐数量:", GUILayout.Width(70));
            recommendTopK = EditorGUILayout.IntSlider(recommendTopK, 1, 10);
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(5);

            // 推荐按钮
            GUI.enabled = !isLoading && !string.IsNullOrWhiteSpace(recommendContext) && isConnected;
            if (GUILayout.Button("获取推荐", GUILayout.Height(30)))
            {
                PerformRecommend();
            }
            GUI.enabled = true;

            EditorGUILayout.EndVertical();

            EditorGUILayout.Space(10);

            // 推荐结果
            if (recommendations.Count > 0)
            {
                EditorGUILayout.LabelField($"推荐的Action类型 ({recommendations.Count})", EditorStyles.boldLabel);

                recommendScrollPos = EditorGUILayout.BeginScrollView(recommendScrollPos);

                foreach (var recommendation in recommendations)
                {
                    DrawRecommendation(recommendation);
                    EditorGUILayout.Space(5);
                }

                EditorGUILayout.EndScrollView();
            }
            else if (!string.IsNullOrEmpty(recommendContext) && !isLoading)
            {
                EditorGUILayout.HelpBox("没有找到合适的推荐", MessageType.Info);
            }
        }

        private void DrawRecommendation(EditorRAGClient.ActionRecommendation recommendation)
        {
            EditorGUILayout.BeginVertical("box");

            // Action类型标题
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField(recommendation.action_type, EditorStyles.boldLabel);
            GUILayout.FlexibleSpace();
            GUILayout.Label($"出现 {recommendation.frequency} 次", EditorStyles.miniLabel);
            EditorGUILayout.EndHorizontal();

            // 示例
            if (recommendation.examples != null && recommendation.examples.Count > 0)
            {
                EditorGUILayout.LabelField("参数示例:", EditorStyles.miniLabel);

                foreach (var example in recommendation.examples)
                {
                    EditorGUI.indentLevel++;
                    EditorGUILayout.LabelField($"来自: {example.skill_name}", EditorStyles.miniLabel);

                    if (example.parameters != null && example.parameters.Count > 0)
                    {
                        EditorGUI.indentLevel++;
                        foreach (var param in example.parameters)
                        {
                            EditorGUILayout.LabelField($"{param.Key}: {param.Value}", EditorStyles.miniLabel);
                        }
                        EditorGUI.indentLevel--;
                    }
                    EditorGUI.indentLevel--;
                }
            }

            // 操作按钮
            if (GUILayout.Button($"在编辑器中添加 {recommendation.action_type}", GUILayout.Height(25)))
            {
                // TODO: 集成到SkillEditor，自动添加Action
                ShowNotification(new GUIContent($"添加 {recommendation.action_type} 功能待实现"));
            }

            EditorGUILayout.EndVertical();
        }

        private void DrawManagementTab()
        {
            EditorGUILayout.BeginVertical("box");

            EditorGUILayout.LabelField("索引管理", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            EditorGUILayout.HelpBox("管理技能索引，重建索引会扫描所有技能文件并更新向量数据库。", MessageType.Info);

            EditorGUILayout.Space(5);

            EditorGUILayout.BeginHorizontal();

            GUI.enabled = !isLoading && isConnected;
            if (GUILayout.Button("更新索引", GUILayout.Height(35)))
            {
                TriggerIndex(false);
            }

            if (GUILayout.Button("重建索引", GUILayout.Height(35)))
            {
                if (EditorUtility.DisplayDialog("确认", "重建索引会清空现有数据并重新索引所有技能，是否继续？", "确定", "取消"))
                {
                    TriggerIndex(true);
                }
            }
            GUI.enabled = true;

            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(10);

            if (GUILayout.Button("清空缓存", GUILayout.Height(30)))
            {
                ClearCache();
            }

            if (GUILayout.Button("获取统计信息", GUILayout.Height(30)))
            {
                GetStatistics();
            }

            EditorGUILayout.EndVertical();

            EditorGUILayout.Space(10);

            // 快速链接
            EditorGUILayout.BeginVertical("box");
            EditorGUILayout.LabelField("快速链接", EditorStyles.boldLabel);

            if (GUILayout.Button("打开API文档"))
            {
                Application.OpenURL($"http://{serverHost}:{serverPort}/docs");
            }

            if (GUILayout.Button("打开技能文件夹"))
            {
                EditorUtility.RevealInFinder(Application.dataPath + "/Skills");
            }

            EditorGUILayout.EndVertical();
        }

        private void DrawStatusBar()
        {
            EditorGUILayout.Space(5);

            EditorGUILayout.BeginHorizontal(EditorStyles.helpBox);

            if (isLoading)
            {
                GUILayout.Label("处理中...", EditorStyles.miniLabel);
            }
            else if (!string.IsNullOrEmpty(statusMessage))
            {
                GUILayout.Label(statusMessage, EditorStyles.miniLabel);
            }
            else
            {
                GUILayout.Label("就绪", EditorStyles.miniLabel);
            }

            GUILayout.FlexibleSpace();

            EditorGUILayout.EndHorizontal();
        }

        #region API调用

        /// <summary>
        /// 异步检查连接（不阻塞主线程）
        /// </summary>
        private async void CheckConnectionAsync()
        {
            statusMessage = "正在连接...";
            isLoading = true;
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                string status = await System.Threading.Tasks.Task.Run(() =>
                {
                    return client.CheckHealthAsync().Result;
                });

                isConnected = true;
                statusMessage = $"已连接到RAG服务 ({status})";
            }
            catch (Exception e)
            {
                isConnected = false;
                statusMessage = $"连接失败: {e.InnerException?.Message ?? e.Message}";
                Debug.LogError($"[RAG] Connection error: {e}");
            }
            finally
            {
                isLoading = false;
                Repaint();
            }
        }

        private async void PerformSearch()
        {
            statusMessage = "正在搜索...";
            isLoading = true;
            searchResults.Clear();
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await System.Threading.Tasks.Task.Run(() =>
                {
                    return client.SearchSkillsAsync(searchQuery, searchTopK, searchReturnDetails).Result;
                });

                searchResults = response.results ?? new List<EditorRAGClient.SearchResult>();
                statusMessage = $"找到 {searchResults.Count} 个结果";
            }
            catch (Exception e)
            {
                statusMessage = $"搜索失败: {e.InnerException?.Message ?? e.Message}";
                Debug.LogError($"[RAG] Search error: {e}");
            }
            finally
            {
                isLoading = false;
                Repaint();
            }
        }

        private async void PerformRecommend()
        {
            statusMessage = "正在获取推荐...";
            isLoading = true;
            recommendations.Clear();
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await System.Threading.Tasks.Task.Run(() =>
                {
                    return client.RecommendActionsAsync(recommendContext, recommendTopK).Result;
                });

                recommendations = response.recommendations ?? new List<EditorRAGClient.ActionRecommendation>();
                statusMessage = $"获得 {recommendations.Count} 个推荐";
            }
            catch (Exception e)
            {
                statusMessage = $"推荐失败: {e.InnerException?.Message ?? e.Message}";
                Debug.LogError($"[RAG] Recommend error: {e}");
            }
            finally
            {
                isLoading = false;
                Repaint();
            }
        }

        private async void TriggerIndex(bool forceRebuild)
        {
            statusMessage = "正在索引...";
            isLoading = true;
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await System.Threading.Tasks.Task.Run(() =>
                {
                    return client.TriggerIndexAsync(forceRebuild).Result;
                });

                statusMessage = $"索引完成: {response.count} 个技能 ({response.elapsed_time:F2}秒)";
                EditorUtility.DisplayDialog("索引完成", statusMessage, "确定");
            }
            catch (Exception e)
            {
                string errorMsg = e.InnerException?.Message ?? e.Message;
                statusMessage = $"索引失败: {errorMsg}";
                EditorUtility.DisplayDialog("索引失败", errorMsg, "确定");
                Debug.LogError($"[RAG] Index error: {e}");
            }
            finally
            {
                isLoading = false;
                Repaint();
            }
        }

        private async void ClearCache()
        {
            statusMessage = "正在清空缓存...";
            isLoading = true;
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                await System.Threading.Tasks.Task.Run(() =>
                {
                    return client.ClearCacheAsync();
                });

                statusMessage = "缓存已清空";
            }
            catch (Exception e)
            {
                statusMessage = $"清空缓存失败: {e.InnerException?.Message ?? e.Message}";
                Debug.LogError($"[RAG] Clear cache error: {e}");
            }
            finally
            {
                isLoading = false;
                Repaint();
            }
        }

        private async void GetStatistics()
        {
            statusMessage = "正在获取统计...";
            isLoading = true;
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await System.Threading.Tasks.Task.Run(() =>
                {
                    return client.GetStatisticsAsync().Result;
                });

                statusMessage = "统计信息已获取";
                Debug.Log($"RAG统计: {response.statistics}");
            }
            catch (Exception e)
            {
                statusMessage = $"获取统计失败: {e.InnerException?.Message ?? e.Message}";
                Debug.LogError($"[RAG] Get statistics error: {e}");
            }
            finally
            {
                isLoading = false;
                Repaint();
            }
        }

        #endregion

        private void OpenSkillFile(string filePath)
        {
            if (string.IsNullOrEmpty(filePath))
                return;

            // 转换为Unity资产路径
            string assetPath = filePath.Replace("\\", "/");

            // 如果是绝对路径，尝试转换为相对路径
            if (System.IO.Path.IsPathRooted(assetPath))
            {
                string dataPath = Application.dataPath;
                if (assetPath.StartsWith(dataPath))
                {
                    assetPath = "Assets" + assetPath.Substring(dataPath.Length);
                }
            }

            // 打开技能编辑器
            var skillData = SkillSystem.Data.SkillDataSerializer.LoadFromFile(assetPath);
            if (skillData != null)
            {
                SkillSystem.Editor.SkillEditorWindow.OpenSkill(skillData);
            }
            else
            {
                EditorUtility.DisplayDialog("错误", $"无法加载技能文件: {assetPath}", "确定");
            }
        }
    }

}
