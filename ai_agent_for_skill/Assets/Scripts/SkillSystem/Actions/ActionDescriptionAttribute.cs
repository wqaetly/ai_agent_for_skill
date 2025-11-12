using System;

namespace SkillSystem.Actions
{
    /// <summary>
    /// Action功能描述特�?
    /// 用于为Action类提供详细的功能描述，支持RAG语义搜索
    /// </summary>
    [AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
    public class ActionDescriptionAttribute : Attribute
    {
        /// <summary>
        /// 功能描述文本（支持中英文，用于语义搜索）
        /// </summary>
        public string Description { get; }

        public ActionDescriptionAttribute(string description)
        {
            Description = description;
        }
    }
}
