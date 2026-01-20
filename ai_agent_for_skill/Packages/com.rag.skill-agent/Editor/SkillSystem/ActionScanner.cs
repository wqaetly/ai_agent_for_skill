using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;

namespace RAG
{
    /// <summary>
    /// Scans and collects Action types from assemblies
    /// 使用配置驱动的方式扫描Action类型，支持适配不同项目的技能架构
    /// </summary>
    public static class ActionScanner
    {
        /// <summary>
        /// Scan all Action types and create ActionEntry list (无参数版本)
        /// </summary>
        public static List<ActionEntry> ScanActions()
        {
            return ScanActions(null);
        }

        /// <summary>
        /// Scan all Action types and create ActionEntry list
        /// 使用 RAGConfig 中配置的基类类型进行扫描
        /// </summary>
        /// <param name="database">The action description database to load existing data from</param>
        /// <returns>List of ActionEntry objects</returns>
        public static List<ActionEntry> ScanActions(ActionDescriptionDatabase database)
        {
            var actionEntries = new List<ActionEntry>();
            var config = RAGConfig.Instance;
            var typeConfig = config.skillSystemConfig;

            // 获取配置的基类类型
            Type baseActionType = typeConfig.GetBaseActionType();
            if (baseActionType == null)
            {
                Debug.LogError($"[ActionScanner] 无法找到配置的基类类型: {typeConfig.baseActionTypeName}");
                Debug.LogWarning("[ActionScanner] 请在 RAGConfig 中检查 skillSystemConfig.baseActionTypeName 配置");
                return actionEntries;
            }

            Debug.Log($"[ActionScanner] 使用基类类型: {baseActionType.FullName}");

            // 扫描所有继承自基类的非抽象类型
            var actionTypes = ScanActionTypes(baseActionType);
            Debug.Log($"[ActionScanner] 发现 {actionTypes.Count()} 个Action类型");

            foreach (var type in actionTypes)
            {
                var entry = new ActionEntry
                {
                    typeName = type.Name,
                    namespaceName = type.Namespace,
                    fullTypeName = $"{type.Namespace}.{type.Name}"
                };

                var existingData = database?.GetDescriptionByType(type.Name);
                if (existingData != null)
                {
                    entry.displayName = existingData.displayName;
                    entry.category = existingData.category;
                    entry.description = existingData.description;
                    entry.searchKeywords = existingData.searchKeywords;
                    entry.isAIGenerated = existingData.isAIGenerated;
                    entry.aiGeneratedTime = existingData.aiGeneratedTime;

                    // Load parameter descriptions from database
                    if (existingData.parameterDescriptions != null)
                    {
                        foreach (var kvp in existingData.parameterDescriptions)
                        {
                            entry.parameterDescriptions[kvp.Key] = kvp.Value;
                        }
                    }
                }
                else
                {
                    // 使用配置的特性名称查找显示名称和分类
                    entry.displayName = GetDisplayName(type, typeConfig) ?? type.Name;
                    entry.category = GetCategory(type, typeConfig) ?? "Other";
                }

                // Extract parameters for display
                entry.parameters = ExtractParameters(type, entry.parameterDescriptions, typeConfig);

                actionEntries.Add(entry);
            }

            return actionEntries;
        }

        /// <summary>
        /// 扫描所有继承自指定基类的Action类型
        /// </summary>
        private static IEnumerable<Type> ScanActionTypes(Type baseActionType)
        {
            var results = new List<Type>();

            // 遍历所有已加载的程序集
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    // 跳过系统程序集
                    if (assembly.FullName.StartsWith("System") ||
                        assembly.FullName.StartsWith("Unity") ||
                        assembly.FullName.StartsWith("mscorlib"))
                    {
                        continue;
                    }

                    var types = assembly.GetTypes()
                        .Where(t => t.IsSubclassOf(baseActionType) && !t.IsAbstract)
                        .OrderBy(t => t.Name);

                    results.AddRange(types);
                }
                catch (ReflectionTypeLoadException)
                {
                    // 某些程序集可能无法加载所有类型，忽略
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"[ActionScanner] 扫描程序集 {assembly.GetName().Name} 时出错: {ex.Message}");
                }
            }

            return results;
        }

        /// <summary>
        /// 使用配置的特性名称获取显示名称
        /// </summary>
        private static string GetDisplayName(Type type, SkillSystemTypeConfig config)
        {
            var attr = type.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == config.displayNameAttributeName);

            if (attr != null)
            {
                var prop = attr.GetType().GetProperty("DisplayName");
                if (prop != null)
                {
                    return prop.GetValue(attr) as string;
                }
            }

            return null;
        }

        /// <summary>
        /// 使用配置的特性名称获取分类
        /// </summary>
        private static string GetCategory(Type type, SkillSystemTypeConfig config)
        {
            var attr = type.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == config.categoryAttributeName);

            if (attr != null)
            {
                var prop = attr.GetType().GetProperty("Category");
                if (prop != null)
                {
                    return prop.GetValue(attr) as string;
                }
            }

            return null;
        }

        /// <summary>
        /// Extract parameters from action type
        /// 使用配置驱动的方式提取参数，支持不同的基类类型
        /// </summary>
        private static List<ActionParameterInfo> ExtractParameters(
            Type actionType,
            Dictionary<string, string> aiParameterDescriptions = null,
            SkillSystemTypeConfig typeConfig = null)
        {
            if (actionType == null) return new List<ActionParameterInfo>();

            typeConfig = typeConfig ?? RAGConfig.Instance.skillSystemConfig;
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

                ExtractOdinAttributes(field, param, typeConfig);

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
        private static void ExtractOdinAttributes(FieldInfo field, ActionParameterInfo param, SkillSystemTypeConfig typeConfig = null)
        {
            typeConfig = typeConfig ?? RAGConfig.Instance.skillSystemConfig;

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
        private static string GetFriendlyTypeName(Type type)
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
        private static string SerializeValue(object value)
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
    }
}
