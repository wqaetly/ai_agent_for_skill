using UnityEditor;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// RAG编辑器集成
    /// 提供WebUI集成入口
    /// </summary>
    public static class RAGEditorIntegration
    {
        // WebUI配置
        private const string WEBUI_URL_KEY = "SkillAgent_WebUIUrl";

        public static string WebUIUrl
        {
            get => EditorPrefs.GetString(WEBUI_URL_KEY, "http://localhost:3000");
            set => EditorPrefs.SetString(WEBUI_URL_KEY, value);
        }

        /// <summary>
        /// 添加RAG设置到Preferences
        /// </summary>
        [SettingsProvider]
        public static SettingsProvider CreateRAGSettingsProvider()
        {
            var provider = new SettingsProvider("Preferences/技能系统/RAG设置", SettingsScope.User)
            {
                label = "RAG设置",

                guiHandler = (searchContext) =>
                {
                    EditorGUILayout.Space(10);
                    EditorGUILayout.LabelField("技能RAG系统设置", EditorStyles.boldLabel);
                    EditorGUILayout.Space(5);

                    EditorGUILayout.LabelField("WebUI配置", EditorStyles.boldLabel);

                    // WebUI地址
                    EditorGUILayout.BeginHorizontal();
                    EditorGUILayout.LabelField("WebUI地址:", GUILayout.Width(100));
                    string newUrl = EditorGUILayout.TextField(WebUIUrl);
                    EditorGUILayout.EndHorizontal();

                    if (newUrl != WebUIUrl)
                    {
                        WebUIUrl = newUrl;
                    }

                    EditorGUILayout.Space(10);

                    // 打开WebUI
                    if (GUILayout.Button("打开WebUI", GUILayout.Height(35)))
                    {
                        Application.OpenURL(WebUIUrl);
                    }

                    EditorGUILayout.Space(10);
                    EditorGUILayout.HelpBox(
                        "RAG（检索增强生成）功能已迁移至WebUI。\n\n" +
                        "请在WebUI中进行以下操作：\n" +
                        "• 技能语义搜索\n" +
                        "• Action智能推荐\n" +
                        "• 参数推荐\n" +
                        "• 索引管理\n\n" +
                        "使用前请确保已通过 Tools → SkillAgent → 启动服务器 启动后端服务。",
                        MessageType.Info
                    );

                    EditorGUILayout.Space(5);

                    if (GUILayout.Button("查看迁移文档"))
                    {
                        string docPath = Application.dataPath + "/../MIGRATION_GUIDE.md";
                        if (System.IO.File.Exists(docPath))
                        {
                            Application.OpenURL("file:///" + docPath);
                        }
                        else
                        {
                            EditorUtility.DisplayDialog("提示", "迁移文档不存在", "确定");
                        }
                    }
                },

                keywords = new System.Collections.Generic.HashSet<string>(new[] { "RAG", "WebUI", "技能", "迁移" })
            };

            return provider;
        }

        /// <summary>
        /// 菜单项：打开WebUI
        /// </summary>
        [MenuItem("技能系统/RAG功能/打开WebUI", false, 100)]
        private static void OpenWebUI()
        {
            Application.OpenURL(WebUIUrl);
        }

        /// <summary>
        /// 菜单项：重建索引（提示用户在WebUI操作）
        /// </summary>
        [MenuItem("技能系统/RAG功能/重建索引", false, 110)]
        private static void RebuildIndexHint()
        {
            bool openWebUI = EditorUtility.DisplayDialog(
                "重建索引",
                "索引重建功能已迁移至WebUI。\n\n" +
                "请在WebUI的 RAG管理 页面中点击 '重建索引' 按钮。\n\n" +
                "是否现在打开WebUI？",
                "打开WebUI",
                "取消"
            );

            if (openWebUI)
            {
                Application.OpenURL(WebUIUrl + "/rag");
            }
        }
    }
}
