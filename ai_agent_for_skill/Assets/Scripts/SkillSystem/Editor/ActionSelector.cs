using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;
using SkillSystem.Actions;
using Sirenix.OdinInspector.Editor;

namespace SkillSystem.Editor
{
    /// <summary>
    /// Action选择�?- 基于反射的动态Action类型发现和选择
    /// 职责：自动发现所有ISkillAction实现类，提供可扩展的选择UI
    /// </summary>
    public static class ActionSelector
    {
        // 缓存所有发现的Action类型
        private static Dictionary<string, Type> cachedActionTypes = null;

        /// <summary>
        /// 获取所有可用的Action类型
        /// </summary>
        public static Dictionary<string, Type> GetAllActionTypes()
        {
            if (cachedActionTypes == null)
            {
                RefreshActionTypes();
            }
            return new Dictionary<string, Type>(cachedActionTypes);
        }

        /// <summary>
        /// 刷新Action类型缓存
        /// </summary>
        public static void RefreshActionTypes()
        {
            cachedActionTypes = new Dictionary<string, Type>();

            // 获取所有程序集
            var assemblies = System.AppDomain.CurrentDomain.GetAssemblies();

            foreach (var assembly in assemblies)
            {
                try
                {
                    // 查找所有继承自ISkillAction的类�?
                    var actionTypes = assembly.GetTypes()
                        .Where(t => t.IsSubclassOf(typeof(ISkillAction)) &&
                                   !t.IsAbstract &&
                                   t.IsPublic)
                        .ToList();

                    foreach (var actionType in actionTypes)
                    {
                        // 获取Action显示名称
                        string displayName = GetActionDisplayName(actionType);

                        // 避免重名冲突
                        if (!cachedActionTypes.ContainsKey(displayName))
                        {
                            cachedActionTypes[displayName] = actionType;
                        }
                        else
                        {
                            // 如果有重名，使用完整类名
                            string fullName = $"{actionType.Name} ({actionType.Namespace})";
                            cachedActionTypes[fullName] = actionType;
                        }
                    }
                }
                catch (ReflectionTypeLoadException ex)
                {
                    // 跳过加载失败的程序集
                    UnityEngine.Debug.LogWarning($"Failed to load types from assembly {assembly.FullName}: {ex.Message}");
                }
                catch (Exception ex)
                {
                    // 跳过其他异常
                    UnityEngine.Debug.LogWarning($"Error processing assembly {assembly.FullName}: {ex.Message}");
                }
            }
        }

        /// <summary>
        /// 获取Action的显示名�?
        /// </summary>
        private static string GetActionDisplayName(Type actionType)
        {
            // 优先使用类上的特性定义的名称
            var displayNameAttribute = actionType.GetCustomAttribute<ActionDisplayNameAttribute>();
            if (displayNameAttribute != null)
            {
                return displayNameAttribute.DisplayName;
            }

            // 移除"Action"后缀，使名称更清�?
            string name = actionType.Name;
            if (name.EndsWith("Action"))
            {
                name = name.Substring(0, name.Length - 6);
            }

            // 添加空格分隔驼峰命名
            return AddSpacesToPascalCase(name);
        }

        /// <summary>
        /// 为驼峰命名添加空�?
        /// </summary>
        private static string AddSpacesToPascalCase(string text)
        {
            if (string.IsNullOrEmpty(text))
                return text;

            var result = new System.Text.StringBuilder();
            result.Append(text[0]);

            for (int i = 1; i < text.Length; i++)
            {
                if (char.IsUpper(text[i]) && char.IsLower(text[i - 1]))
                {
                    result.Append(' ');
                }
                result.Append(text[i]);
            }

            return result.ToString();
        }

        /// <summary>
        /// 创建Action实例
        /// </summary>
        public static ISkillAction CreateActionInstance(Type actionType)
        {
            try
            {
                return (ISkillAction)Activator.CreateInstance(actionType);
            }
            catch (Exception ex)
            {
                UnityEngine.Debug.LogError($"Failed to create instance of {actionType.Name}: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 创建Action实例
        /// </summary>
        public static T CreateActionInstance<T>() where T : ISkillAction, new()
        {
            return new T();
        }

        /// <summary>
        /// 按类别分组Action类型
        /// </summary>
        public static Dictionary<string, List<Type>> GetActionTypesByCategory()
        {
            var actionTypes = GetAllActionTypes();
            var categorized = new Dictionary<string, List<Type>>();

            foreach (var kvp in actionTypes)
            {
                var actionType = kvp.Value;
                string category = GetActionCategory(actionType);

                if (!categorized.ContainsKey(category))
                {
                    categorized[category] = new List<Type>();
                }

                categorized[category].Add(actionType);
            }

            // 按类别名称排�?
            var sortedCategories = new Dictionary<string, List<Type>>();
            foreach (var category in categorized.Keys.OrderBy(k => k))
            {
                // 按Action名称排序
                categorized[category].Sort((a, b) => GetActionDisplayName(a).CompareTo(GetActionDisplayName(b)));
                sortedCategories[category] = categorized[category];
            }

            return sortedCategories;
        }

        /// <summary>
        /// 获取Action类别
        /// </summary>
        private static string GetActionCategory(Type actionType)
        {
            // 优先使用类上的特性定义的类别
            var categoryAttribute = actionType.GetCustomAttribute<ActionCategoryAttribute>();
            if (categoryAttribute != null)
            {
                return categoryAttribute.Category;
            }

            // 根据名称推断类别
            string name = actionType.Name.ToLower();

            if (name.Contains("damage") || name.Contains("attack") || name.Contains("projectile"))
                return "Combat";
            if (name.Contains("heal") || name.Contains("buff") || name.Contains("shield"))
                return "Support";
            if (name.Contains("movement") || name.Contains("teleport"))
                return "Movement";
            if (name.Contains("animation") || name.Contains("camera") || name.Contains("audio"))
                return "Visual & Audio";
            if (name.Contains("collision") || name.Contains("area"))
                return "Detection";
            if (name.Contains("resource") || name.Contains("control"))
                return "System";
            if (name.Contains("summon") || name.Contains("spawn"))
                return "Summoning";

            return "General";
        }
    }

}