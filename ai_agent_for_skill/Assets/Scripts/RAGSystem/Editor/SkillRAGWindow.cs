using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using Cysharp.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using SkillSystem.Data;
using SkillSystem.Editor;
using Debug = UnityEngine.Debug;

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

        // 服务器进程管理
        private Process serverProcess = null;
        private bool isServerRunning = false;
        private string serverOutput = "";

        // 定时ping相关
        private double lastPingTime = 0;
        private float pingInterval = 1.0f;  // ping间隔（秒）
        private bool isPinging = false;

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

            // 注册定时器用于定期ping服务器
            EditorApplication.update += OnEditorUpdate;

            // 延迟执行连接检查，避免阻塞主线程
            EditorApplication.delayCall += () => CheckConnectionAsync();
        }

        private void OnDisable()
        {
            // 注销定时器
            EditorApplication.update -= OnEditorUpdate;

            // 停止服务器进程
            StopServer();
            client?.Dispose();
        }

        /// <summary>
        /// 编辑器更新回调，用于定时ping服务器
        /// </summary>
        private void OnEditorUpdate()
        {
            // 检查是否到了ping的时间
            if (EditorApplication.timeSinceStartup - lastPingTime >= pingInterval)
            {
                lastPingTime = EditorApplication.timeSinceStartup;

                // 异步ping服务器
                if (!isPinging)
                {
                    PingServerAsync();
                }
            }
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

            // 服务器管理按钮 - 检查进程状态
            if (serverProcess != null && serverProcess.HasExited)
            {
                // 服务器进程意外退出
                isServerRunning = false;
                serverProcess.Dispose();
                serverProcess = null;
                if (isConnected)
                {
                    isConnected = false;
                    statusMessage = "服务器意外停止";
                }
            }

            if (isServerRunning)
            {
                // 服务器运行中
                GUIStyle runningStyle = new GUIStyle(EditorStyles.toolbarButton);
                runningStyle.normal.textColor = Color.green;
                if (GUILayout.Button("● 服务器运行中", runningStyle, GUILayout.Width(110)))
                {
                    // 点击可查看输出
                    Debug.Log($"[RAG Server] 输出:\n{serverOutput}");
                }

                if (GUILayout.Button("停止服务器", EditorStyles.toolbarButton, GUILayout.Width(80)))
                {
                    StopServer();
                }
            }
            else
            {
                // 服务器未运行
                if (GUILayout.Button("启动服务器", EditorStyles.toolbarButton, GUILayout.Width(80)))
                {
                    StartServer();
                }
            }

            GUILayout.Space(10);

            // 连接状态（带ping时间显示）
            GUIStyle statusStyle = new GUIStyle(EditorStyles.label);
            statusStyle.normal.textColor = isConnected ? Color.green : Color.red;
            string statusText = isConnected ? "● 已连接" : "● 未连接";
            GUILayout.Label(statusText, statusStyle);

            // 显示上次ping时间
            if (lastPingTime > 0)
            {
                double timeSinceLastPing = EditorApplication.timeSinceStartup - lastPingTime;
                GUILayout.Label($"(ping: {timeSinceLastPing:F1}s前)", EditorStyles.miniLabel, GUILayout.Width(80));
            }

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

            // Action类型标题行
            EditorGUILayout.BeginHorizontal();

            // 显示名称和类型
            string title = !string.IsNullOrEmpty(recommendation.display_name)
                ? $"{recommendation.display_name} ({recommendation.action_type})"
                : recommendation.action_type;
            EditorGUILayout.LabelField(title, EditorStyles.boldLabel);

            GUILayout.FlexibleSpace();

            // 综合得分标签（颜色根据得分高低）
            Color originalColor = GUI.backgroundColor;
            float score = recommendation.combined_score;
            GUI.backgroundColor = score >= 0.7f ? Color.green :
                                  score >= 0.4f ? Color.yellow : Color.red;
            GUILayout.Label($"得分: {score:P0}", EditorStyles.miniButton, GUILayout.Width(60));
            GUI.backgroundColor = originalColor;

            EditorGUILayout.EndHorizontal();

            // 分类和描述
            if (!string.IsNullOrEmpty(recommendation.category))
            {
                EditorGUILayout.BeginHorizontal();
                EditorGUILayout.LabelField("分类:", GUILayout.Width(60));
                EditorGUILayout.LabelField(recommendation.category, EditorStyles.miniLabel);
                EditorGUILayout.EndHorizontal();
            }

            if (!string.IsNullOrEmpty(recommendation.description))
            {
                EditorGUILayout.BeginHorizontal();
                EditorGUILayout.LabelField("描述:", GUILayout.Width(60));
                EditorGUILayout.LabelField(recommendation.description, EditorStyles.wordWrappedMiniLabel);
                EditorGUILayout.EndHorizontal();
            }

            // 详细评分信息
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField("详细评分:", EditorStyles.miniLabel, GUILayout.Width(60));
            EditorGUILayout.LabelField(
                $"语义相似度: {recommendation.semantic_similarity:P0}  |  使用频率: {recommendation.frequency} 次",
                EditorStyles.miniLabel
            );
            EditorGUILayout.EndHorizontal();

            // 参数示例
            if (recommendation.examples != null && recommendation.examples.Count > 0)
            {
                EditorGUILayout.Space(3);
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
            EditorGUILayout.Space(3);
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
        /// 定时ping服务器（不显示状态信息，仅更新连接状态）
        /// </summary>
        private async UniTaskVoid PingServerAsync()
        {
            if (isPinging)
                return;

            isPinging = true;

            try
            {
                // 在后台线程执行HTTP请求（设置短超时）
                var pingTask = UniTask.RunOnThreadPool(async () =>
                {
                    using (var tempClient = new EditorRAGClient(serverHost, serverPort))
                    {
                        return await tempClient.CheckHealthAsync();
                    }
                });

                // 等待ping结果，最多1秒
                string status = await pingTask.Timeout(TimeSpan.FromSeconds(1));

                // Ping成功
                if (!isConnected)
                {
                    // 从未连接变为已连接
                    isConnected = true;
                    statusMessage = $"已连接到RAG服务 ({status})";
                    Repaint();
                }
                else
                {
                    // 保持已连接状态
                    isConnected = true;
                }
            }
            catch (TimeoutException)
            {
                // Ping超时
                if (isConnected)
                {
                    // 从已连接变为未连接
                    isConnected = false;
                    statusMessage = "连接超时";
                    Repaint();
                }
            }
            catch (Exception)
            {
                // Ping失败
                if (isConnected)
                {
                    // 从已连接变为未连接
                    isConnected = false;
                    statusMessage = "连接断开";
                    Repaint();
                }
            }
            finally
            {
                isPinging = false;
            }
        }

        /// <summary>
        /// 异步检查连接（不阻塞主线程）
        /// </summary>
        private async UniTaskVoid CheckConnectionAsync()
        {
            statusMessage = "正在连接...";
            isLoading = true;
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                string status = await UniTask.RunOnThreadPool(async () =>
                {
                    return await client.CheckHealthAsync();
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

        private async UniTaskVoid PerformSearch()
        {
            statusMessage = "正在搜索...";
            isLoading = true;
            searchResults.Clear();
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await UniTask.RunOnThreadPool(async () =>
                {
                    return await client.SearchSkillsAsync(searchQuery, searchTopK, searchReturnDetails);
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

        private async UniTaskVoid PerformRecommend()
        {
            statusMessage = "正在获取推荐...";
            isLoading = true;
            recommendations.Clear();
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await UniTask.RunOnThreadPool(async () =>
                {
                    return await client.RecommendActionsAsync(recommendContext, recommendTopK);
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

        private async UniTaskVoid TriggerIndex(bool forceRebuild)
        {
            statusMessage = "正在索引...";
            isLoading = true;
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await UniTask.RunOnThreadPool(async () =>
                {
                    return await client.TriggerIndexAsync(forceRebuild);
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

        private async UniTaskVoid ClearCache()
        {
            statusMessage = "正在清空缓存...";
            isLoading = true;
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                await UniTask.RunOnThreadPool(async () =>
                {
                    await client.ClearCacheAsync();
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

        private async UniTaskVoid GetStatistics()
        {
            statusMessage = "正在获取统计...";
            isLoading = true;
            Repaint();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await UniTask.RunOnThreadPool(async () =>
                {
                    return await client.GetStatisticsAsync();
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
            var skillData = SkillDataSerializer.LoadFromFile(assetPath);
            if (skillData != null)
            {
                SkillEditorWindow.OpenSkill(skillData);
            }
            else
            {
                EditorUtility.DisplayDialog("错误", $"无法加载技能文件: {assetPath}", "确定");
            }
        }

        #region 服务器管理

        /// <summary>
        /// 启动Python RAG服务器
        /// </summary>
        private void StartServer()
        {
            if (isServerRunning)
            {
                UnityEngine.Debug.LogWarning("[RAG] 服务器已在运行中");
                return;
            }

            try
            {
                // 查找Python可执行文件
                string pythonPath = FindPythonExecutable();
                if (string.IsNullOrEmpty(pythonPath))
                {
                    EditorUtility.DisplayDialog("错误", "未找到Python环境，请先安装Python 3.7+", "确定");
                    return;
                }

                // 构建服务器脚本路径
                // Application.dataPath = .../ai_agent_for_skill/ai_agent_for_skill/Assets
                // 我们需要到上上级目录 .../ai_agent_for_skill/ 才能找到 SkillRAG/
                string assetsPath = Application.dataPath;  // .../ai_agent_for_skill/Assets
                string unityProjectPath = Directory.GetParent(assetsPath).FullName;  // .../ai_agent_for_skill
                string rootPath = Directory.GetParent(unityProjectPath).FullName;  // .../
                string serverScriptPath = Path.Combine(rootPath, "SkillRAG", "Python", "server.py");

                // 标准化路径
                serverScriptPath = Path.GetFullPath(serverScriptPath);

                Debug.Log($"[RAG] 查找服务器脚本: {serverScriptPath}");

                if (!File.Exists(serverScriptPath))
                {
                    EditorUtility.DisplayDialog("错误",
                        $"未找到服务器脚本:\n{serverScriptPath}\n\n" +
                        $"Assets路径: {assetsPath}\n" +
                        $"Unity项目路径: {unityProjectPath}\n" +
                        $"根路径: {rootPath}\n\n" +
                        "请确保SkillRAG目录与ai_agent_for_skill目录在同一级",
                        "确定");
                    return;
                }

                // 配置进程启动信息
                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = $"\"{serverScriptPath}\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    WorkingDirectory = Path.GetDirectoryName(serverScriptPath)
                };

                // 启动进程
                serverProcess = new Process { StartInfo = startInfo };

                // 监听输出
                serverProcess.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        serverOutput += e.Data + "\n";
                        UnityEngine.Debug.Log($"[RAG Server] {e.Data}");
                    }
                };

                serverProcess.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        serverOutput += "[ERROR] " + e.Data + "\n";
                        UnityEngine.Debug.LogWarning($"[RAG Server] {e.Data}");
                    }
                };

                serverProcess.Start();
                serverProcess.BeginOutputReadLine();
                serverProcess.BeginErrorReadLine();

                isServerRunning = true;
                statusMessage = "服务器启动中...";

                UnityEngine.Debug.Log($"[RAG] 服务器已启动 (PID: {serverProcess.Id})");

                // 等待3秒后尝试连接
                WaitAndConnectAsync().Forget();
            }
            catch (Exception e)
            {
                UnityEngine.Debug.LogError($"[RAG] 启动服务器失败: {e.Message}");
                EditorUtility.DisplayDialog("错误", $"启动服务器失败:\n{e.Message}", "确定");
                isServerRunning = false;
            }
        }

        /// <summary>
        /// 等待3秒后尝试连接（使用UniTask）
        /// </summary>
        private async UniTaskVoid WaitAndConnectAsync()
        {
            await UniTask.Delay(TimeSpan.FromSeconds(3));
            CheckConnectionAsync().Forget();
        }

        /// <summary>
        /// 停止Python RAG服务器
        /// </summary>
        private void StopServer()
        {
            if (serverProcess != null && !serverProcess.HasExited)
            {
                try
                {
                    serverProcess.Kill();
                    serverProcess.WaitForExit(5000);
                    serverProcess.Dispose();
                    serverProcess = null;

                    isServerRunning = false;
                    isConnected = false;
                    statusMessage = "服务器已停止";

                    UnityEngine.Debug.Log("[RAG] 服务器已停止");
                }
                catch (Exception e)
                {
                    UnityEngine.Debug.LogError($"[RAG] 停止服务器失败: {e.Message}");
                }
            }
            else
            {
                serverProcess = null;
                isServerRunning = false;
            }
        }

        /// <summary>
        /// 查找Python可执行文件
        /// </summary>
        private string FindPythonExecutable()
        {
            // 尝试常见的Python命令
            string[] pythonCommands = { "python", "python3", "py" };

            foreach (string cmd in pythonCommands)
            {
                try
                {
                    ProcessStartInfo startInfo = new ProcessStartInfo
                    {
                        FileName = cmd,
                        Arguments = "--version",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true
                    };

                    using (Process process = Process.Start(startInfo))
                    {
                        process.WaitForExit(2000);
                        if (process.ExitCode == 0)
                        {
                            return cmd;
                        }
                    }
                }
                catch
                {
                    // 继续尝试下一个命令
                }
            }

            return null;
        }

        #endregion
    }

}
