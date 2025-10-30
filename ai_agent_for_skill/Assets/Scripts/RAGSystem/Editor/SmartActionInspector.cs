using System.Collections.Generic;
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
                EditorGUILayout.HelpBox("没有找到相关的参数建议", MessageType.Info);
                return;
            }

            EditorGUILayout.LabelField($"基于 {GetTotalFrequency(suggestions)} 个相似案例的建议:", EditorStyles.miniLabel);
            EditorGUILayout.Space(3);

            suggestionsScrollPos = EditorGUILayout.BeginScrollView(
                suggestionsScrollPos,
                GUILayout.MaxHeight(200)
            );

            // 只显示当前Action类型的建议
            foreach (var suggestion in suggestions)
            {
                if (suggestion.action_type == actionType)
                {
                    DrawActionSuggestion(suggestion, action);
                }
            }

            EditorGUILayout.EndScrollView();
        }

        /// <summary>
        /// 绘制单个Action建议
        /// </summary>
        private static void DrawActionSuggestion(EditorRAGClient.ActionRecommendation suggestion, SkillSystem.Actions.ISkillAction action)
        {
            if (suggestion.examples == null || suggestion.examples.Count == 0)
                return;

            EditorGUILayout.BeginVertical("box");

            EditorGUILayout.LabelField($"常见参数配置 (出现 {suggestion.frequency} 次)", EditorStyles.boldLabel);

            foreach (var example in suggestion.examples)
            {
                EditorGUILayout.BeginVertical("helpBox");

                EditorGUILayout.LabelField($"来源: {example.skill_name}", EditorStyles.miniLabel);
                EditorGUILayout.Space(2);

                if (example.parameters != null && example.parameters.Count > 0)
                {
                    EditorGUI.indentLevel++;

                    foreach (var param in example.parameters)
                    {
                        EditorGUILayout.BeginHorizontal();

                        EditorGUILayout.LabelField($"{param.Key}:", GUILayout.Width(150));

                        // 显示值
                        string valueStr = param.Value?.ToString() ?? "null";
                        EditorGUILayout.SelectableLabel(valueStr, EditorStyles.miniLabel, GUILayout.Height(16));

                        // 应用按钮
                        if (GUILayout.Button("应用", EditorStyles.miniButton, GUILayout.Width(40)))
                        {
                            ApplyParameterToAction(action, param.Key, param.Value);
                        }

                        EditorGUILayout.EndHorizontal();
                    }

                    EditorGUI.indentLevel--;
                }

                EditorGUILayout.EndVertical();
                EditorGUILayout.Space(3);
            }

            // 全部应用按钮
            if (suggestion.examples.Count > 0 && suggestion.examples[0].parameters != null)
            {
                if (GUILayout.Button("应用此配置的所有参数", GUILayout.Height(25)))
                {
                    ApplyAllParameters(action, suggestion.examples[0].parameters);
                }
            }

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 刷新建议
        /// </summary>
        private static async void RefreshSuggestions(string actionType)
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
                var response = await System.Threading.Tasks.Task.Run(() =>
                {
                    return ragClient.RecommendActionsAsync(context, 3).Result;
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
        /// 应用参数到Action
        /// </summary>
        private static void ApplyParameterToAction(SkillSystem.Actions.ISkillAction action, string paramName, object paramValue)
        {
            try
            {
                var field = action.GetType().GetField(paramName);

                if (field != null)
                {
                    // 类型转换
                    object convertedValue = ConvertValue(paramValue, field.FieldType);

                    if (convertedValue != null)
                    {
                        // Note: ISkillAction is not a UnityEngine.Object, so we can't use Undo
                        // The changes will be applied directly to the action data
                        field.SetValue(action, convertedValue);

                        Debug.Log($"[SmartActionInspector] 已应用参数: {paramName} = {paramValue}");
                    }
                    else
                    {
                        Debug.LogWarning($"[SmartActionInspector] 无法转换参数类型: {paramName}");
                    }
                }
                else
                {
                    Debug.LogWarning($"[SmartActionInspector] 未找到字段: {paramName}");
                }
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[SmartActionInspector] 应用参数失败: {e.Message}");
            }
        }

        /// <summary>
        /// 应用所有参数
        /// </summary>
        private static void ApplyAllParameters(SkillSystem.Actions.ISkillAction action, Dictionary<string, object> parameters)
        {
            // Note: ISkillAction is not a UnityEngine.Object, so we can't use Undo
            // The changes will be applied directly to the action data

            int appliedCount = 0;

            foreach (var param in parameters)
            {
                try
                {
                    var field = action.GetType().GetField(param.Key);

                    if (field != null)
                    {
                        object convertedValue = ConvertValue(param.Value, field.FieldType);

                        if (convertedValue != null)
                        {
                            field.SetValue(action, convertedValue);
                            appliedCount++;
                        }
                    }
                }
                catch (System.Exception e)
                {
                    Debug.LogWarning($"[SmartActionInspector] 应用参数 {param.Key} 失败: {e.Message}");
                }
            }

            Debug.Log($"[SmartActionInspector] 已应用 {appliedCount}/{parameters.Count} 个参数");
        }

        /// <summary>
        /// 类型转换辅助方法
        /// </summary>
        private static object ConvertValue(object value, System.Type targetType)
        {
            if (value == null)
                return null;

            try
            {
                // 如果类型已匹配
                if (targetType.IsAssignableFrom(value.GetType()))
                    return value;

                // 字符串转换
                if (value is string strValue)
                {
                    if (targetType == typeof(int))
                        return int.Parse(strValue);
                    if (targetType == typeof(float))
                        return float.Parse(strValue);
                    if (targetType == typeof(double))
                        return double.Parse(strValue);
                    if (targetType == typeof(bool))
                        return bool.Parse(strValue);
                    if (targetType.IsEnum)
                        return System.Enum.Parse(targetType, strValue);
                }

                // 数值类型转换
                if (targetType == typeof(float) && (value is int || value is double))
                    return System.Convert.ToSingle(value);

                if (targetType == typeof(int) && (value is float || value is double))
                    return System.Convert.ToInt32(value);

                // 枚举转换
                if (targetType.IsEnum && value is string enumStr)
                    return System.Enum.Parse(targetType, enumStr);

                // 默认转换
                return System.Convert.ChangeType(value, targetType);
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// 获取总频率
        /// </summary>
        private static int GetTotalFrequency(List<EditorRAGClient.ActionRecommendation> suggestions)
        {
            int total = 0;
            foreach (var suggestion in suggestions)
            {
                total += suggestion.frequency;
            }
            return total;
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
