using System;

namespace SkillSystem.Actions
{
    /// <summary>
    /// Action显示名称特�?
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
    /// Action类别特�?
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