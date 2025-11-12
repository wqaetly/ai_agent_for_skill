using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using UnityEditor;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// 智能Action检查器
    /// 在ActionInspector中提供AI参数推荐功能
    /// </summary>
    public class SmartActionInspector
    {
        private static EditorRAGClient ragClient;
        private static Dictionary<string, List<EditorRAGClient.ActionRecommendation>> paramSuggestionsCache;
        private static bool isInitialized = false;

        // UI状态
        private static bool showSmartSuggestions = true;
        private static Vector2 suggestionsScrollPos;
        private static bool isLoadingSuggestions = false;
        private static string currentActionType = "";

        /// <summary>
        /// 初始化智能检查器
        /// </summary>
        public static void Initialize()
        {
            if (isInitialized)
                return;

            ragClient = new EditorRAGClient();
            paramSuggestionsCache = new Dictionary<string, List<EditorRAGClient.ActionRecommendation>>();
            isInitialized = true;
        }

        /// <summary>
        /// 绘制智能建议UI（在ActionInspector中调用）
        /// </summary>
        /// <param name="action">当前编辑的Action</param>
        public static void DrawSmartSuggestions(SkillSystem.Actions.ISkillAction action)
        {
            if (!isInitialized)
                Initialize();

            if (action == null)
                return;

            string actionType = action.GetType().Name;

            EditorGUILayout.Space(10);

            // 折叠栏
            EditorGUILayout.BeginVertical("box");

            EditorGUILayout.BeginHorizontal();
            showSmartSuggestions = EditorGUILayout.Foldout(showSmartSuggestions, "🤖 AI参数建议", true, EditorStyles.foldoutHeader);

            if (GUILayout.Button("刷新", EditorStyles.miniButton, GUILayout.Width(50)))
            {
                RefreshSuggestions(actionType);
            }

            EditorGUILayout.EndHorizontal();

            if (showSmartSuggestions)
            {
                EditorGUI.indentLevel++;

                // 检查是否有缓存的建议
                if (paramSuggestionsCache.ContainsKey(actionType))
                {
                    DrawCachedSuggestions(actionType, action);
                }
                else if (!isLoadingSuggestions)
                {
                    // 首次加载
                    EditorGUILayout.HelpBox("点击\"刷新\"获取AI参数建议", MessageType.Info);
                }
                else
                {
                    EditorGUILayout.LabelField("正在加载建议...", EditorStyles.miniLabel);
                }

                EditorGUI.indentLevel--;
            }

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 绘制缓存的建议
        /// </summary>
        private static void DrawCachedSuggestions(string actionType, SkillSystem.Actions.ISkillAction action)
        {
            var suggestions = paramSuggestionsCache[actionType];

            if (suggestions == null || suggestions.Count == 0)
            {
                EditorGUILayout.HelpBox("没有找到相关的AI推荐", MessageType.Info);
                return;
            }

            EditorGUILayout.LabelField($"找到 {suggestions.Count} 个推荐的Action类型:", EditorStyles.miniLabel);
            EditorGUILayout.Space(3);

            suggestionsScrollPos = EditorGUILayout.BeginScrollView(
                suggestionsScrollPos,
                GUILayout.MaxHeight(200)
            );

            // 显示所有推荐的Action
            foreach (var suggestion in suggestions)
            {
                DrawActionSuggestion(suggestion);
            }

            EditorGUILayout.EndScrollView();
        }

        /// <summary>
        /// 绘制单个Action建议
        /// </summary>
        private static void DrawActionSuggestion(EditorRAGClient.ActionRecommendation suggestion)
        {
            EditorGUILayout.BeginVertical("box");

            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField($"{suggestion.display_name} ({suggestion.action_type})", EditorStyles.boldLabel);
            EditorGUILayout.LabelField($"相似度: {suggestion.semantic_similarity:F3}", GUILayout.Width(100));
            EditorGUILayout.EndHorizontal();

            if (!string.IsNullOrEmpty(suggestion.description))
            {
                EditorGUILayout.LabelField($"描述: {suggestion.description}", EditorStyles.wordWrappedMiniLabel);
            }

            EditorGUILayout.LabelField($"分类: {suggestion.category}", EditorStyles.miniLabel);

            EditorGUILayout.EndVertical();
            EditorGUILayout.Space(2);
        }

        /// <summary>
        /// 刷新建议
        /// </summary>
        private static async UniTaskVoid RefreshSuggestions(string actionType)
        {
            if (isLoadingSuggestions)
                return;

            isLoadingSuggestions = true;
            currentActionType = actionType;

            // 构建上下文查询
            string context = GetActionContextQuery(actionType);

            try
            {
                // 在后台线程执行HTTP请求
                var response = await UniTask.RunOnThreadPool(async () =>
                {
                    return await ragClient.RecommendActionsAsync(context, 3);
                });

                paramSuggestionsCache[actionType] = response.recommendations;
                Debug.Log($"[SmartActionInspector] 获取到 {response.recommendations.Count} 个建议");
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[SmartActionInspector] 获取建议异常: {e}");
                paramSuggestionsCache[actionType] = new List<EditorRAGClient.ActionRecommendation>();
            }
            finally
            {
                isLoadingSuggestions = false;
            }
        }

        /// <summary>
        /// 根据Action类型构建上下文查询
        /// </summary>
        private static string GetActionContextQuery(string actionType)
        {
            // 移除"Action"后缀
            string baseName = actionType.Replace("Action", "");

            // 根据Action类型返回对应的中文描述
            var contextMap = new Dictionary<string, string>
            {
                { "Damage", "造成伤害的技能效果" },
                { "Heal", "治疗恢复生命值" },
                { "Movement", "移动角色位置" },
                { "Projectile", "发射弹道飞行物" },
                { "AreaOfEffect", "范围效果作用于区域" },
                { "Buff", "增益或减益状态效果" },
                { "Shield", "护盾吸收伤害" },
                { "Summon", "召唤单位" },
                { "Teleport", "瞬移传送" },
                { "Animation", "播放动画效果" },
                { "Audio", "播放音效" },
                { "Camera", "相机震动或缩放" },
                { "Control", "控制输入限制" },
                { "Collision", "碰撞检测" },
                { "Resource", "资源消耗或生成" }
            };

            return contextMap.ContainsKey(baseName) ? contextMap[baseName] : $"{baseName} 相关效果";
        }

        /// <summary>
        /// 清空缓存
        /// </summary>
        public static void ClearCache()
        {
            paramSuggestionsCache?.Clear();
            Debug.Log("[SmartActionInspector] 缓存已清空");
        }
    }
}
