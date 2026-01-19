using RAGBuilder;
using RAGBuilder.Editor;
using UnityEditor;
using UnityEngine;
using SkillSystem.RAG.Adapters;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Initializes RAG Builder integration for the Skill System.
    /// This script automatically registers the skill system providers when Unity loads.
    /// </summary>
    [InitializeOnLoad]
    public static class RAGBuilderIntegration
    {
        private const string CONFIG_PATH = "Assets/Data/RAGBuilderConfig.asset";

        static RAGBuilderIntegration()
        {
            // Delay initialization to ensure everything is loaded
            EditorApplication.delayCall += Initialize;
        }

        private static void Initialize()
        {
            // Try to load or create configuration
            var config = AssetDatabase.LoadAssetAtPath<RAGBuilderConfig>(CONFIG_PATH);
            
            if (config == null)
            {
                Debug.Log("[RAGBuilderIntegration] No configuration found. Create one via Edit > Preferences > RAG Builder");
                return;
            }

            // Create action provider
            var actionProvider = new SkillSystemActionProvider();

            // Initialize the RAG Builder service
            RAGBuilderService.Instance.Initialize(
                config,
                actionProvider: actionProvider
            );

            Debug.Log("[RAGBuilderIntegration] RAG Builder initialized with Skill System adapters");
        }

        /// <summary>
        /// Menu item to manually refresh the integration
        /// </summary>
        [MenuItem("技能系统/RAG Builder/刷新集成", priority = 200)]
        public static void RefreshIntegration()
        {
            Initialize();
            Debug.Log("[RAGBuilderIntegration] Integration refreshed");
        }

        /// <summary>
        /// Menu item to create RAG Builder configuration
        /// </summary>
        [MenuItem("技能系统/RAG Builder/创建配置", priority = 201)]
        public static void CreateConfiguration()
        {
            // Check if config already exists
            var existing = AssetDatabase.LoadAssetAtPath<RAGBuilderConfig>(CONFIG_PATH);
            if (existing != null)
            {
                Selection.activeObject = existing;
                EditorGUIUtility.PingObject(existing);
                Debug.Log("[RAGBuilderIntegration] Configuration already exists");
                return;
            }

            // Create new configuration
            var config = ScriptableObject.CreateInstance<RAGBuilderConfig>();
            
            // Set default paths for this project
            config.serverHost = "127.0.0.1";
            config.serverPort = 2024;
            config.actionExportDirectory = "../skill_agent/Data/Actions";
            config.skillExportDirectory = "../skill_agent/Data/Skills";
            config.serverScriptPath = "../skill_agent/langgraph_server.py";
            config.webUIUrl = "http://127.0.0.1:2024";

            // Ensure directory exists
            string directory = System.IO.Path.GetDirectoryName(CONFIG_PATH);
            if (!AssetDatabase.IsValidFolder(directory))
            {
                System.IO.Directory.CreateDirectory(directory);
                AssetDatabase.Refresh();
            }

            AssetDatabase.CreateAsset(config, CONFIG_PATH);
            AssetDatabase.SaveAssets();

            Selection.activeObject = config;
            EditorGUIUtility.PingObject(config);

            Debug.Log($"[RAGBuilderIntegration] Created configuration at {CONFIG_PATH}");

            // Initialize with new config
            Initialize();
        }
    }
}
