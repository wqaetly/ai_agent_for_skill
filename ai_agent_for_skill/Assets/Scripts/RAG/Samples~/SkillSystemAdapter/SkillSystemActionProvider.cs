using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using RAGBuilder;
using SkillSystem.Actions;
using SkillSystem.Data;
using UnityEngine;

namespace SkillSystem.RAG.Adapters
{
    /// <summary>
    /// Adapter to integrate existing SkillSystem with RAG Builder package.
    /// This adapter wraps the existing action types to work with RAG Builder interfaces.
    /// </summary>
    public class SkillSystemActionProvider : IActionProvider
    {
        private Dictionary<string, SkillActionInfoAdapter> actionCache = new Dictionary<string, SkillActionInfoAdapter>();
        private IDescriptionStorage descriptionStorage;

        public SkillSystemActionProvider(IDescriptionStorage descriptionStorage = null)
        {
            this.descriptionStorage = descriptionStorage;
            ScanActions();
        }

        private void ScanActions()
        {
            actionCache.Clear();

            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (var assembly in assemblies)
            {
                try
                {
                    var types = assembly.GetTypes()
                        .Where(t => !t.IsAbstract && typeof(ISkillAction).IsAssignableFrom(t) && t != typeof(ISkillAction));

                    foreach (var type in types)
                    {
                        try
                        {
                            string description = "";
                            if (descriptionStorage != null)
                            {
                                description = descriptionStorage.GetDescription(type.Name);
                            }

                            var adapter = new SkillActionInfoAdapter(type, description);
                            actionCache[type.Name] = adapter;
                        }
                        catch (Exception e)
                        {
                            Debug.LogWarning($"[SkillSystemActionProvider] Failed to create adapter for {type.Name}: {e.Message}");
                        }
                    }
                }
                catch (Exception)
                {
                    // Skip assemblies that can't be loaded
                }
            }

            Debug.Log($"[SkillSystemActionProvider] Scanned {actionCache.Count} action types");
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

        public void Refresh()
        {
            ScanActions();
        }
    }

    /// <summary>
    /// Adapter that wraps ISkillAction types to implement IActionInfo
    /// </summary>
    public class SkillActionInfoAdapter : IActionInfo
    {
        private readonly Type actionType;
        private readonly string description;
        private readonly List<SkillActionParameterAdapter> parameters;

        public string TypeName => actionType.Name;
        public string DisplayName { get; private set; }
        public string Category { get; private set; }
        public string Description => description;
        public string SearchText => $"{TypeName} {DisplayName} {Description} {Category}";
        public IReadOnlyList<IActionParameterInfo> Parameters => parameters;

        public SkillActionInfoAdapter(Type actionType, string description)
        {
            this.actionType = actionType;
            this.description = description;
            this.parameters = new List<SkillActionParameterAdapter>();

            // Get display name from attribute or type name
            var displayAttr = actionType.GetCustomAttribute<ActionDisplayNameAttribute>();
            DisplayName = displayAttr?.DisplayName ?? GetDefaultDisplayName(actionType.Name);

            // Get category
            Category = GetCategory(actionType.Name);

            // Extract parameters
            ExtractParameters();
        }

        private string GetDefaultDisplayName(string typeName)
        {
            // Remove "Action" suffix and add spaces before capitals
            string name = typeName;
            if (name.EndsWith("Action"))
            {
                name = name.Substring(0, name.Length - 6);
            }
            return name;
        }

        private string GetCategory(string typeName)
        {
            if (typeName.Contains("Damage")) return "Damage";
            if (typeName.Contains("Heal")) return "Heal";
            if (typeName.Contains("Movement") || typeName.Contains("Teleport")) return "Movement";
            if (typeName.Contains("Shield")) return "Defense";
            if (typeName.Contains("Control")) return "Control";
            if (typeName.Contains("Buff")) return "Buff";
            if (typeName.Contains("Animation")) return "Visual";
            if (typeName.Contains("Audio")) return "Audio";
            if (typeName.Contains("Projectile")) return "Projectile";
            if (typeName.Contains("Area") || typeName.Contains("AOE")) return "Area";
            if (typeName.Contains("Summon")) return "Summon";
            if (typeName.Contains("Resource")) return "Resource";
            return "Other";
        }

        private void ExtractParameters()
        {
            var fields = actionType.GetFields(BindingFlags.Public | BindingFlags.Instance);
            
            foreach (var field in fields)
            {
                // Skip inherited base fields
                if (field.DeclaringType == typeof(ISkillAction)) continue;

                var param = new SkillActionParameterAdapter(field);
                parameters.Add(param);
            }
        }
    }

    /// <summary>
    /// Adapter that wraps FieldInfo to implement IActionParameterInfo
    /// </summary>
    public class SkillActionParameterAdapter : IActionParameterInfo
    {
        private readonly FieldInfo field;
        private List<string> enumValues;

        public string Name => field.Name;
        public string Type => field.FieldType.Name;
        public string DefaultValue { get; private set; }
        public string Label { get; private set; }
        public string Description { get; private set; }
        public bool IsArray => field.FieldType.IsArray;
        public bool IsEnum => field.FieldType.IsEnum;
        public IReadOnlyList<string> EnumValues => enumValues;
        public float? MinValue { get; private set; }
        public float? MaxValue { get; private set; }

        public SkillActionParameterAdapter(FieldInfo field)
        {
            this.field = field;
            this.enumValues = new List<string>();

            // Get label from attribute or field name
            var labelAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == "LabelTextAttribute");
            if (labelAttr != null)
            {
                var textProp = labelAttr.GetType().GetProperty("Text");
                Label = textProp?.GetValue(labelAttr)?.ToString() ?? field.Name;
            }
            else
            {
                Label = field.Name;
            }

            Description = Label;

            // Get enum values if enum type
            if (IsEnum)
            {
                enumValues = Enum.GetNames(field.FieldType).ToList();
            }

            // Try to get min/max from attributes
            var minAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == "MinValueAttribute");
            if (minAttr != null)
            {
                var valueProp = minAttr.GetType().GetProperty("MinValue");
                if (valueProp != null)
                {
                    var value = valueProp.GetValue(minAttr);
                    if (value != null && float.TryParse(value.ToString(), out float min))
                    {
                        MinValue = min;
                    }
                }
            }

            var maxAttr = field.GetCustomAttributes()
                .FirstOrDefault(a => a.GetType().Name == "MaxValueAttribute");
            if (maxAttr != null)
            {
                var valueProp = maxAttr.GetType().GetProperty("MaxValue");
                if (valueProp != null)
                {
                    var value = valueProp.GetValue(maxAttr);
                    if (value != null && float.TryParse(value.ToString(), out float max))
                    {
                        MaxValue = max;
                    }
                }
            }

            // Get default value
            try
            {
                var instance = Activator.CreateInstance(field.DeclaringType);
                var defaultVal = field.GetValue(instance);
                DefaultValue = defaultVal?.ToString() ?? "";
            }
            catch
            {
                DefaultValue = "";
            }
        }
    }
}
