using System;
using System.Collections.Generic;

namespace RAG
{
    /// <summary>
    /// Action导出JSON文件的根对象
    /// </summary>
    [Serializable]
    public class ActionFile
    {
        public string version;
        public string exportTime;
        public ActionDefinition action;
    }

    /// <summary>
    /// Action定义数据
    /// </summary>
    [Serializable]
    public class ActionDefinition
    {
        public string typeName;
        public string fullTypeName;
        public string namespaceName;
        public string assemblyName;
        public string displayName;
        public string category;
        public string description;
        public string searchText;
        public List<ActionParameterInfo> parameters;
    }

    /// <summary>
    /// Action参数信息
    /// </summary>
    [Serializable]
    public class ActionParameterInfo
    {
        public string name;
        public string type;
        public string defaultValue;
        public string label;
        public string description;  // AI generated parameter description
        public string group;
        public string infoBox;
        public bool isArray;
        public bool isEnum;
        public string elementType;
        public List<string> enumValues;
        public ParameterConstraints constraints;

        public ActionParameterInfo()
        {
            constraints = new ParameterConstraints();
            enumValues = new List<string>();
        }
    }

    /// <summary>
    /// 参数约束信息
    /// </summary>
    [Serializable]
    public class ParameterConstraints
    {
        public string minValue;
        public string maxValue;
        public string min;
        public string max;
    }
}
