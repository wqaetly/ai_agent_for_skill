using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEngine;
using UnityEditor;

namespace RAG.BuffSystem
{
    /// <summary>
    /// Buff JSON导出器 - 将Buff效果和触发器信息导出为JSON
    /// 使用配置驱动的方式，通过反射获取枚举类型，无外部类型依赖
    /// 注意：统一入口请使用 技能系统 > RAG数据导出中心
    /// </summary>
    public static class BuffJSONExporter
    {
        // 枚举类型名称配置（可在RAGConfig中配置，这里是默认值）
        private static readonly string[] DefaultEnumTypeNames = new[]
        {
            "BuffSystem.Data.BuffType",
            "BuffSystem.Data.BuffCategory",
            "BuffSystem.Data.DurationType",
            "BuffSystem.Data.StackingType",
            "BuffSystem.Data.DispelType",
            "BuffSystem.Data.TriggerEventType",
            "BuffSystem.Effects.AttributeType",
            "BuffSystem.Effects.DamageType",
            "BuffSystem.Effects.SpecialStateFlags"
        };

        /// <summary>
        /// 导出 Buff 枚举数据（配置驱动，通过反射获取枚举类型）
        /// </summary>
        public static void ExportBuffEnums()
        {
            var config = RAGConfig.Instance;
            string exportDir = config?.buffSystemConfig?.exportDirectory ?? "../skill_agent/Data/Buffs";
            string directory = Path.Combine(Application.dataPath, exportDir);
            Directory.CreateDirectory(directory);

            var enumData = new BuffEnumData
            {
                version = "1.0",
                exportTime = DateTime.Now.ToString("O"),
                buffTypes = GetEnumInfoByTypeName("BuffSystem.Data.BuffType"),
                buffCategories = GetEnumInfoByTypeName("BuffSystem.Data.BuffCategory"),
                durationTypes = GetEnumInfoByTypeName("BuffSystem.Data.DurationType"),
                stackingTypes = GetEnumInfoByTypeName("BuffSystem.Data.StackingType"),
                dispelTypes = GetEnumInfoByTypeName("BuffSystem.Data.DispelType"),
                triggerEventTypes = GetEnumInfoByTypeName("BuffSystem.Data.TriggerEventType"),
                attributeTypes = GetEnumInfoByTypeName("BuffSystem.Effects.AttributeType"),
                damageTypes = GetEnumInfoByTypeName("BuffSystem.Effects.DamageType"),
                specialStateFlags = GetEnumInfoByTypeName("BuffSystem.Effects.SpecialStateFlags")
            };

            string json = JsonUtility.ToJson(enumData, true);
            string filePath = Path.Combine(directory, "BuffEnums.json");
            File.WriteAllText(filePath, json);

            Debug.Log($"[BuffJSONExporter] Exported buff enums to {filePath}");
        }

        /// <summary>
        /// 通过类型名称获取枚举信息（配置驱动）
        /// </summary>
        private static List<EnumValueInfo> GetEnumInfoByTypeName(string enumTypeName)
        {
            var values = new List<EnumValueInfo>();

            Type enumType = FindTypeByName(enumTypeName);
            if (enumType == null || !enumType.IsEnum)
            {
                Debug.LogWarning($"[BuffJSONExporter] 未找到枚举类型: {enumTypeName}");
                return values;
            }

            foreach (var value in Enum.GetValues(enumType))
            {
                values.Add(new EnumValueInfo
                {
                    name = value.ToString(),
                    value = Convert.ToInt32(value),
                    label = GetEnumLabel(enumType, value)
                });
            }

            return values;
        }

        /// <summary>
        /// 通过反射查找类型
        /// </summary>
        private static Type FindTypeByName(string typeName)
        {
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    var type = assembly.GetType(typeName);
                    if (type != null) return type;
                }
                catch { }
            }
            return null;
        }

        /// <summary>
        /// 获取枚举值的标签（通过反射查找LabelText特性）
        /// </summary>
        private static string GetEnumLabel(Type enumType, object value)
        {
            var field = enumType.GetField(value.ToString());
            if (field == null) return value.ToString();

            // 通过反射查找 LabelTextAttribute (避免直接依赖Odin)
            var attrs = field.GetCustomAttributes(true);
            foreach (var attr in attrs)
            {
                if (attr.GetType().Name == "LabelTextAttribute")
                {
                    var textProp = attr.GetType().GetProperty("Text");
                    if (textProp != null)
                    {
                        return textProp.GetValue(attr) as string ?? value.ToString();
                    }
                }
            }

            return value.ToString();
        }

    }

    /// <summary>
    /// Buff JSON导出器实例 - 实例化的导出器，支持导出效果和触发器
    /// </summary>
    public class BuffJSONExporterInstance
    {
        private string exportDirectory;
        private Action<string> logAction;

        public BuffJSONExporterInstance(string exportDirectory, Action<string> logAction = null)
        {
            this.exportDirectory = exportDirectory;
            this.logAction = logAction;
        }

        /// <summary>
        /// 导出所有Buff效果到JSON文件
        /// </summary>
        /// <param name="entries">效果条目列表</param>
        /// <returns>(成功数, 失败数)</returns>
        public (int successCount, int failCount) ExportEffectsToJSON(List<BuffEffectEntry> entries)
        {
            int successCount = 0;
            int failCount = 0;

            try
            {
                string effectsDir = Path.Combine(Path.GetFullPath(exportDirectory), "Effects");
                if (!Directory.Exists(effectsDir))
                {
                    Directory.CreateDirectory(effectsDir);
                }

                Log($"\n[Export] Starting Buff Effects JSON export to: {effectsDir}");

                foreach (var entry in entries)
                {
                    if (ExportSingleEffect(entry, effectsDir))
                    {
                        successCount++;
                    }
                    else
                    {
                        failCount++;
                    }
                }

                Log($"[Export] Complete - Success: {successCount}, Failed: {failCount}");
            }
            catch (Exception e)
            {
                Log($"[Export Failed] {e.Message}");
            }

            return (successCount, failCount);
        }

        /// <summary>
        /// 导出所有Buff触发器到JSON文件
        /// </summary>
        /// <param name="entries">触发器条目列表</param>
        /// <returns>(成功数, 失败数)</returns>
        public (int successCount, int failCount) ExportTriggersToJSON(List<BuffTriggerEntry> entries)
        {
            int successCount = 0;
            int failCount = 0;

            try
            {
                string triggersDir = Path.Combine(Path.GetFullPath(exportDirectory), "Triggers");
                if (!Directory.Exists(triggersDir))
                {
                    Directory.CreateDirectory(triggersDir);
                }

                Log($"\n[Export] Starting Buff Triggers JSON export to: {triggersDir}");

                foreach (var entry in entries)
                {
                    if (ExportSingleTrigger(entry, triggersDir))
                    {
                        successCount++;
                    }
                    else
                    {
                        failCount++;
                    }
                }

                Log($"[Export] Complete - Success: {successCount}, Failed: {failCount}");
            }
            catch (Exception e)
            {
                Log($"[Export Failed] {e.Message}");
            }

            return (successCount, failCount);
        }

        /// <summary>
        /// 静默导出Buff效果（不弹出对话框）
        /// </summary>
        public int ExportEffectsToJSONSilent(List<BuffEffectEntry> entries)
        {
            string effectsDir = Path.Combine(Path.GetFullPath(exportDirectory), "Effects");
            if (!Directory.Exists(effectsDir)) Directory.CreateDirectory(effectsDir);

            int successCount = 0;
            foreach (var entry in entries)
            {
                try
                {
                    if (ExportSingleEffect(entry, effectsDir))
                    {
                        successCount++;
                    }
                }
                catch { }
            }

            Log($"  Exported {successCount} Buff Effect JSON files");
            return successCount;
        }

        /// <summary>
        /// 静默导出Buff触发器（不弹出对话框）
        /// </summary>
        public int ExportTriggersToJSONSilent(List<BuffTriggerEntry> entries)
        {
            string triggersDir = Path.Combine(Path.GetFullPath(exportDirectory), "Triggers");
            if (!Directory.Exists(triggersDir)) Directory.CreateDirectory(triggersDir);

            int successCount = 0;
            foreach (var entry in entries)
            {
                try
                {
                    if (ExportSingleTrigger(entry, triggersDir))
                    {
                        successCount++;
                    }
                }
                catch { }
            }

            Log($"  Exported {successCount} Buff Trigger JSON files");
            return successCount;
        }

        /// <summary>
        /// 导出单个效果到JSON文件
        /// </summary>
        private bool ExportSingleEffect(BuffEffectEntry entry, string directory)
        {
            try
            {
                var fileWrapper = new BuffEffectFileWrapper
                {
                    version = "1.0",
                    exportTime = DateTime.Now.ToString("O"),
                    dataType = "BuffEffect",
                    effect = entry
                };

                string json = JsonUtility.ToJson(fileWrapper, true);
                string fileName = $"{entry.typeName}.json";
                string filePath = Path.Combine(directory, fileName);

                File.WriteAllText(filePath, json);
                return true;
            }
            catch (Exception e)
            {
                Log($"[Export Error] {entry.typeName}: {e.Message}");
                return false;
            }
        }

        /// <summary>
        /// 导出单个触发器到JSON文件
        /// </summary>
        private bool ExportSingleTrigger(BuffTriggerEntry entry, string directory)
        {
            try
            {
                var fileWrapper = new BuffTriggerFileWrapper
                {
                    version = "1.0",
                    exportTime = DateTime.Now.ToString("O"),
                    dataType = "BuffTrigger",
                    trigger = entry
                };

                string json = JsonUtility.ToJson(fileWrapper, true);
                string fileName = $"{entry.typeName}.json";
                string filePath = Path.Combine(directory, fileName);

                File.WriteAllText(filePath, json);
                return true;
            }
            catch (Exception e)
            {
                Log($"[Export Error] {entry.typeName}: {e.Message}");
                return false;
            }
        }

        private void Log(string message)
        {
            logAction?.Invoke(message);
        }
    }

    #region JSON Wrappers

    [Serializable]
    public class BuffEffectFileWrapper
    {
        public string version;
        public string exportTime;
        public string dataType;
        public BuffEffectEntry effect;
    }

    [Serializable]
    public class BuffTriggerFileWrapper
    {
        public string version;
        public string exportTime;
        public string dataType;
        public BuffTriggerEntry trigger;
    }

    [Serializable]
    public class BuffEnumData
    {
        public string version;
        public string exportTime;
        public List<EnumValueInfo> buffTypes;
        public List<EnumValueInfo> buffCategories;
        public List<EnumValueInfo> durationTypes;
        public List<EnumValueInfo> stackingTypes;
        public List<EnumValueInfo> dispelTypes;
        public List<EnumValueInfo> triggerEventTypes;
        public List<EnumValueInfo> attributeTypes;
        public List<EnumValueInfo> damageTypes;
        public List<EnumValueInfo> specialStateFlags;
    }

    [Serializable]
    public class EnumValueInfo
    {
        public string name;
        public int value;
        public string label;
    }

    #endregion
}
