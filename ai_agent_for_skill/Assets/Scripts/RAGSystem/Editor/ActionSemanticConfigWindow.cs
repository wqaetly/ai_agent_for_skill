using UnityEngine;
using UnityEditor;
using System.Collections.Generic;

namespace SkillSystem.RAG
{
    /// <summary>
    /// Action语义配置管理窗口
    /// 提供配置文件管理、测试和验证功能
    /// </summary>
    public class ActionSemanticConfigWindow : EditorWindow
    {
        private ActionSemanticRegistry registry;
        private ActionRecommendationEnhancer enhancer;
        private Vector2 scrollPos;

        // 测试相关
        private string testContext = "造成范围伤害的技能效果";
        private int testTopK = 3;
        private List<string> testExistingActions = new List<string>();
        private string testResult = "";

        [MenuItem("技能系统/Action语义配置管理", false, 103)]
        public static void ShowWindow()
        {
            var window = GetWindow<ActionSemanticConfigWindow>("Action语义配置");
            window.minSize = new Vector2(500, 400);
            window.Show();
        }

        private void OnEnable()
        {
            registry = ActionSemanticRegistry.Instance;
            enhancer = ActionRecommendationEnhancer.Instance;
        }

        private void OnGUI()
        {
            scrollPos = EditorGUILayout.BeginScrollView(scrollPos);

            DrawConfigInfo();
            EditorGUILayout.Space(10);
            DrawConfigManagement();
            EditorGUILayout.Space(10);
            DrawHealthCheck();
            EditorGUILayout.Space(10);
            DrawTestTools();

            EditorGUILayout.EndScrollView();
        }

        /// <summary>
        /// 绘制配置信息
        /// </summary>
        private void DrawConfigInfo()
        {
            EditorGUILayout.BeginVertical("box");
            EditorGUILayout.LabelField("配置信息", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            var actions = registry.GetAllSemanticInfo();
            var rules = registry.GetEnabledRules();

            EditorGUILayout.LabelField($"已注册Action: {actions.Count}");
            EditorGUILayout.LabelField($"已启用规则: {rules.Count}");
            EditorGUILayout.LabelField($"配置文件路径: {registry.GetConfigPath()}");
            EditorGUILayout.LabelField($"最后加载时间: {registry.GetLastLoadTime():yyyy-MM-dd HH:mm:ss}");

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 绘制配置管理
        /// </summary>
        private void DrawConfigManagement()
        {
            EditorGUILayout.BeginVertical("box");
            EditorGUILayout.LabelField("配置管理", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            EditorGUILayout.BeginHorizontal();

            if (GUILayout.Button("重新加载配置", GUILayout.Height(30)))
            {
                if (registry.ReloadConfig())
                {
                    ShowNotification(new GUIContent("配置已重新加载"));
                }
                else
                {
                    ShowNotification(new GUIContent("配置加载失败"));
                }
            }

            if (GUILayout.Button("保存配置", GUILayout.Height(30)))
            {
                if (registry.SaveConfig())
                {
                    ShowNotification(new GUIContent("配置已保存"));
                }
                else
                {
                    ShowNotification(new GUIContent("配置保存失败"));
                }
            }

            if (GUILayout.Button("在编辑器中打开", GUILayout.Height(30)))
            {
                string path = registry.GetConfigPath();
                if (System.IO.File.Exists(path))
                {
                    System.Diagnostics.Process.Start(path);
                }
                else
                {
                    EditorUtility.DisplayDialog("提示", "配置文件不存在，将自动创建", "确定");
                    registry.LoadConfig(); // 触发创建默认配置
                }
            }

            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(5);
            EditorGUILayout.HelpBox("修改配置文件后，点击\"重新加载配置\"以应用更改。配置支持热更新。", MessageType.Info);

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 绘制健康检查
        /// </summary>
        private void DrawHealthCheck()
        {
            EditorGUILayout.BeginVertical("box");
            EditorGUILayout.LabelField("系统健康检查", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            if (GUILayout.Button("执行健康检查", GUILayout.Height(30)))
            {
                string message;
                bool isHealthy = enhancer.HealthCheck(out message);

                if (isHealthy)
                {
                    EditorUtility.DisplayDialog("健康检查", message, "确定");
                }
                else
                {
                    EditorUtility.DisplayDialog("健康检查失败", message, "确定");
                }
            }

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 绘制测试工具
        /// </summary>
        private void DrawTestTools()
        {
            EditorGUILayout.BeginVertical("box");
            EditorGUILayout.LabelField("功能测试", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            EditorGUILayout.LabelField("测试上下文:");
            testContext = EditorGUILayout.TextArea(testContext, GUILayout.Height(60));

            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField("推荐数量:", GUILayout.Width(70));
            testTopK = EditorGUILayout.IntSlider(testTopK, 1, 10);
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(5);

            if (GUILayout.Button("测试约束验证", GUILayout.Height(30)))
            {
                TestConstraintValidation();
            }

            if (GUILayout.Button("测试评分系统", GUILayout.Height(30)))
            {
                TestScoringSystem();
            }

            // 显示测试结果
            if (!string.IsNullOrEmpty(testResult))
            {
                EditorGUILayout.Space(5);
                EditorGUILayout.TextArea(testResult, GUILayout.Height(150));
            }

            EditorGUILayout.EndVertical();
        }

        /// <summary>
        /// 测试约束验证
        /// </summary>
        private void TestConstraintValidation()
        {
            var testActions = new List<string> { "DamageAction", "HealAction", "ShieldAction" };

            var issues = new List<string>();
            bool isValid = enhancer.ValidateActionCombination(testActions, out issues);

            testResult = "=== 约束验证测试 ===\n";
            testResult += $"测试Action组合: {string.Join(", ", testActions)}\n";
            testResult += $"验证结果: {(isValid ? "通过" : "失败")}\n\n";

            if (issues.Count > 0)
            {
                testResult += "发现的问题:\n";
                foreach (var issue in issues)
                {
                    testResult += $"- {issue}\n";
                }
            }
            else
            {
                testResult += "未发现约束冲突\n";
            }

            testResult += "\n协同推荐测试:\n";
            var synergies = enhancer.GetSynergyRecommendations("DamageAction");
            testResult += $"DamageAction的协同Action: {string.Join(", ", synergies)}\n";

            Debug.Log(testResult);
        }

        /// <summary>
        /// 测试评分系统
        /// </summary>
        private void TestScoringSystem()
        {
            // 创建模拟推荐数据
            var mockRecommendations = new List<EditorRAGClient.ActionRecommendation>
            {
                new EditorRAGClient.ActionRecommendation
                {
                    action_type = "DamageAction",
                    display_name = "伤害",
                    category = "Damage",
                    description = "对目标造成伤害",
                    semantic_similarity = 0.85f
                },
                new EditorRAGClient.ActionRecommendation
                {
                    action_type = "ShieldAction",
                    display_name = "护盾",
                    category = "Defense",
                    description = "为目标提供护盾",
                    semantic_similarity = 0.65f
                },
                new EditorRAGClient.ActionRecommendation
                {
                    action_type = "MovementAction",
                    display_name = "位移",
                    category = "Movement",
                    description = "改变角色位置",
                    semantic_similarity = 0.55f
                }
            };

            // 执行增强
            var enhanced = enhancer.EnhanceRecommendations(
                mockRecommendations,
                testContext,
                null,
                false,
                testTopK
            );

            testResult = "=== 评分系统测试 ===\n";
            testResult += $"测试上下文: {testContext}\n\n";

            foreach (var rec in enhanced)
            {
                testResult += $"--- {rec.action_type} ---\n";
                testResult += $"语义相似度: {rec.semantic_similarity:P0}\n";
                testResult += $"业务得分: {rec.business_score:F2}\n";
                testResult += $"最终得分: {rec.final_score:P0}\n";
                testResult += $"验证状态: {(rec.is_valid ? "通过" : "失败")}\n";

                if (rec.reasons.Count > 0)
                {
                    testResult += "推荐理由:\n";
                    foreach (var reason in rec.reasons)
                    {
                        testResult += $"  • {reason}\n";
                    }
                }

                if (rec.warnings.Count > 0)
                {
                    testResult += "警告:\n";
                    foreach (var warning in rec.warnings)
                    {
                        testResult += $"  {warning}\n";
                    }
                }

                testResult += "\n";
            }

            Debug.Log(testResult);
        }
    }
}
