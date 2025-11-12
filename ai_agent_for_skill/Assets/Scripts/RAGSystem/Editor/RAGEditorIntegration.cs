using Cysharp.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using SkillSystem.Actions;

namespace SkillSystem.RAG
{
    /// <summary>
    /// RAG编辑器集�?
    /// 将RAG功能集成到现有的SkillEditor�?
    /// </summary>
    [InitializeOnLoad]
    public static class RAGEditorIntegration
    {
        private static EditorRAGClient ragClient;
        private static bool isInitialized = false;

        // 配置
        private const string RAG_ENABLED_KEY = "skill_agent_Enabled";
        private const string RAG_AUTO_SUGGEST_KEY = "skill_agent_AutoSuggest";
        private const string RAG_SERVER_HOST_KEY = "skill_agent_ServerHost";
        private const string RAG_SERVER_PORT_KEY = "skill_agent_ServerPort";

        // 属�?
        public static bool IsEnabled
        {
            get => EditorPrefs.GetBool(RAG_ENABLED_KEY, true);
            set => EditorPrefs.SetBool(RAG_ENABLED_KEY, value);
        }

        public static bool AutoSuggest
        {
            get => EditorPrefs.GetBool(RAG_AUTO_SUGGEST_KEY, true);
            set => EditorPrefs.SetBool(RAG_AUTO_SUGGEST_KEY, value);
        }

        public static string ServerHost
        {
            get => EditorPrefs.GetString(RAG_SERVER_HOST_KEY, "127.0.0.1");
            set => EditorPrefs.SetString(RAG_SERVER_HOST_KEY, value);
        }

        public static int ServerPort
        {
            get => EditorPrefs.GetInt(RAG_SERVER_PORT_KEY, 8765);
            set => EditorPrefs.SetInt(RAG_SERVER_PORT_KEY, value);
        }

        // 静态构造函数（Unity启动时自动调用）
        static RAGEditorIntegration()
        {
            EditorApplication.delayCall += Initialize;
        }

        /// <summary>
        /// 初始化RAG集成
        /// </summary>
        private static void Initialize()
        {
            if (isInitialized)
                return;

            if (!IsEnabled)
            {
                Debug.Log("[RAG] RAG功能已禁�?);
                return;
            }

            ragClient = new EditorRAGClient(ServerHost, ServerPort);

            // 初始化SmartActionInspector
            SmartActionInspector.Initialize();

            isInitialized = true;

            Debug.Log($"[RAG] RAG编辑器集成已初始�?(服务�? {ServerHost}:{ServerPort})");
        }

        /// <summary>
        /// 在ActionInspector中绘制RAG建议（由ActionInspector调用�?
        /// </summary>
        public static void DrawActionRAGSuggestions(ISkillAction action)
        {
            if (!IsEnabled || !isInitialized || !AutoSuggest)
                return;

            SmartActionInspector.DrawSmartSuggestions(action);
        }

        /// <summary>
        /// 搜索相似技能（可从SkillEditor调用�?
        /// </summary>
        public static async UniTaskVoid SearchSimilarSkills(string query, System.Action<bool, EditorRAGClient.SearchResponse> callback)
        {
            if (!isInitialized)
            {
                callback?.Invoke(false, null);
                return;
            }

            try
            {
                // 在后台线程执行HTTP请求
                var response = await UniTask.RunOnThreadPool(async () =>
                {
                    return await ragClient.SearchSkillsAsync(query, 5, true);
                });

                callback?.Invoke(true, response);
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[RAG] 搜索异常: {e}");
                callback?.Invoke(false, null);
            }
        }

        /// <summary>
        /// 添加RAG设置到Preferences
        /// </summary>
        [SettingsProvider]
        public static SettingsProvider CreateRAGSettingsProvider()
        {
            var provider = new SettingsProvider("Preferences/技能系�?RAG设置", SettingsScope.User)
            {
                label = "RAG设置",

                guiHandler = (searchContext) =>
                {
                    EditorGUILayout.Space(10);
                    EditorGUILayout.LabelField("技能RAG系统设置", EditorStyles.boldLabel);
                    EditorGUILayout.Space(5);

                    EditorGUI.BeginChangeCheck();

                    // 启用/禁用
                    bool newEnabled = EditorGUILayout.Toggle("启用RAG功能", IsEnabled);

                    EditorGUI.BeginDisabledGroup(!newEnabled);

                    // 自动建议
                    bool newAutoSuggest = EditorGUILayout.Toggle("自动显示参数建议", AutoSuggest);

                    EditorGUILayout.Space(10);
                    EditorGUILayout.LabelField("服务器配�?, EditorStyles.boldLabel);

                    // 服务器地址
                    EditorGUILayout.BeginHorizontal();
                    EditorGUILayout.LabelField("服务器地址:", GUILayout.Width(100));
                    string newHost = EditorGUILayout.TextField(ServerHost);
                    EditorGUILayout.EndHorizontal();

                    // 服务器端�?
                    EditorGUILayout.BeginHorizontal();
                    EditorGUILayout.LabelField("服务器端�?", GUILayout.Width(100));
                    int newPort = EditorGUILayout.IntField(ServerPort);
                    EditorGUILayout.EndHorizontal();

                    EditorGUI.EndDisabledGroup();

                    if (EditorGUI.EndChangeCheck())
                    {
                        IsEnabled = newEnabled;
                        AutoSuggest = newAutoSuggest;
                        ServerHost = newHost;
                        ServerPort = newPort;

                        // 重新初始�?
                        if (newEnabled)
                        {
                            isInitialized = false;
                            Initialize();
                        }
                    }

                    EditorGUILayout.Space(10);

                    // 测试连接
                    if (GUILayout.Button("测试连接", GUILayout.Height(30)))
                    {
                        TestConnection();
                    }

                    EditorGUILayout.Space(5);

                    // 打开RAG窗口
                    if (GUILayout.Button("打开RAG查询窗口", GUILayout.Height(30)))
                    {
                        skill_agentWindow.ShowWindow();
                    }

                    // 清空缓存
                    if (GUILayout.Button("清空本地缓存", GUILayout.Height(25)))
                    {
                        SmartActionInspector.ClearCache();
                        EditorUtility.DisplayDialog("完成", "本地缓存已清�?, "确定");
                    }

                    EditorGUILayout.Space(10);
                    EditorGUILayout.HelpBox(
                        "RAG（检索增强生成）系统提供基于AI的技能搜索和参数推荐功能。\n\n" +
                        "使用前请确保已启动Python RAG服务器�?,
                        MessageType.Info
                    );

                    EditorGUILayout.Space(5);

                    if (GUILayout.Button("查看RAG文档"))
                    {
                        string docPath = Application.dataPath + "/../skill_agent/Docs/UserGuide.md";
                        if (System.IO.File.Exists(docPath))
                        {
                            Application.OpenURL("file:///" + docPath);
                        }
                        else
                        {
                            EditorUtility.DisplayDialog("提示", "文档文件不存�?, "确定");
                        }
                    }
                },

                keywords = new System.Collections.Generic.HashSet<string>(new[] { "RAG", "AI", "技�?, "推荐", "搜索" })
            };

            return provider;
        }

        /// <summary>
        /// 测试连接
        /// </summary>
        private static async UniTaskVoid TestConnection()
        {
            if (!isInitialized)
                Initialize();

            try
            {
                // 在后台线程执行HTTP请求
                string status = await UniTask.RunOnThreadPool(async () =>
                {
                    return await ragClient.CheckHealthAsync();
                });

                EditorUtility.DisplayDialog(
                    "连接成功",
                    $"已成功连接到RAG服务器\n状�? {status}",
                    "确定"
                );
            }
            catch (System.Exception e)
            {
                EditorUtility.DisplayDialog(
                    "连接失败",
                    $"无法连接到RAG服务器\n错误: {e.InnerException?.Message ?? e.Message}\n\n请确保Python服务器正在运行�?,
                    "确定"
                );
                Debug.LogError($"[RAG] Connection error: {e}");
            }
        }

        /// <summary>
        /// 在SkillEditor菜单中添加RAG相关选项
        /// </summary>
        [MenuItem("技能系�?RAG功能/打开RAG查询窗口", false, 100)]
        private static void OpenRAGWindow()
        {
            skill_agentWindow.ShowWindow();
        }

        [MenuItem("技能系�?RAG功能/启用RAG功能", false, 101)]
        private static void ToggleRAGEnabled()
        {
            IsEnabled = !IsEnabled;
            Menu.SetChecked("技能系�?RAG功能/启用RAG功能", IsEnabled);

            if (IsEnabled)
            {
                isInitialized = false;
                Initialize();
            }
        }

        [MenuItem("技能系�?RAG功能/启用RAG功能", true)]
        private static bool ToggleRAGEnabled_Validate()
        {
            Menu.SetChecked("技能系�?RAG功能/启用RAG功能", IsEnabled);
            return true;
        }

        [MenuItem("技能系�?RAG功能/自动显示参数建议", false, 102)]
        private static void ToggleAutoSuggest()
        {
            AutoSuggest = !AutoSuggest;
            Menu.SetChecked("技能系�?RAG功能/自动显示参数建议", AutoSuggest);
        }

        [MenuItem("技能系�?RAG功能/自动显示参数建议", true)]
        private static bool ToggleAutoSuggest_Validate()
        {
            Menu.SetChecked("技能系�?RAG功能/自动显示参数建议", AutoSuggest);
            return IsEnabled;
        }

        [MenuItem("技能系�?RAG功能/重建索引", false, 110)]
        private static async UniTaskVoid RebuildIndex()
        {
            if (!EditorUtility.DisplayDialog(
                "确认",
                "重建索引会扫描所有技能文件并更新向量数据库，这可能需要一些时间。\n\n是否继续�?,
                "确定",
                "取消"))
            {
                return;
            }

            if (!isInitialized)
                Initialize();

            try
            {
                // 在后台线程执行HTTP请求
                var response = await UniTask.RunOnThreadPool(async () =>
                {
                    return await ragClient.TriggerIndexAsync(true);
                });

                EditorUtility.DisplayDialog(
                    "索引完成",
                    $"成功索引 {response.count} 个技能\n耗时: {response.elapsed_time:F2}�?,
                    "确定"
                );
            }
            catch (System.Exception e)
            {
                EditorUtility.DisplayDialog(
                    "索引失败",
                    $"索引时发生异�?\n{e.InnerException?.Message ?? e.Message}",
                    "确定"
                );
                Debug.LogError($"[RAG] Index error: {e}");
            }
        }

        [MenuItem("技能系�?RAG功能/重建索引", true)]
        private static bool RebuildIndex_Validate()
        {
            return IsEnabled;
        }
    }
}
