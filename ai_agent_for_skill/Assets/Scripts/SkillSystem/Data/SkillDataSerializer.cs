using System.IO;
using UnityEngine;
using Sirenix.Serialization;
using SkillSystem.Data;
using UnityEditor;
using SerializationUtility = Sirenix.Serialization.SerializationUtility;

namespace SkillSystem.Data
{
    public static class SkillDataSerializer
    {
        private static readonly DataFormat dataFormat = DataFormat.JSON;

        public static string SerializeToJson(SkillData skillData)
        {
            if (skillData == null)
            {
                Debug.LogError("Cannot serialize null SkillData!");
                return string.Empty;
            }

            try
            {
                byte[] bytes = SerializationUtility.SerializeValue(skillData, dataFormat);
                return System.Text.Encoding.UTF8.GetString(bytes);
            }
            catch (System.Exception e)
            {
                Debug.LogError($"Failed to serialize SkillData: {e.Message}");
                return string.Empty;
            }
        }

        public static SkillData DeserializeFromJson(string json)
        {
            if (string.IsNullOrEmpty(json))
            {
                Debug.LogError("Cannot deserialize empty or null JSON string!");
                return null;
            }

            try
            {
                byte[] bytes = System.Text.Encoding.UTF8.GetBytes(json);
                return SerializationUtility.DeserializeValue<SkillData>(bytes, dataFormat);
            }
            catch (System.Exception e)
            {
                Debug.LogError($"Failed to deserialize SkillData: {e.Message}");
                return null;
            }
        }

        public static bool SaveToFile(SkillData skillData, string filePath)
        {
            if (skillData == null)
            {
                Debug.LogError("Cannot save null SkillData!");
                return false;
            }

            try
            {
                string json = SerializeToJson(skillData);
                if (string.IsNullOrEmpty(json))
                {
                    return false;
                }

                string directory = Path.GetDirectoryName(filePath);
                if (!Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                File.WriteAllText(filePath, json);
                Debug.Log($"SkillData saved to: {filePath}");
                
                AssetDatabase.Refresh();
                return true;
            }
            catch (System.Exception e)
            {
                Debug.LogError($"Failed to save SkillData to file: {e.Message}");
                return false;
            }
        }

        public static SkillData LoadFromFile(string filePath)
        {
            if (!File.Exists(filePath))
            {
                Debug.LogError($"File not found: {filePath}");
                return null;
            }

            try
            {
                string json = File.ReadAllText(filePath);
                SkillData skillData = DeserializeFromJson(json);

                if (skillData != null)
                {
                    Debug.Log($"SkillData loaded from: {filePath}");
                }

                return skillData;
            }
            catch (System.Exception e)
            {
                Debug.LogError($"Failed to load SkillData from file: {e.Message}");
                return null;
            }
        }

        public static string GetDefaultSkillPath()
        {
            return Path.Combine(Application.dataPath, "Skills");
        }

        public static string GetSkillFilePath(string skillName)
        {
            string fileName = $"{skillName}.json";
            return Path.Combine(GetDefaultSkillPath(), fileName);
        }
    }
}