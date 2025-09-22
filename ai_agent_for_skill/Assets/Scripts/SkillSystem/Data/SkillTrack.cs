using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;
using SkillSystem.Actions;

namespace SkillSystem.Data
{
    [Serializable]
    public class SkillTrack
    {
        [SerializeField]
        [LabelText("Track Name")]
        public string trackName = "New Track";


        [SerializeField]
        [LabelText("Enabled")]
        public bool enabled = true;

        [SerializeReference]
        [LabelText("Actions")]
        [ListDrawerSettings(ShowIndexLabels = true, ListElementLabelName = "GetActionDisplayName")]
        public List<ISkillAction> actions = new List<ISkillAction>();

        public void AddAction(ISkillAction action)
        {
            if (action != null)
            {
                actions.Add(action);
                SortActionsByFrame();
            }
        }

        public void RemoveAction(ISkillAction action)
        {
            if (actions.Contains(action))
            {
                actions.Remove(action);
            }
        }

        public void SortActionsByFrame()
        {
            actions.Sort((a, b) => a.frame.CompareTo(b.frame));
        }

        public List<ISkillAction> GetActionsAtFrame(int frame)
        {
            var result = new List<ISkillAction>();
            foreach (var action in actions)
            {
                if (action.IsActiveAtFrame(frame))
                {
                    result.Add(action);
                }
            }
            return result;
        }

        private string GetActionDisplayName(ISkillAction action, int index)
        {
            if (action == null) return $"Action {index}";
            return $"{action.GetActionName()} (Frame {action.frame})";
        }
    }
}