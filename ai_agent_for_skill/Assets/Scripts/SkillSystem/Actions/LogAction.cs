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

        public override void OnEnter()
        {
            Debug.unityLogger.Log(logType, $"[OnEnter] {message}");
        }

        public override void OnTick(int relativeFrame)
        {
            // Log actions typically only execute on enter, but can provide tick feedback
            if (relativeFrame % 10 == 0) // Log every 10 frames during duration
            {
                Debug.unityLogger.Log(LogType.Log, $"[OnTick] {message} (Frame: {relativeFrame})");
            }
        }

        public override void OnExit()
        {
            Debug.unityLogger.Log(LogType.Log, $"[OnExit] {message} - Action completed");
        }

    }
}