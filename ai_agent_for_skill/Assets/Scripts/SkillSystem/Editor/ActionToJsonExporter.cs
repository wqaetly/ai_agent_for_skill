using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using Sirenix.OdinInspector;
using SkillSystem.Actions;

namespace SkillSystem.Editor
{
    /// <summary>
    /// Action脚本导出工具
    /// 将所有ISkillAction子类的元数据导出为JSON格式，用于RAG索引
    /// </summary>
    public class ActionToJsonExporter : EditorWindow
    {
        private const string ExportDirectory = "../SkillRAG/Data/Actions";
        private Vector2 scrollPosition;

        [MenuItem("Tools/Skill RAG/Export Actions to JSON")]
        public static void ShowWindow()
        {
            var window = GetWindow<ActionToJsonExporter>("Action Exporter");
            window.minSize = new Vector2(400, 300);
        }

        private void OnGUI()
        {
            GUILayout.Label("Action脚本导出工具", EditorStyles.boldLabel);
            GUILayout.Space(10);

            EditorGUILayout.HelpBox(
                "此工具将扫描所有Action脚本，提取类型、参数、特性等信息，并为每个Action生成独立的JSON文件用于RAG索引。\n" +
                $"导出目录: {ExportDirectory}/",
                MessageType.Info);

            GUILayout.Space(10);

            if (GUILayout.Button("导出所有Actions", GUILayout.Height(40)))
            {
                ExportActions();
            }

            GUILayout.Space(10);

            if (GUILayout.Button("预览Actions列表", GUILayout.Height(30)))
            {
                PreviewActions();
            }
        }

        private void ExportActions()
        {
            try
            {
                var actions = CollectAllActions();

                // 确保导出目录存在
                string fullDirectory = System.IO.Path.GetFullPath(ExportDirectory);
                if (!System.IO.Directory.Exists(fullDirectory))
                {
                    System.IO.Directory.CreateDirectory(fullDirectory);
                }

                int successCount = 0;
                int failCount = 0;

                // 为每个Action生成独立的JSON文件
                foreach (var action in actions)
                {
                    try
                    {
                        // 构建单个Action的JSON数据
                        var actionFile = new ActionFile
                        {
                            version = "1.0",
                            exportTime = DateTime.Now.ToString("o"),
                            action = action
                        };

                        string json = JsonUtility.ToJson(actionFile, true);

                        // 文件名：ActionTypeName.json
                        string fileName = $"{action.typeName}.json";
                        string filePath = System.IO.Path.Combine(fullDirectory, fileName);

                        System.IO.File.WriteAllText(filePath, json);
                        successCount++;

                        Debug.Log($"✅ 导出: {fileName}");
                    }
                    catch (Exception e)
                    {
                        Debug.LogError($"❌ 导出 {action.typeName} 失败: {e.Message}");
                        failCount++;
                    }
                }

                Debug.Log($"✅ 导出完成: 成功 {successCount} 个，失败 {failCount} 个");
                Debug.Log($"导出目录: {fullDirectory}");

                EditorUtility.DisplayDialog("导出完成",
                    $"成功导出 {successCount} 个Action\n" +
                    $"失败 {failCount} 个\n" +
                    $"导出目录: {fullDirectory}", "确定");
            }
            catch (Exception e)
            {
                Debug.LogError($"❌ 导出失败: {e.Message}\n{e.StackTrace}");
                EditorUtility.DisplayDialog("导出失败", $"错误: {e.Message}", "确定");
            }
        }

        private void PreviewActions()
        {
            var actions = CollectAllActions();

            Debug.Log($"=== Action列表预览 ({actions.Count}个) ===");
            foreach (var action in actions.OrderBy(a => a.category).ThenBy(a => a.displayName))
            {
                Debug.Log($"[{action.category}] {action.displayName} ({action.typeName}) - {action.parameters.Count}个参数");
            }
        }

        private List<ActionDefinition> CollectAllActions()
        {
            var results = new List<ActionDefinition>();

            // 获取所有ISkillAction的子类
            var actionTypes = Assembly.GetAssembly(typeof(ISkillAction))
                .GetTypes()
                .Where(t => t.IsSubclassOf(typeof(ISkillAction)) && !t.IsAbstract)
                .OrderBy(t => t.Name);

            foreach (var type in actionTypes)
            {
                try
                {
                    var definition = ExtractActionInfo(type);
                    results.Add(definition);
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"⚠️ 跳过Action {type.Name}: {e.Message}");
                }
            }

            return results;
        }

        private ActionDefinition ExtractActionInfo(Type actionType)
        {
            var definition = new ActionDefinition
            {
                typeName = actionType.Name,
                fullTypeName = $"{actionType.Namespace}.{actionType.Name}",
                assemblyName = actionType.Assembly.GetName().Name,
                namespaceName = actionType.Namespace
            };

            // 提取ActionDisplayName特性
            var displayAttr = actionType.GetCustomAttribute<ActionDisplayNameAttribute>();
            definition.displayName = displayAttr?.DisplayName ?? actionType.Name;

            // 提取ActionCategory特性
            var categoryAttr = actionType.GetCustomAttribute<ActionCategoryAttribute>();
            definition.category = categoryAttr?.Category ?? "Other";

            // 提取类的XML注释（简化版本，从summary标签提取）
            var xmlComments = ExtractXmlComments(actionType);
            definition.description = xmlComments;

            // 提取字段信息
            definition.parameters = ExtractParameters(actionType);

            // 生成示例用途文本
            definition.searchText = BuildSearchText(definition);

            return definition;
        }

        private List<ParameterInfo> ExtractParameters(Type actionType)
        {
            var parameters = new List<ParameterInfo>();
            var fields = actionType.GetFields(BindingFlags.Public | BindingFlags.Instance);

            // 创建实例以获取默认值
            object instance = null;
            try
            {
                instance = Activator.CreateInstance(actionType);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"无法创建 {actionType.Name} 的实例: {e.Message}");
            }

            foreach (var field in fields)
            {
                // 跳过基类字段（frame, duration, enabled）
                if (field.DeclaringType == typeof(ISkillAction))
                    continue;

                var param = new ParameterInfo
                {
                    name = field.Name,
                    type = GetFriendlyTypeName(field.FieldType),
                    isArray = field.FieldType.IsArray,
                    isEnum = field.FieldType.IsEnum
                };

                // 获取默认值
                if (instance != null)
                {
                    try
                    {
                        object value = field.GetValue(instance);
                        param.defaultValue = SerializeValue(value);
                    }
                    catch
                    {
                        param.defaultValue = "null";
                    }
                }

                // 提取Odin特性
                ExtractOdinAttributes(field, param);

                // 提取枚举值
                if (field.FieldType.IsEnum)
                {
                    param.enumValues = Enum.GetNames(field.FieldType).ToList();
                }

                // 提取数组元素类型
                if (field.FieldType.IsArray)
                {
                    param.elementType = GetFriendlyTypeName(field.FieldType.GetElementType());
                }

                parameters.Add(param);
            }

            return parameters;
        }

        private void ExtractOdinAttributes(FieldInfo field, ParameterInfo param)
        {
            // LabelText
            var labelAttr = field.GetCustomAttribute<LabelTextAttribute>();
            if (labelAttr != null)
            {
                param.label = labelAttr.Text;
            }

            // BoxGroup
            var boxGroupAttr = field.GetCustomAttribute<BoxGroupAttribute>();
            if (boxGroupAttr != null)
            {
                param.group = boxGroupAttr.GroupName;
            }

            // InfoBox
            var infoBoxAttr = field.GetCustomAttribute<InfoBoxAttribute>();
            if (infoBoxAttr != null)
            {
                param.infoBox = infoBoxAttr.Message;
            }

            // MinValue
            var minValueAttr = field.GetCustomAttribute<MinValueAttribute>();
            if (minValueAttr != null)
            {
                param.constraints.minValue = minValueAttr.MinValue.ToString();
            }

            // Range
            var rangeAttr = field.GetCustomAttribute<RangeAttribute>();
            if (rangeAttr != null)
            {
                param.constraints.min = rangeAttr.min.ToString();
                param.constraints.max = rangeAttr.max.ToString();
            }

            // 提取字段的XML注释
            var fieldComments = ExtractFieldXmlComments(field);
            if (!string.IsNullOrEmpty(fieldComments))
            {
                param.description = fieldComments;
            }
        }

        private string ExtractXmlComments(Type type)
        {
            // 简化版本：尝试从类型的文档字符串中提取
            // 完整实现需要解析生成的XML文档文件
            // 这里我们返回空字符串，实际注释会在代码中手动添加
            return "";
        }

        private string ExtractFieldXmlComments(FieldInfo field)
        {
            // 简化版本：返回空字符串
            // 在实际使用中，字段的注释会通过InfoBoxAttribute或代码中的summary标签提供
            return "";
        }

        private string GetFriendlyTypeName(Type type)
        {
            if (type == null) return "unknown";

            if (type == typeof(int)) return "int";
            if (type == typeof(float)) return "float";
            if (type == typeof(double)) return "double";
            if (type == typeof(bool)) return "bool";
            if (type == typeof(string)) return "string";
            if (type == typeof(Vector2)) return "Vector2";
            if (type == typeof(Vector3)) return "Vector3";
            if (type == typeof(Vector4)) return "Vector4";
            if (type == typeof(Color)) return "Color";
            if (type == typeof(Quaternion)) return "Quaternion";

            if (type.IsArray)
            {
                return GetFriendlyTypeName(type.GetElementType()) + "[]";
            }

            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>))
            {
                return "List<" + GetFriendlyTypeName(type.GetGenericArguments()[0]) + ">";
            }

            return type.Name;
        }

        private string SerializeValue(object value)
        {
            if (value == null) return "null";

            if (value is string str) return $"\"{str}\"";
            if (value is bool b) return b.ToString().ToLower();
            if (value is int || value is float || value is double) return value.ToString();

            if (value is Vector2 v2) return $"({v2.x}, {v2.y})";
            if (value is Vector3 v3) return $"({v3.x}, {v3.y}, {v3.z})";
            if (value is Vector4 v4) return $"({v4.x}, {v4.y}, {v4.z}, {v4.w})";
            if (value is Color c) return $"RGBA({c.r:F2}, {c.g:F2}, {c.b:F2}, {c.a:F2})";
            if (value is Quaternion q) return $"({q.x}, {q.y}, {q.z}, {q.w})";

            if (value is Enum e) return e.ToString();

            if (value.GetType().IsArray)
            {
                var array = value as Array;
                if (array.Length == 0) return "[]";
                return $"[{array.Length} items]";
            }

            return value.ToString();
        }

        private string BuildSearchText(ActionDefinition definition)
        {
            var parts = new List<string>();

            parts.Add($"Action类型: {definition.typeName}");
            parts.Add($"显示名称: {definition.displayName}");
            parts.Add($"分类: {definition.category}");

            if (!string.IsNullOrEmpty(definition.description))
            {
                parts.Add($"功能描述: {definition.description}");
            }

            if (definition.parameters.Count > 0)
            {
                var paramNames = string.Join(", ", definition.parameters.Select(p => p.name));
                parts.Add($"参数: {paramNames}");

                // 添加主要参数的详细信息
                foreach (var param in definition.parameters.Take(5))
                {
                    var paramDesc = $"{param.label ?? param.name}({param.name})";
                    if (!string.IsNullOrEmpty(param.description))
                    {
                        paramDesc += $" - {param.description}";
                    }
                    else if (!string.IsNullOrEmpty(param.infoBox))
                    {
                        paramDesc += $" - {param.infoBox}";
                    }
                    parts.Add(paramDesc);
                }
            }

            return string.Join("\n", parts);
        }
    }

    // ===== 数据类定义 =====

    /// <summary>
    /// 单个Action文件的JSON结构
    /// </summary>
    [Serializable]
    public class ActionFile
    {
        public string version;
        public string exportTime;
        public ActionDefinition action;
    }

    /// <summary>
    /// 所有Action的集合（用于批量导出，已弃用）
    /// </summary>
    [Serializable]
    [Obsolete("不再使用单个大文件，改为每个Action一个文件")]
    public class ActionDefinitionRoot
    {
        public string version;
        public string exportTime;
        public int totalCount;
        public List<ActionDefinition> actions;
    }

    [Serializable]
    public class ActionDefinition
    {
        public string typeName;
        public string fullTypeName;
        public string namespaceName;
        public string assemblyName;
        public string displayName;
        public string category;
        public string description;
        public string searchText;
        public List<ParameterInfo> parameters = new List<ParameterInfo>();
    }

    [Serializable]
    public class ParameterInfo
    {
        public string name;
        public string type;
        public string label;
        public string group;
        public string description;
        public string infoBox;
        public string defaultValue;
        public bool isEnum;
        public bool isArray;
        public string elementType;
        public List<string> enumValues = new List<string>();
        public ParameterConstraints constraints = new ParameterConstraints();
    }

    [Serializable]
    public class ParameterConstraints
    {
        public string minValue;
        public string min;
        public string max;
    }
}
