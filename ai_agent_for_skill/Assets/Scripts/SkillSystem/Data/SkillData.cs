using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;
using Sirenix.Serialization;

namespace SkillSystem.Data
{
    [Serializable]
    public class SkillData : SerializedScriptableObject
    {
        [SerializeField]
        [LabelText("Skill Name")]
        public string skillName = "New Skill";

        [SerializeField]
        [LabelText("Skill Description")]
        [MultiLineProperty(3)]
        public string skillDescription = "";

        [SerializeField]
        [LabelText("Total Duration (Frames)")]
        [MinValue(1)]
        public int totalDuration = 60;

        [SerializeField]
        [LabelText("Frame Rate")]
        [MinValue(1)]
        public int frameRate = 30;

        [OdinSerialize]
        [LabelText("Tracks")]
        [ListDrawerSettings(ShowIndexLabels = true, ListElementLabelName = "trackName")]
        public List<SkillTrack> tracks = new List<SkillTrack>();

        [SerializeField]
        [LabelText("Skill ID")]
        [ReadOnly]
        public string skillId = System.Guid.NewGuid().ToString();

        public float GetDurationInSeconds()
        {
            return (float)totalDuration / frameRate;
        }

        public void AddTrack(SkillTrack track)
        {
            if (track != null)
            {
                tracks.Add(track);
            }
        }

        public void RemoveTrack(SkillTrack track)
        {
            if (tracks.Contains(track))
            {
                tracks.Remove(track);
            }
        }

        public List<SkillTrack> GetEnabledTracks()
        {
            var result = new List<SkillTrack>();
            foreach (var track in tracks)
            {
                if (track.enabled)
                {
                    result.Add(track);
                }
            }
            return result;
        }

        [Button("Generate New ID")]
        private void GenerateNewId()
        {
            skillId = System.Guid.NewGuid().ToString();
        }

        [Button("Validate Skill Data")]
        private void ValidateSkillData()
        {
            bool hasErrors = false;

            if (string.IsNullOrEmpty(skillName))
            {
                Debug.LogError("Skill name cannot be empty!");
                hasErrors = true;
            }

            if (totalDuration <= 0)
            {
                Debug.LogError("Total duration must be greater than 0!");
                hasErrors = true;
            }

            foreach (var track in tracks)
            {
                if (track.actions != null)
                {
                    foreach (var action in track.actions)
                    {
                        if (action.frame >= totalDuration)
                        {
                            Debug.LogWarning($"Action in track '{track.trackName}' starts at frame {action.frame} but skill only lasts {totalDuration} frames!");
                        }
                    }
                }
            }

            if (!hasErrors)
            {
                Debug.Log("Skill data validation passed!");
            }
        }
    }
}