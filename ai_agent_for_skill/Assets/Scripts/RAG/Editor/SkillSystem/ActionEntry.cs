using System;
using System.Collections.Generic;

namespace RAG
{
    /// <summary>
    /// Represents an action entry with its metadata and description information
    /// </summary>
    [Serializable]
    public class ActionEntry
    {
        public bool isSelected;
        public string typeName;
        public string namespaceName;
        public string fullTypeName;
        public string displayName;
        public string category;
        public string description;
        public string searchKeywords;
        public bool isAIGenerated;
        public string aiGeneratedTime;
        public Dictionary<string, string> parameterDescriptions = new Dictionary<string, string>();
        
        // Parameter list for display in the editor window
        public List<ActionParameterInfo> parameters = new List<ActionParameterInfo>();
    }
}
