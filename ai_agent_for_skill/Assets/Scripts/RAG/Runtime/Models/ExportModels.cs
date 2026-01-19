using System;
using System.Collections.Generic;

namespace RAG
{
    /// <summary>
    /// Action export JSON file root object
    /// </summary>
    [Serializable]
    public class ActionExportData
    {
        public string version;
        public string exportTime;
        public ActionDefinitionData action;
    }

    /// <summary>
    /// Action definition data for export
    /// </summary>
    [Serializable]
    public class ActionDefinitionData
    {
        public string typeName;
        public string fullTypeName;
        public string namespaceName;
        public string assemblyName;
        public string displayName;
        public string category;
        public string description;
        public string searchText;
        public List<ActionParameterData> parameters = new List<ActionParameterData>();
    }

    /// <summary>
    /// Action parameter data for export
    /// </summary>
    [Serializable]
    public class ActionParameterData
    {
        public string name;
        public string type;
        public string defaultValue;
        public string label;
        public string group;
        public string infoBox;
        public bool isArray;
        public bool isEnum;
        public string elementType;
        public List<string> enumValues = new List<string>();
        public ParameterConstraintsData constraints = new ParameterConstraintsData();
    }

    /// <summary>
    /// Parameter constraints data for export
    /// </summary>
    [Serializable]
    public class ParameterConstraintsData
    {
        public string minValue;
        public string maxValue;
        public string min;
        public string max;
    }

    /// <summary>
    /// Skill export data for export
    /// </summary>
    [Serializable]
    public class SkillExportData
    {
        public string version;
        public string exportTime;
        public string skillId;
        public string skillName;
        public string description;
        public int totalDuration;
        public int frameRate;
        public float durationInSeconds;
        public List<string> tags = new List<string>();
        public List<SkillTrackData> tracks = new List<SkillTrackData>();
        public string searchText;
    }

    /// <summary>
    /// Skill track data for export
    /// </summary>
    [Serializable]
    public class SkillTrackData
    {
        public string trackName;
        public bool enabled;
        public List<SkillActionData> actions = new List<SkillActionData>();
    }

    /// <summary>
    /// Skill action data for export
    /// </summary>
    [Serializable]
    public class SkillActionData
    {
        public string actionType;
        public string displayName;
        public int frame;
        public int duration;
        public bool enabled;
        public Dictionary<string, object> parameters = new Dictionary<string, object>();
    }
}
