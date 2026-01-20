using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;

namespace RAG
{
    /// <summary>
    /// Handles exporting Action data to JSON files
    /// 使用配置驱动的方式导出，支持适配不同项目的技能架构
    /// </summary>
    public class ActionJSONExporter
    {
        private string exportDirectory;
        private Action<string> logAction;
        private SkillSystemTypeConfig typeConfig;

        public ActionJSONExporter(string exportDirectory, Action<string> logAction = null)
        {
            this.exportDirectory = exportDirectory;
            this.logAction = logAction;
            this.typeConfig = RAGConfig.Instance.skillSystemConfig;
        }

        /// <summary>
        /// Export all actions to JSON files
        /// </summary>
        /// <param name="actionEntries">List of action entries to export</param>
        /// <returns>Tuple of (successCount, failCount)</returns>
        public (int successCount, int failCount) ExportActionsToJSON(List<ActionEntry> actionEntries)
        {
            int successCount = 0;
            int failCount = 0;

            try
            {
                string fullDirectory = Path.GetFullPath(exportDirectory);
                if (!Directory.Exists(fullDirectory))
                {
                    Directory.CreateDirectory(fullDirectory);
                }

                Log($"\n[Export] Starting JSON export to: {fullDirectory}");

                foreach (var entry in actionEntries)
                {
                    try
                    {
                        var actionFile = BuildActionFile(entry);
                        string json = JsonUtility.ToJson(actionFile, true);
                        string fileName = $"{entry.typeName}.json";
                        string filePath = Path.Combine(fullDirectory, fileName);

                        File.WriteAllText(filePath, json);
                        successCount++;
                    }
                    catch (Exception e)
                    {
                        Log($"[Export Error] {entry.typeName}: {e.Message}");
                        failCount++;
                    }
                }

                Log($"[Export] Complete - Success: {successCount}, Failed: {failCount}");
            }
            catch (Exception e)
            {
                Log($"[Export Failed] {e.Message}");
            }

            return (successCount, failCount);
        }

        /// <summary>
        /// Export actions to JSON silently (no dialogs)
        /// </summary>
        public int ExportActionsToJSONSilent(List<ActionEntry> actionEntries)
        {
            string fullDirectory = Path.GetFullPath(exportDirectory);
            if (!Directory.Exists(fullDirectory)) Directory.CreateDirectory(fullDirectory);

            int successCount = 0;
            foreach (var entry in actionEntries)
            {
                try
                {
                    var actionFile = BuildActionFile(entry);
                    string json = JsonUtility.ToJson(actionFile, true);
                    File.WriteAllText(Path.Combine(fullDirectory, $"{entry.typeName}.json"), json);
                    successCount++;
                }
                catch { }
            }

            Log($"  Exported {successCount} JSON files");
            return successCount;
        }

        /// <summary>
        /// Build ActionFile object from ActionEntry
        /// 使用配置驱动的方式查找类型
        /// </summary>
        public ActionFile BuildActionFile(ActionEntry entry)
        {
            // 使用配置驱动的方式查找类型
            Type actionType = FindActionType(entry.typeName);

            var definition = new ActionDefinition
            {
                typeName = entry.typeName,
                fullTypeName = entry.fullTypeName,
                namespaceName = entry.namespaceName,
                assemblyName = actionType?.Assembly.GetName().Name ?? typeConfig.assemblyName,
                displayName = entry.displayName,
                category = entry.category,
                description = entry.description,
                searchText = BuildSearchText(entry),
                parameters = ExtractParameters(actionType, entry.parameterDescriptions)
            };

            return new ActionFile
            {
                version = "1.0",
                exportTime = DateTime.Now.ToString("o"),
                action = definition
            };
        }

        /// <summary>
        /// 使用配置驱动的方式查找Action类型
        /// </summary>
        private Type FindActionType(string typeName)
        {
            Type baseActionType = typeConfig.GetBaseActionType();
            if (baseActionType == null) return null;

            // 遍历所有程序集查找类型
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    var type = assembly.GetTypes()
                        .FirstOrDefault(t => t.Name == typeName && t.IsSubclassOf(baseActionType));
                    if (type != null) return type;
                }
                catch (ReflectionTypeLoadException)
                {
                    // 忽略无法加载的程序集
                }
            }

            return null;
        }

        /// <summary>
        /// Build search text from action entry
        /// </summary>
        private string BuildSearchText(ActionEntry entry)
        {
            var parts = new List<string> { entry.displayName };
            if (!string.IsNullOrEmpty(entry.description))
                parts.Add(entry.description);
            if (!string.IsNullOrEmpty(entry.searchKeywords))
                parts.Add(entry.searchKeywords);
            parts.Add($"Category: {entry.category}");
            parts.Add($"Type: {entry.typeName}");
            return string.Join("\n", parts);
        }

        /// <summary>
        /// Extract parameters from action type
        /// 使用配置驱动的方式提取参数
        /// </summary>
        private List<ActionParameterInfo> ExtractParameters(Type actionType, Dictionary<string, string> aiParameterDescriptions = null)
        {
            if (actionType == null) return new List<ActionParameterInfo>();

            Type baseActionType = typeConfig.GetBaseActionType();

            var parameters = new List<ActionParameterInfo>();
            var fields = actionType.GetFields(BindingFlags.Public | BindingFlags.Instance);

            object instance = null;
            try { instance = Activator.CreateInstance(actionType); } catch { }

            foreach (var field in fields)
            {
                // 跳过基类定义的字段（使用配置的基类类型）
                if (baseActionType != null && field.DeclaringType == baseActionType)
                    continue;

                var param = new ActionParameterInfo
                {
                    name = field.Name,
                    type = GetFriendlyTypeName(field.FieldType),
                    isArray = field.FieldType.IsArray,
                    isEnum = field.FieldType.IsEnum
                };

                if (instance != null)
                {
                    try
                    {
                        object value = field.GetValue(instance);
                        param.defaultValue = SerializeValue(value);
                    }
                    catch { param.defaultValue = "null"; }
                }

                ExtractOdinAttributes(field, param);

                if (aiParameterDescriptions != null && aiParameterDescriptions.TryGetValue(field.Name, out string aiDesc))
                {
                    param.description = aiDesc;
                }

                if (field.FieldType.IsEnum)
                    param.enumValues = Enum.GetNames(field.FieldType).ToList();

                if (field.FieldType.IsArray)
                    param.elementType = GetFriendlyTypeName(field.FieldType.GetElementType());

                parameters.Add(param);
            }

            return parameters;
        }

        /// <summary>
        /// Extract Odin Inspector attributes from field
        /// 使用配置的特性名称进行提取
        /// </summary>
        private void ExtractOdinAttributes(FieldInfo field, ActionParameterInfo param)
        {
            // LabelText 特性
            var labelAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == typeConfig.labelTextAttributeName);
            if (labelAttr != null)
            {
                var textProp = labelAttr.GetType().GetProperty("Text");
                if (textProp != null)
                    param.label = textProp.GetValue(labelAttr) as string;
            }

            // BoxGroup 特性
            var boxGroupAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == typeConfig.boxGroupAttributeName);
            if (boxGroupAttr != null)
            {
                var groupNameProp = boxGroupAttr.GetType().GetProperty("GroupName");
                if (groupNameProp != null)
                    param.group = groupNameProp.GetValue(boxGroupAttr) as string;
            }

            // InfoBox 特性
            var infoBoxAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == typeConfig.infoBoxAttributeName);
            if (infoBoxAttr != null)
            {
                var messageProp = infoBoxAttr.GetType().GetProperty("Message");
                if (messageProp != null)
                    param.infoBox = messageProp.GetValue(infoBoxAttr) as string;
            }

            // MinValue 特性
            var minValueAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == typeConfig.minValueAttributeName);
            if (minValueAttr != null)
            {
                var minValueProp = minValueAttr.GetType().GetProperty("MinValue");
                if (minValueProp != null)
                    param.constraints.minValue = minValueProp.GetValue(minValueAttr)?.ToString();
            }

            // Unity Range 特性（这个是固定的）
            var rangeAttr = field.GetCustomAttribute<RangeAttribute>();
            if (rangeAttr != null)
            {
                param.constraints.min = rangeAttr.min.ToString();
                param.constraints.max = rangeAttr.max.ToString();
            }
        }

        /// <summary>
        /// Get friendly type name for display
        /// </summary>
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
                return GetFriendlyTypeName(type.GetElementType()) + "[]";

            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>))
                return "List<" + GetFriendlyTypeName(type.GetGenericArguments()[0]) + ">";

            return type.Name;
        }

        /// <summary>
        /// Serialize value to string representation
        /// </summary>
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
                return array.Length == 0 ? "[]" : $"[{array.Length} items]";
            }
            return value.ToString();
        }

        private void Log(string message)
        {
            logAction?.Invoke(message);
        }
    }
}
