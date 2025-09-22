using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    [Serializable]
    public class LogAction : ISkillAction
    {
        [SerializeField]
        [LabelText("Log Message")]
        [MultiLineProperty(3)]
        public string message = "Skill Action Executed";

        [SerializeField]
        [LabelText("Log Type")]
        public LogType logType = LogType.Log;

        public override string GetActionName()
        {
            return "Log Action";
        }

        public override void Execute()
        {
            Debug.unityLogger.Log(logType, message);
        }

    }
}