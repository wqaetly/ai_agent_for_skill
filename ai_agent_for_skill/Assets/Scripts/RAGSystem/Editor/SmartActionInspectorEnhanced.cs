using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Cysharp.Threading.Tasks;
using UnityEditor;
using UnityEngine;

namespace SkillSystem.RAG
{
    /// <summary>
    /// 智能Action检查器增强版（REQ-04）
    /// 提供参数推荐、差异对比、验证和一键应用功能
    /// </summary>
    public static class SmartActionInspectorEnhanced
    {
        private static EditorRAGClient ragClient;
        private static bool isInitialized = false;

        // UI状态
        private static bool showSmartPanel = true;
        private static Vector2 scrollPos;
        private static bool isLoading = false;
        private static string currentActionType = "";

        // 推荐数据
        private static EditorRAGClient.RecommendParametersResponse currentRecommendations;
        private static int selectedRecommendationIndex = -1;

        // 验证数据
        private static EditorRAGClient.ValidateParametersResponse validationResult;

        // 差异数据
        private static EditorRAGClient.CompareParametersResponse comparisonResult;

        // 操作历史栈（用于撤销）
        private static Stack<ParameterSnapshot> undoStack = new Stack<ParameterSnapshot>();
        private const int MAX_UNDO_HISTORY = 20;

        // 会话ID
        private static string sessionId;

        /// <summary>
        /// 参数快照（用于撤销）
        /// </summary>
        private class ParameterSnapshot
        {
            public string ActionType;
            public Dictionary<string, object> Parameters;
            public DateTime Timestamp;
        }

        /// <summary>
        /// 初始化
        /// </summary>
        public static void Initialize()
        {
            if (isInitialized)
                return;

            ragClient = new EditorRAGClient();
            undoStack = new Stack<ParameterSnapshot>();
            sessionId = System.Guid.NewGuid().ToString();
            isInitialized = true;

            Debug.Log($"[SmartActionInspectorEnhanced] 初始化完成，会话ID: {sessionId}");
        }

        /// <summary>
        /// 绘制智能建议面板
        /// </summary>
        public static void DrawSmartPanel(SkillSystem.Actions.ISkillAction action, string skillName, string trackName, int trackIndex)
        {
            if (!isInitialized)
                Initialize();

            if (action == null)
                return;

            string actionType = action.GetType().Name;

            EditorGUILayout.Space(10);

            // 主面板
            EditorGUILayout.BeginVertical("box");

            // 标题栏
            EditorGUILayout.BeginHorizontal();
            showSmartPanel = EditorGUILayout.Foldout(showSmartPanel, "🤖 AI参数助手（REQ-04）", true, EditorStyles.foldoutHeader);

            GUI.enabled = !isLoading;
            if (GUILayout.Button("刷新推荐", EditorStyles.miniButton, GUILayout.Width(70)))
            {
                RefreshRecommendations(action, skillName, trackName, trackIndex).Forget();
            }

            if (undoStack.Count > 0 && GUILayout.Button($"撤销 ({undoStack.Count})", EditorStyles.miniButton, GUILayout.Width(70)))
            {
                UndoLastChange(action);
            }
            GUI.enabled = true;

            EditorGUILayout.EndHorizontal();

            if (showSmartPanel)
            {
                EditorGUI.indentLevel++;

                if (isLoading)
                {
                    EditorGUILayout.LabelField("⏳ 正在加载AI推荐...", EditorStyles.miniLabel);
                }
                else if (currentRecommendations != null && currentRecommendations.count > 0)
                {
                    DrawRecommendationsPanel(action);
                }
                else
                {
                    EditorGUILayout.HelpBox("点击\"刷新推荐\"获取AI参数建议", MessageType.Info);
                }

                EditorGUI.indentLevel--;
            }

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 绘制推荐面板
        /// </summary>
        private static void DrawRecommendationsPanel(SkillSystem.Actions.ISkillAction action)
        {
            EditorGUILayout.LabelField($"找到 {currentRecommendations.count} 个推荐配置:", EditorStyles.boldLabel);
            EditorGUILayout.Space(3);

            scrollPos = EditorGUILayout.BeginScrollView(scrollPos, GUILayout.MaxHeight(400));

            for (int i = 0; i < currentRecommendations.recommendations.Count; i++)
            {
                var recommendation = currentRecommendations.recommendations[i];
                bool isSelected = (i == selectedRecommendationIndex);

                DrawRecommendationItem(action, recommendation, i, isSelected);
            }

            EditorGUILayout.EndScrollView();
        }

        /// <summary>
        /// 绘制单个推荐项
        /// </summary>
        private static void DrawRecommendationItem(
            SkillSystem.Actions.ISkillAction action,
            EditorRAGClient.ParameterRecommendation recommendation,
            int index,
            bool isSelected)
        {
            try
            {
                // 选中时高亮显示
                Color originalColor = GUI.backgroundColor;
                if (isSelected)
                    GUI.backgroundColor = new Color(0.5f, 0.8f, 1.0f);

                EditorGUILayout.BeginVertical("box");
                GUI.backgroundColor = originalColor;

                // 标题行
                EditorGUILayout.BeginHorizontal();
                EditorGUILayout.LabelField($"#{index + 1} {recommendation.source_skill}", EditorStyles.boldLabel);
                EditorGUILayout.LabelField($"相似度: {recommendation.similarity:P0}", GUILayout.Width(80));
                EditorGUILayout.EndHorizontal();

                // 来源信息
                EditorGUILayout.LabelField($"来源: {recommendation.source_file}", EditorStyles.miniLabel);

                // 推理说明
                if (!string.IsNullOrEmpty(recommendation.reasoning))
                {
                    EditorGUILayout.LabelField($"💡 {recommendation.reasoning}", EditorStyles.wordWrappedMiniLabel);
                }

                EditorGUILayout.Space(2);

                // 参数列表
                EditorGUILayout.LabelField("推荐参数:", EditorStyles.miniLabel);
                EditorGUI.indentLevel++;

                var currentParams = ExtractActionParameters(action);

                if (recommendation.parameters != null)
                {
                    foreach (var param in recommendation.parameters)
                    {
                        EditorGUILayout.BeginHorizontal();
                        EditorGUILayout.LabelField(param.Key, GUILayout.Width(120));

                        // 显示当前值 vs 推荐值
                        var currentValue = currentParams.ContainsKey(param.Key) ? currentParams[param.Key] : null;
                        bool isDifferent = currentValue == null || !currentValue.Equals(param.Value);

                        if (isDifferent)
                            GUI.contentColor = new Color(1f, 0.8f, 0.3f);

                        EditorGUILayout.LabelField($"{currentValue} → {param.Value}", EditorStyles.miniLabel);

                        GUI.contentColor = Color.white;
                        EditorGUILayout.EndHorizontal();
                    }
                }

                EditorGUI.indentLevel--;

                EditorGUILayout.Space(2);

                // 操作按钮行
                EditorGUILayout.BeginHorizontal();

                if (GUILayout.Button(isSelected ? "✓ 已选择" : "查看详情", EditorStyles.miniButton))
                {
                    // 延迟到下一帧修改选择状态，避免GUI结构在同一帧内变化
                    int newIndex = isSelected ? -1 : index;
                    EditorApplication.delayCall += () =>
                    {
                        selectedRecommendationIndex = newIndex;
                        if (newIndex >= 0)
                            CompareWithCurrent(action, recommendation).Forget();
                    };
                }

                GUI.enabled = isSelected;
                if (GUILayout.Button("✓ 应用此配置", EditorStyles.miniButtonMid))
                {
                    ApplyRecommendation(action, recommendation).Forget();
                }
                GUI.enabled = true;

                // 始终保留按钮位置，避免GUI结构变化
                if (GUILayout.Button("验证参数", EditorStyles.miniButtonRight))
                {
                    if (isSelected && comparisonResult != null)
                    {
                        ValidateParameters(action, recommendation).Forget();
                    }
                }

                EditorGUILayout.EndHorizontal();

                // 显示差异对比（如果已选择）
                if (isSelected && comparisonResult != null)
                {
                    DrawComparisonResult();
                }

                // 显示验证结果（如果已验证）
                if (isSelected && validationResult != null)
                {
                    DrawValidationResult();
                }
            }
            finally
            {
                EditorGUILayout.EndVertical();
                EditorGUILayout.Space(3);
            }
        }

        /// <summary>
        /// 绘制差异对比结果
        /// </summary>
        private static void DrawComparisonResult()
        {
            try
            {
                EditorGUILayout.BeginVertical("box");
                EditorGUILayout.LabelField("📊 参数差异对比", EditorStyles.boldLabel);

                // 风险等级
                Color riskColor = comparisonResult.risk_level switch
                {
                    "high" => Color.red,
                    "medium" => Color.yellow,
                    "low" => Color.green,
                    _ => Color.gray
                };

                GUI.contentColor = riskColor;
                EditorGUILayout.LabelField($"风险等级: {comparisonResult.risk_level.ToUpper()} ({comparisonResult.total_changes} 处变化)", EditorStyles.boldLabel);
                GUI.contentColor = Color.white;

                EditorGUILayout.Space(2);

                // 详细差异列表
                if (comparisonResult.differences != null)
                {
                    foreach (var diff in comparisonResult.differences)
                    {
                        EditorGUILayout.BeginHorizontal();

                        // 重要性指示器
                        string indicator = diff.significance switch
                        {
                            "high" => "🔴",
                            "medium" => "🟡",
                            "low" => "🟢",
                            _ => "⚪"
                        };

                        EditorGUILayout.LabelField(indicator, GUILayout.Width(20));
                        EditorGUILayout.LabelField(diff.field, GUILayout.Width(100));
                        EditorGUILayout.LabelField($"{diff.current} → {diff.recommended}", EditorStyles.miniLabel);

                        EditorGUILayout.EndHorizontal();
                    }
                }
            }
            finally
            {
                EditorGUILayout.EndVertical();
            }
        }

        /// <summary>
        /// 绘制验证结果
        /// </summary>
        private static void DrawValidationResult()
        {
            try
            {
                EditorGUILayout.BeginVertical("box");
                EditorGUILayout.LabelField("✓ 参数验证结果", EditorStyles.boldLabel);

                // 验证状态
                if (validationResult.valid)
                {
                    GUI.contentColor = Color.green;
                    EditorGUILayout.LabelField("✓ 参数验证通过", EditorStyles.boldLabel);
                    GUI.contentColor = Color.white;
                }
                else
                {
                    GUI.contentColor = Color.red;
                    EditorGUILayout.LabelField("✗ 参数验证失败", EditorStyles.boldLabel);
                    GUI.contentColor = Color.white;
                }

                // 错误列表
                if (validationResult.errors != null && validationResult.errors.Count > 0)
                {
                    EditorGUILayout.Space(2);
                    EditorGUILayout.LabelField("❌ 错误:", EditorStyles.boldLabel);
                    foreach (var error in validationResult.errors)
                    {
                        EditorGUILayout.HelpBox($"{error.field}: {error.message}", MessageType.Error);
                    }
                }

                // 警告列表
                if (validationResult.warnings != null && validationResult.warnings.Count > 0)
                {
                    EditorGUILayout.Space(2);
                    EditorGUILayout.LabelField("⚠️ 警告:", EditorStyles.boldLabel);
                    foreach (var warning in validationResult.warnings)
                    {
                        EditorGUILayout.HelpBox($"{warning.field}: {warning.message}", MessageType.Warning);
                    }
                }

                // 建议列表
                if (validationResult.suggestions != null && validationResult.suggestions.Count > 0)
                {
                    EditorGUILayout.Space(2);
                    EditorGUILayout.LabelField("💡 建议:", EditorStyles.boldLabel);
                    foreach (var suggestion in validationResult.suggestions)
                    {
                        EditorGUILayout.LabelField($"• {suggestion.field}: {suggestion.reason}", EditorStyles.wordWrappedMiniLabel);
                    }
                }
            }
            finally
            {
                EditorGUILayout.EndVertical();
            }
        }

        /// <summary>
        /// 刷新推荐
        /// </summary>
        private static async UniTaskVoid RefreshRecommendations(
            SkillSystem.Actions.ISkillAction action,
            string skillName,
            string trackName,
            int trackIndex)
        {
            if (isLoading)
                return;

            isLoading = true;
            currentActionType = action.GetType().Name;
            selectedRecommendationIndex = -1;
            comparisonResult = null;
            validationResult = null;

            try
            {
                // 构建上下文
                var context = new EditorRAGClient.ActionContext
                {
                    skill_name = skillName,
                    track_name = trackName,
                    track_index = trackIndex,
                    frame = GetActionFrame(action),
                    existing_actions = new List<EditorRAGClient.ExistingActionInfo>()
                };

                // 调用API
                var response = await ragClient.RecommendParametersAsync(
                    actionType: currentActionType,
                    context: context,
                    topK: 5,
                    includeReasoning: true
                );

                currentRecommendations = response;
                Debug.Log($"[SmartActionInspectorEnhanced] 获取到 {response.count} 个推荐");
            }
            catch (Exception e)
            {
                Debug.LogError($"[SmartActionInspectorEnhanced] 获取推荐失败: {e.Message}");
                currentRecommendations = null;
            }
            finally
            {
                isLoading = false;
            }
        }

        /// <summary>
        /// 对比当前参数和推荐参数
        /// </summary>
        private static async UniTaskVoid CompareWithCurrent(
            SkillSystem.Actions.ISkillAction action,
            EditorRAGClient.ParameterRecommendation recommendation)
        {
            try
            {
                var currentParams = ExtractActionParameters(action);
                var recommendedParams = recommendation.parameters;

                var response = await ragClient.CompareParametersAsync(
                    actionType: action.GetType().Name,
                    currentParameters: currentParams,
                    recommendedParameters: recommendedParams
                );

                comparisonResult = response;
                validationResult = null;  // 清空之前的验证结果

                Debug.Log($"[SmartActionInspectorEnhanced] 参数对比完成: {response.total_changes} 处差异");
            }
            catch (Exception e)
            {
                Debug.LogError($"[SmartActionInspectorEnhanced] 参数对比失败: {e.Message}");
                comparisonResult = null;
            }
        }

        /// <summary>
        /// 验证推荐参数
        /// </summary>
        private static async UniTaskVoid ValidateParameters(
            SkillSystem.Actions.ISkillAction action,
            EditorRAGClient.ParameterRecommendation recommendation)
        {
            try
            {
                var response = await ragClient.ValidateParametersAsync(
                    actionType: action.GetType().Name,
                    parameters: recommendation.parameters,
                    context: null
                );

                validationResult = response;

                Debug.Log($"[SmartActionInspectorEnhanced] 参数验证完成: valid={response.valid}");
            }
            catch (Exception e)
            {
                Debug.LogError($"[SmartActionInspectorEnhanced] 参数验证失败: {e.Message}");
                validationResult = null;
            }
        }

        /// <summary>
        /// 应用推荐参数
        /// </summary>
        private static async UniTaskVoid ApplyRecommendation(
            SkillSystem.Actions.ISkillAction action,
            EditorRAGClient.ParameterRecommendation recommendation)
        {
            try
            {
                // 保存当前参数到撤销栈
                SaveToUndoStack(action);

                // 应用新参数
                var oldParams = ExtractActionParameters(action);
                ApplyParametersToAction(action, recommendation.parameters);

                Debug.Log($"[SmartActionInspectorEnhanced] 参数已应用，来源: {recommendation.source_skill}");

                // 记录操作日志
                await ragClient.LogOperationAsync(
                    operation: "apply_parameters",
                    actionType: action.GetType().Name,
                    oldParameters: oldParams,
                    newParameters: recommendation.parameters,
                    user: "Unity Editor",
                    sessionId: sessionId
                );

                // 清空选择
                selectedRecommendationIndex = -1;
                comparisonResult = null;
                validationResult = null;

                // 注意：不需要SetDirty，因为ActionInspector会处理刷新
                // ISkillAction不继承自UnityEngine.Object

                EditorUtility.DisplayDialog("成功", "参数已成功应用！", "确定");
            }
            catch (Exception e)
            {
                Debug.LogError($"[SmartActionInspectorEnhanced] 应用参数失败: {e.Message}");
                EditorUtility.DisplayDialog("错误", $"应用参数失败: {e.Message}", "确定");
            }
        }

        /// <summary>
        /// 撤销最后一次更改
        /// </summary>
        private static void UndoLastChange(SkillSystem.Actions.ISkillAction action)
        {
            if (undoStack.Count == 0)
                return;

            var snapshot = undoStack.Pop();

            if (snapshot.ActionType == action.GetType().Name)
            {
                ApplyParametersToAction(action, snapshot.Parameters);
                Debug.Log($"[SmartActionInspectorEnhanced] 已撤销到 {snapshot.Timestamp}");

                // 注意：不需要SetDirty，因为ActionInspector会处理刷新
                // ISkillAction不继承自UnityEngine.Object
            }
            else
            {
                Debug.LogWarning("[SmartActionInspectorEnhanced] Action类型不匹配，无法撤销");
                undoStack.Push(snapshot);  // 放回栈
            }
        }

        /// <summary>
        /// 保存到撤销栈
        /// </summary>
        private static void SaveToUndoStack(SkillSystem.Actions.ISkillAction action)
        {
            var snapshot = new ParameterSnapshot
            {
                ActionType = action.GetType().Name,
                Parameters = ExtractActionParameters(action),
                Timestamp = DateTime.Now
            };

            undoStack.Push(snapshot);

            // 限制栈大小
            if (undoStack.Count > MAX_UNDO_HISTORY)
            {
                var tempStack = new Stack<ParameterSnapshot>(undoStack.Reverse().Take(MAX_UNDO_HISTORY));
                undoStack = new Stack<ParameterSnapshot>(tempStack.Reverse());
            }
        }

        /// <summary>
        /// 提取Action的参数
        /// </summary>
        private static Dictionary<string, object> ExtractActionParameters(SkillSystem.Actions.ISkillAction action)
        {
            var parameters = new Dictionary<string, object>();
            var type = action.GetType();

            foreach (var field in type.GetFields(BindingFlags.Public | BindingFlags.Instance))
            {
                if (field.Name == "frame" || field.Name == "duration")
                    continue;  // 跳过基础字段

                var value = field.GetValue(action);
                if (value != null)
                    parameters[field.Name] = value;
            }

            foreach (var property in type.GetProperties(BindingFlags.Public | BindingFlags.Instance))
            {
                if (!property.CanRead || !property.CanWrite)
                    continue;

                if (property.Name == "frame" || property.Name == "duration")
                    continue;

                var value = property.GetValue(action);
                if (value != null)
                    parameters[property.Name] = value;
            }

            return parameters;
        }

        /// <summary>
        /// 应用参数到Action
        /// </summary>
        private static void ApplyParametersToAction(SkillSystem.Actions.ISkillAction action, Dictionary<string, object> parameters)
        {
            var type = action.GetType();

            foreach (var param in parameters)
            {
                try
                {
                    // 尝试设置字段
                    var field = type.GetField(param.Key, BindingFlags.Public | BindingFlags.Instance);
                    if (field != null)
                    {
                        var convertedValue = Convert.ChangeType(param.Value, field.FieldType);
                        field.SetValue(action, convertedValue);
                        continue;
                    }

                    // 尝试设置属性
                    var property = type.GetProperty(param.Key, BindingFlags.Public | BindingFlags.Instance);
                    if (property != null && property.CanWrite)
                    {
                        var convertedValue = Convert.ChangeType(param.Value, property.PropertyType);
                        property.SetValue(action, convertedValue);
                    }
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[SmartActionInspectorEnhanced] 无法设置参数 {param.Key}: {e.Message}");
                }
            }
        }

        /// <summary>
        /// 获取Action的frame值
        /// </summary>
        private static int GetActionFrame(SkillSystem.Actions.ISkillAction action)
        {
            var field = action.GetType().GetField("frame", BindingFlags.Public | BindingFlags.Instance);
            if (field != null)
            {
                return (int)field.GetValue(action);
            }
            return 0;
        }

        /// <summary>
        /// 清空缓存
        /// </summary>
        public static void ClearCache()
        {
            currentRecommendations = null;
            comparisonResult = null;
            validationResult = null;
            selectedRecommendationIndex = -1;
            undoStack.Clear();
            Debug.Log("[SmartActionInspectorEnhanced] 缓存已清空");
        }
    }
}
