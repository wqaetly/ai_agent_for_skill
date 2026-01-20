using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;

namespace RAG.BuffSystem
{
    /// <summary>
    /// Buff扫描器 - 扫描项目中的所有Buff效果和触发器类型
    /// 使用配置驱动的方式扫描，通过反射获取类型信息，无外部类型依赖
    /// </summary>
    public static class BuffScanner
    {
        // 缓存的接口属性名称（通过反射读取）
        private const string EFFECT_NAME_PROPERTY = "EffectName";
        private const string TRIGGER_NAME_PROPERTY = "TriggerName";
        private const string DESCRIPTION_PROPERTY = "Description";

        /// <summary>
        /// 扫描所有Buff效果类型
        /// </summary>
        public static List<BuffEffectEntry> ScanBuffEffects()
        {
            var entries = new List<BuffEffectEntry>();
            var config = RAGConfig.Instance;
            var typeConfig = config.buffSystemConfig;

            // 通过配置获取基类/接口类型
            Type baseType = typeConfig.GetBuffEffectType();
            if (baseType == null)
            {
                Debug.LogError($"[BuffScanner] 无法找到Buff效果接口类型: {typeConfig.buffEffectTypeName}");
                Debug.LogWarning("[BuffScanner] 请在 RAGConfig 中检查 buffSystemConfig.buffEffectTypeName 配置");
                return entries;
            }

            Debug.Log($"[BuffScanner] 使用Buff效果基类/接口: {baseType.FullName}");

            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    var types = assembly.GetTypes()
                        .Where(t => baseType.IsAssignableFrom(t) &&
                                   !t.IsInterface &&
                                   !t.IsAbstract &&
                                   t.GetConstructor(Type.EmptyTypes) != null);

                    foreach (var type in types)
                    {
                        var entry = CreateEffectEntry(type, baseType);
                        if (entry != null)
                        {
                            entries.Add(entry);
                        }
                    }
                }
                catch (Exception)
                {
                    // 忽略无法加载的程序集
                }
            }

            Debug.Log($"[BuffScanner] 发现 {entries.Count} 个Buff效果类型");
            return entries;
        }

        /// <summary>
        /// 扫描所有Buff触发器类型
        /// </summary>
        public static List<BuffTriggerEntry> ScanBuffTriggers()
        {
            var entries = new List<BuffTriggerEntry>();
            var config = RAGConfig.Instance;
            var typeConfig = config.buffSystemConfig;

            // 通过配置获取基类/接口类型
            Type baseType = typeConfig.GetBuffTriggerType();
            if (baseType == null)
            {
                Debug.LogError($"[BuffScanner] 无法找到Buff触发器接口类型: {typeConfig.buffTriggerTypeName}");
                Debug.LogWarning("[BuffScanner] 请在 RAGConfig 中检查 buffSystemConfig.buffTriggerTypeName 配置");
                return entries;
            }

            Debug.Log($"[BuffScanner] 使用Buff触发器基类/接口: {baseType.FullName}");

            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    var types = assembly.GetTypes()
                        .Where(t => baseType.IsAssignableFrom(t) &&
                                   !t.IsInterface &&
                                   !t.IsAbstract &&
                                   t.GetConstructor(Type.EmptyTypes) != null);

                    foreach (var type in types)
                    {
                        var entry = CreateTriggerEntry(type, baseType);
                        if (entry != null)
                        {
                            entries.Add(entry);
                        }
                    }
                }
                catch (Exception)
                {
                    // 忽略无法加载的程序集
                }
            }

            Debug.Log($"[BuffScanner] 发现 {entries.Count} 个Buff触发器类型");
            return entries;
        }

        private static BuffEffectEntry CreateEffectEntry(Type type, Type baseType)
        {
            try
            {
                var instance = Activator.CreateInstance(type);
                if (instance == null) return null;

                // 通过反射获取接口属性值
                string effectName = GetPropertyValue<string>(instance, EFFECT_NAME_PROPERTY) ?? type.Name;
                string description = GetPropertyValue<string>(instance, DESCRIPTION_PROPERTY) ?? "";

                var entry = new BuffEffectEntry
                {
                    typeName = type.Name,
                    fullTypeName = type.FullName,
                    namespaceName = type.Namespace ?? "",
                    assemblyName = type.Assembly.GetName().Name,
                    displayName = GetDisplayName(type) ?? effectName,
                    description = description,
                    category = GetCategory(type),
                    parameters = ExtractParameters(type, baseType)
                };

                return entry;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[BuffScanner] Failed to create entry for {type.Name}: {e.Message}");
                return null;
            }
        }

        private static BuffTriggerEntry CreateTriggerEntry(Type type, Type baseType)
        {
            try
            {
                var instance = Activator.CreateInstance(type);
                if (instance == null) return null;

                // 通过反射获取接口属性值
                string triggerName = GetPropertyValue<string>(instance, TRIGGER_NAME_PROPERTY) ?? type.Name;
                string description = GetPropertyValue<string>(instance, DESCRIPTION_PROPERTY) ?? "";

                var entry = new BuffTriggerEntry
                {
                    typeName = type.Name,
                    fullTypeName = type.FullName,
                    namespaceName = type.Namespace ?? "",
                    assemblyName = type.Assembly.GetName().Name,
                    displayName = GetDisplayName(type) ?? triggerName,
                    description = description,
                    category = GetCategory(type),
                    parameters = ExtractParameters(type, baseType)
                };

                return entry;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[BuffScanner] Failed to create entry for {type.Name}: {e.Message}");
                return null;
            }
        }

        /// <summary>
        /// 通过反射获取属性值
        /// </summary>
        private static T GetPropertyValue<T>(object instance, string propertyName)
        {
            try
            {
                var prop = instance.GetType().GetProperty(propertyName,
                    BindingFlags.Public | BindingFlags.Instance);
                if (prop != null)
                {
                    var value = prop.GetValue(instance);
                    if (value is T result)
                        return result;
                }
            }
            catch { }
            return default;
        }

        private static string GetDisplayName(Type type)
        {
            // 通过反射查找 LabelTextAttribute (Odin)
            var labelAttr = FindAttribute(type, "LabelTextAttribute");
            if (labelAttr != null)
            {
                var textProp = labelAttr.GetType().GetProperty("Text");
                if (textProp != null)
                {
                    return textProp.GetValue(labelAttr) as string;
                }
            }
            return null;
        }

        private static string GetCategory(Type type)
        {
            // 从命名空间推断分类
            if (type.Namespace != null)
            {
                if (type.Namespace.Contains("Effects"))
                    return "Effect";
                if (type.Namespace.Contains("Triggers"))
                    return "Trigger";
            }
            return "General";
        }

        private static List<BuffParameterInfo> ExtractParameters(Type type, Type baseType)
        {
            var parameters = new List<BuffParameterInfo>();

            var fields = type.GetFields(BindingFlags.Public | BindingFlags.Instance);
            foreach (var field in fields)
            {
                // 跳过基类/接口定义的字段（通过检查声明类型是否为baseType或其基类）
                if (IsBaseTypeField(field.DeclaringType, baseType))
                    continue;

                var param = new BuffParameterInfo
                {
                    name = field.Name,
                    type = GetTypeName(field.FieldType),
                    isArray = field.FieldType.IsArray,
                    isEnum = field.FieldType.IsEnum,
                    label = GetFieldLabel(field),
                    group = GetFieldGroup(field),
                    infoBox = GetFieldInfoBox(field),
                    defaultValue = GetDefaultValue(type, field)
                };

                if (field.FieldType.IsEnum)
                {
                    param.enumValues = Enum.GetNames(field.FieldType).ToList();
                }

                parameters.Add(param);
            }

            return parameters;
        }

        /// <summary>
        /// 检查类型是否是基类类型（用于跳过基类字段）
        /// </summary>
        private static bool IsBaseTypeField(Type declaringType, Type baseType)
        {
            if (declaringType == null) return false;

            // 如果声明类型是接口或基类本身，跳过
            if (baseType.IsAssignableFrom(declaringType) && declaringType != baseType)
            {
                // 检查是否是直接实现类（而非基类）
                // 如果声明类型实现了baseType，说明是具体类的字段，不应跳过
                return false;
            }

            // 通过名称匹配判断是否是常见基类
            string typeName = declaringType.Name;
            if (typeName.Contains("Base") || typeName.StartsWith("I"))
            {
                return true;
            }

            return false;
        }

        private static string GetTypeName(Type type)
        {
            if (type.IsArray)
                return type.GetElementType().Name + "[]";
            if (type.IsGenericType)
                return type.Name.Split('`')[0] + "<" + string.Join(", ", type.GetGenericArguments().Select(t => t.Name)) + ">";
            return type.Name;
        }

        private static string GetFieldLabel(FieldInfo field)
        {
            var attr = FindAttribute(field, "LabelTextAttribute");
            if (attr != null)
            {
                var textProp = attr.GetType().GetProperty("Text");
                if (textProp != null)
                {
                    return textProp.GetValue(attr) as string ?? field.Name;
                }
            }
            return field.Name;
        }

        private static string GetFieldGroup(FieldInfo field)
        {
            var attr = FindAttribute(field, "BoxGroupAttribute");
            if (attr != null)
            {
                var groupProp = attr.GetType().GetProperty("GroupName");
                if (groupProp != null)
                {
                    return groupProp.GetValue(attr) as string ?? "";
                }
            }
            return "";
        }

        private static string GetFieldInfoBox(FieldInfo field)
        {
            var attr = FindAttribute(field, "InfoBoxAttribute");
            if (attr != null)
            {
                var msgProp = attr.GetType().GetProperty("Message");
                if (msgProp != null)
                {
                    return msgProp.GetValue(attr) as string ?? "";
                }
            }
            return "";
        }

        /// <summary>
        /// 通过名称查找特性（避免直接依赖Odin类型）
        /// </summary>
        private static Attribute FindAttribute(MemberInfo member, string attributeName)
        {
            try
            {
                var attrs = member.GetCustomAttributes(true);
                foreach (var attr in attrs)
                {
                    if (attr.GetType().Name == attributeName)
                        return attr as Attribute;
                }
            }
            catch { }
            return null;
        }

        /// <summary>
        /// 通过名称查找类型上的特性
        /// </summary>
        private static Attribute FindAttribute(Type type, string attributeName)
        {
            try
            {
                var attrs = type.GetCustomAttributes(true);
                foreach (var attr in attrs)
                {
                    if (attr.GetType().Name == attributeName)
                        return attr as Attribute;
                }
            }
            catch { }
            return null;
        }

        private static string GetDefaultValue(Type type, FieldInfo field)
        {
            try
            {
                var instance = Activator.CreateInstance(type);
                var value = field.GetValue(instance);
                if (value == null) return "null";
                if (value is string str) return str;
                if (value is bool b) return b.ToString().ToLower();
                if (value.GetType().IsEnum) return value.ToString();
                return value.ToString();
            }
            catch
            {
                return "";
            }
        }
    }

    #region Data Models

    [Serializable]
    public class BuffEffectEntry
    {
        public string typeName;
        public string fullTypeName;
        public string namespaceName;
        public string assemblyName;
        public string displayName;
        public string description;
        public string category;
        public List<BuffParameterInfo> parameters;

        // UI state (not serialized)
        [NonSerialized] public bool isSelected;

        // AI generation metadata
        public bool isAIGenerated;
        public string aiGeneratedTime;
    }

    [Serializable]
    public class BuffTriggerEntry
    {
        public string typeName;
        public string fullTypeName;
        public string namespaceName;
        public string assemblyName;
        public string displayName;
        public string description;
        public string category;
        public List<BuffParameterInfo> parameters;

        // UI state (not serialized)
        [NonSerialized] public bool isSelected;

        // AI generation metadata
        public bool isAIGenerated;
        public string aiGeneratedTime;
    }

    [Serializable]
    public class BuffParameterInfo
    {
        public string name;
        public string type;
        public string label;
        public string group;
        public string infoBox;
        public string defaultValue;
        public string description;
        public bool isArray;
        public bool isEnum;
        public List<string> enumValues;
    }

    #endregion
}
