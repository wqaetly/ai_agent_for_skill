using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using SkillSystem.Actions;
using UnityEngine;

namespace RAG
{
    /// <summary>
    /// Scans and collects Action types from assemblies
    /// </summary>
    public static class ActionScanner
    {
        /// <summary>
        /// Scan all Action types and create ActionEntry list
        /// </summary>
        /// <param name="database">The action description database to load existing data from</param>
        /// <returns>List of ActionEntry objects</returns>
        public static List<ActionEntry> ScanActions(ActionDescriptionDatabase database)
        {
            var actionEntries = new List<ActionEntry>();

            var actionTypes = Assembly.GetAssembly(typeof(ISkillAction))
                .GetTypes()
                .Where(t => t.IsSubclassOf(typeof(ISkillAction)) && !t.IsAbstract)
                .OrderBy(t => t.Name);

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
                    var displayAttr = type.GetCustomAttribute<ActionDisplayNameAttribute>();
                    var categoryAttr = type.GetCustomAttribute<ActionCategoryAttribute>();
                    entry.displayName = displayAttr?.DisplayName ?? type.Name;
                    entry.category = categoryAttr?.Category ?? "Other";
                }

                // Extract parameters for display
                entry.parameters = ExtractParameters(type, entry.parameterDescriptions);

                actionEntries.Add(entry);
            }

            return actionEntries;
        }

        /// <summary>
        /// Extract parameters from action type
        /// </summary>
        private static List<ActionParameterInfo> ExtractParameters(Type actionType, Dictionary<string, string> aiParameterDescriptions = null)
        {
            if (actionType == null) return new List<ActionParameterInfo>();

            var parameters = new List<ActionParameterInfo>();
            var fields = actionType.GetFields(BindingFlags.Public | BindingFlags.Instance);

            object instance = null;
            try { instance = Activator.CreateInstance(actionType); } catch { }

            foreach (var field in fields)
            {
                if (field.DeclaringType == typeof(ISkillAction))
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
        /// </summary>
        private static void ExtractOdinAttributes(FieldInfo field, ActionParameterInfo param)
        {
            var labelAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == "LabelTextAttribute");
            if (labelAttr != null)
            {
                var textProp = labelAttr.GetType().GetProperty("Text");
                if (textProp != null)
                    param.label = textProp.GetValue(labelAttr) as string;
            }

            var boxGroupAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == "BoxGroupAttribute");
            if (boxGroupAttr != null)
            {
                var groupNameProp = boxGroupAttr.GetType().GetProperty("GroupName");
                if (groupNameProp != null)
                    param.group = groupNameProp.GetValue(boxGroupAttr) as string;
            }

            var infoBoxAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == "InfoBoxAttribute");
            if (infoBoxAttr != null)
            {
                var messageProp = infoBoxAttr.GetType().GetProperty("Message");
                if (messageProp != null)
                    param.infoBox = messageProp.GetValue(infoBoxAttr) as string;
            }

            var minValueAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == "MinValueAttribute");
            if (minValueAttr != null)
            {
                var minValueProp = minValueAttr.GetType().GetProperty("MinValue");
                if (minValueProp != null)
                    param.constraints.minValue = minValueProp.GetValue(minValueAttr)?.ToString();
            }

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
