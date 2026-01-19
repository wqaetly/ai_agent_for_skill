using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using RAGBuilder;
using UnityEngine;

namespace RAGBuilder.Samples
{
    /// <summary>
    /// Sample Action Provider implementation.
    /// Shows how to scan and provide action types from your project.
    /// </summary>
    public class SampleActionProvider : IActionProvider
    {
        private Dictionary<string, IActionInfo> actionCache = new Dictionary<string, IActionInfo>();
        private Type baseActionType;
        private IDescriptionStorage descriptionStorage;

        /// <summary>
        /// Create provider with base action type to scan for
        /// </summary>
        /// <param name="baseActionType">Base class/interface that all actions inherit from</param>
        /// <param name="descriptionStorage">Optional storage for action descriptions</param>
        public SampleActionProvider(Type baseActionType, IDescriptionStorage descriptionStorage = null)
        {
            this.baseActionType = baseActionType;
            this.descriptionStorage = descriptionStorage;
            ScanActions();
        }

        /// <summary>
        /// Scan all action types in the project
        /// </summary>
        private void ScanActions()
        {
            actionCache.Clear();

            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (var assembly in assemblies)
            {
                try
                {
                    var types = assembly.GetTypes()
                        .Where(t => !t.IsAbstract && baseActionType.IsAssignableFrom(t) && t != baseActionType);

                    foreach (var type in types)
                    {
                        var actionInfo = CreateActionInfo(type);
                        if (actionInfo != null)
                        {
                            actionCache[type.Name] = actionInfo;
                        }
                    }
                }
                catch (Exception)
                {
                    // Skip assemblies that can't be loaded
                }
            }

            Debug.Log($"[SampleActionProvider] Scanned {actionCache.Count} action types");
        }

        private IActionInfo CreateActionInfo(Type type)
        {
            // Get display name from attribute or generate from type name
            string displayName = GetDisplayName(type);
            
            // Get category from attribute or infer from type name
            string category = GetCategory(type);
            
            // Get description from storage or generate default
            string description = "";
            if (descriptionStorage != null)
            {
                description = descriptionStorage.GetDescription(type.Name);
            }
            
            if (string.IsNullOrEmpty(description))
            {
                description = $"Performs {displayName} action";
            }

            return new SampleActionInfo(type, displayName, category, description);
        }

        private string GetDisplayName(Type type)
        {
            // Try to get from custom attribute
            var attr = type.GetCustomAttribute<ActionDisplayNameAttribute>();
            if (attr != null)
            {
                return attr.DisplayName;
            }

            // Generate from type name (remove "Action" suffix)
            string name = type.Name;
            if (name.EndsWith("Action"))
            {
                name = name.Substring(0, name.Length - 6);
            }
            return name;
        }

        private string GetCategory(Type type)
        {
            // Try to get from custom attribute
            var attr = type.GetCustomAttribute<ActionCategoryAttribute>();
            if (attr != null)
            {
                return attr.Category;
            }

            // Infer from type name
            string name = type.Name;
            if (name.Contains("Damage")) return "Damage";
            if (name.Contains("Heal")) return "Heal";
            if (name.Contains("Movement") || name.Contains("Teleport")) return "Movement";
            if (name.Contains("Shield")) return "Defense";
            if (name.Contains("Control")) return "Control";
            if (name.Contains("Buff")) return "Buff";
            if (name.Contains("Animation")) return "Visual";
            if (name.Contains("Audio")) return "Audio";

            return "Other";
        }

        public IEnumerable<IActionInfo> GetAllActions()
        {
            return actionCache.Values;
        }

        public IActionInfo GetAction(string typeName)
        {
            return actionCache.TryGetValue(typeName, out var info) ? info : null;
        }

        public bool HasAction(string typeName)
        {
            return actionCache.ContainsKey(typeName);
        }

        /// <summary>
        /// Force rescan of action types
        /// </summary>
        public void Refresh()
        {
            ScanActions();
        }
    }

    /// <summary>
    /// Custom attribute for action display name
    /// </summary>
    [AttributeUsage(AttributeTargets.Class)]
    public class ActionDisplayNameAttribute : Attribute
    {
        public string DisplayName { get; }

        public ActionDisplayNameAttribute(string displayName)
        {
            DisplayName = displayName;
        }
    }

    /// <summary>
    /// Custom attribute for action category
    /// </summary>
    [AttributeUsage(AttributeTargets.Class)]
    public class ActionCategoryAttribute : Attribute
    {
        public string Category { get; }

        public ActionCategoryAttribute(string category)
        {
            Category = category;
        }
    }
}
