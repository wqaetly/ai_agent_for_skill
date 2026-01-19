using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using RAGBuilder;
using UnityEngine;

namespace RAGBuilder.Samples
{
    /// <summary>
    /// Sample implementation of IActionInfo.
    /// This shows how to wrap your action types to work with RAG Builder.
    /// </summary>
    public class SampleActionInfo : IActionInfo
    {
        private readonly Type actionType;
        private readonly string description;
        private readonly List<SampleParameterInfo> parameters;

        public string TypeName => actionType.Name;
        public string DisplayName { get; private set; }
        public string Category { get; private set; }
        public string Description => description;
        public string SearchText => $"{TypeName} {DisplayName} {Description} {Category}";
        public IReadOnlyList<IActionParameterInfo> Parameters => parameters;

        public SampleActionInfo(Type actionType, string displayName, string category, string description)
        {
            this.actionType = actionType;
            this.DisplayName = displayName;
            this.Category = category;
            this.description = description;
            this.parameters = new List<SampleParameterInfo>();

            // Extract parameters from type
            ExtractParameters();
        }

        private void ExtractParameters()
        {
            var fields = actionType.GetFields(BindingFlags.Public | BindingFlags.Instance);
            foreach (var field in fields)
            {
                // Skip inherited fields from base class
                if (field.DeclaringType != actionType) continue;

                var paramInfo = new SampleParameterInfo
                {
                    Name = field.Name,
                    Type = field.FieldType.Name,
                    Label = field.Name,
                    IsArray = field.FieldType.IsArray,
                    IsEnum = field.FieldType.IsEnum
                };

                if (paramInfo.IsEnum)
                {
                    paramInfo.SetEnumValues(Enum.GetNames(field.FieldType).ToList());
                }

                parameters.Add(paramInfo);
            }
        }
    }

    /// <summary>
    /// Sample implementation of IActionParameterInfo
    /// </summary>
    public class SampleParameterInfo : IActionParameterInfo
    {
        public string Name { get; set; }
        public string Type { get; set; }
        public string DefaultValue { get; set; }
        public string Label { get; set; }
        public string Description { get; set; }
        public bool IsArray { get; set; }
        public bool IsEnum { get; set; }
        public float? MinValue { get; set; }
        public float? MaxValue { get; set; }

        private List<string> enumValues = new List<string>();
        public IReadOnlyList<string> EnumValues => enumValues;

        public void SetEnumValues(List<string> values)
        {
            enumValues = values;
        }
    }

    /// <summary>
    /// Sample implementation of ISkillInfo
    /// </summary>
    public class SampleSkillInfo : ISkillInfo
    {
        public string SkillId { get; set; }
        public string SkillName { get; set; }
        public string Description { get; set; }
        public int TotalDuration { get; set; }
        public int FrameRate { get; set; }

        private List<SampleActionInstance> actions = new List<SampleActionInstance>();
        private List<string> tags = new List<string>();

        public IReadOnlyList<ISkillActionInstance> Actions => actions;
        public IReadOnlyList<string> Tags => tags;

        public void AddAction(SampleActionInstance action)
        {
            actions.Add(action);
        }

        public void AddTag(string tag)
        {
            if (!tags.Contains(tag))
            {
                tags.Add(tag);
            }
        }
    }

    /// <summary>
    /// Sample implementation of ISkillActionInstance
    /// </summary>
    public class SampleActionInstance : ISkillActionInstance
    {
        public string ActionType { get; set; }
        public int Frame { get; set; }
        public int Duration { get; set; }
        public string TrackName { get; set; }

        private Dictionary<string, object> parameters = new Dictionary<string, object>();
        public IReadOnlyDictionary<string, object> Parameters => parameters;

        public void SetParameter(string name, object value)
        {
            parameters[name] = value;
        }
    }
}
