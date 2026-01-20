using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

namespace RAG.BuffSystem
{
    /// <summary>
    /// 单个Buff Effect的描述数据
    /// </summary>
    [Serializable]
    public class BuffEffectDescriptionData
    {
        [ReadOnly]
        [LabelText("Effect类型")]
        public string typeName;

        [ReadOnly]
        [LabelText("完整类型名")]
        public string fullTypeName;

        [ReadOnly]
        [LabelText("命名空间")]
        public string namespaceName;

        [ReadOnly]
        [LabelText("程序集")]
        public string assemblyName;

        [LabelText("显示名称")]
        [InfoBox("策划可修改，用于UI显示")]
        public string displayName;

        // 参数信息
        [HideInInspector]
        public List<BuffParameterInfo> parameters = new List<BuffParameterInfo>();

        [LabelText("分类")]
        [InfoBox("策划可修改，用于分类筛选")]
        public string category;

        [TextArea(5, 10)]
        [LabelText("功能描述")]
        [InfoBox("AI生成或策划手动编写，用于RAG语义搜索的核心文本\n\n建议包含：\n- 核心功能说明\n- 关键参数说明\n- 典型使用场景\n- 与其他Effect的区别", InfoMessageType.Info)]
        public string description;

        [TextArea(3, 8)]
        [LabelText("搜索关键词")]
        [InfoBox("可选，额外的搜索关键词，用逗号分隔\n例如：属性修改,增益,减益", InfoMessageType.None)]
        public string searchKeywords;

        [HideInInspector]
        [LabelText("参数描述")]
        public SerializableDictionary<string, string> parameterDescriptions = new SerializableDictionary<string, string>();

        [HideInInspector]
        public bool isAIGenerated;

        [HideInInspector]
        [LabelText("AI生成时间")]
        public string aiGeneratedTime;

        [HideInInspector]
        [LabelText("最后修改时间")]
        public string lastModifiedTime;

        [HideInInspector]
        [LabelText("最后修改人")]
        public string lastModifiedBy;
    }

    /// <summary>
    /// 单个Buff Trigger的描述数据
    /// </summary>
    [Serializable]
    public class BuffTriggerDescriptionData
    {
        [ReadOnly]
        [LabelText("Trigger类型")]
        public string typeName;

        [ReadOnly]
        [LabelText("完整类型名")]
        public string fullTypeName;

        [ReadOnly]
        [LabelText("命名空间")]
        public string namespaceName;

        [ReadOnly]
        [LabelText("程序集")]
        public string assemblyName;

        [LabelText("显示名称")]
        [InfoBox("策划可修改，用于UI显示")]
        public string displayName;

        // 参数信息
        [HideInInspector]
        public List<BuffParameterInfo> parameters = new List<BuffParameterInfo>();

        [LabelText("分类")]
        [InfoBox("策划可修改，用于分类筛选")]
        public string category;

        [TextArea(5, 10)]
        [LabelText("功能描述")]
        [InfoBox("AI生成或策划手动编写，用于RAG语义搜索的核心文本\n\n建议包含：\n- 核心功能说明\n- 关键参数说明\n- 典型使用场景\n- 与其他Trigger的区别", InfoMessageType.Info)]
        public string description;

        [TextArea(3, 8)]
        [LabelText("搜索关键词")]
        [InfoBox("可选，额外的搜索关键词，用逗号分隔\n例如：触发,事件,条件", InfoMessageType.None)]
        public string searchKeywords;

        [HideInInspector]
        [LabelText("参数描述")]
        public SerializableDictionary<string, string> parameterDescriptions = new SerializableDictionary<string, string>();

        [HideInInspector]
        public bool isAIGenerated;

        [HideInInspector]
        [LabelText("AI生成时间")]
        public string aiGeneratedTime;

        [HideInInspector]
        [LabelText("最后修改时间")]
        public string lastModifiedTime;

        [HideInInspector]
        [LabelText("最后修改人")]
        public string lastModifiedBy;
    }

    /// <summary>
    /// Buff描述数据库 - ScriptableObject
    /// 存储所有Buff Effect和Trigger的描述信息，供RAG系统使用
    /// </summary>
    [CreateAssetMenu(fileName = "BuffDescriptionDatabase", menuName = "Buff System/Buff Description Database")]
    public class BuffDescriptionDatabase : ScriptableObject
    {
        [Title("Buff Effect描述数据库")]
        [InfoBox("此数据库存储所有Buff Effect的描述信息\n- AI自动生成的描述可以被策划手动优化\n- 修改后需要重新导出Buff JSON并重建RAG索引", InfoMessageType.Warning)]
        [ListDrawerSettings(
            ShowIndexLabels = true,
            ListElementLabelName = "typeName",
            DraggableItems = false,
            ShowPaging = true,
            NumberOfItemsPerPage = 10
        )]
        [Searchable]
        public List<BuffEffectDescriptionData> effects = new List<BuffEffectDescriptionData>();

        [Title("Buff Trigger描述数据库")]
        [InfoBox("此数据库存储所有Buff Trigger的描述信息\n- AI自动生成的描述可以被策划手动优化\n- 修改后需要重新导出Buff JSON并重建RAG索引", InfoMessageType.Warning)]
        [ListDrawerSettings(
            ShowIndexLabels = true,
            ListElementLabelName = "typeName",
            DraggableItems = false,
            ShowPaging = true,
            NumberOfItemsPerPage = 10
        )]
        [Searchable]
        public List<BuffTriggerDescriptionData> triggers = new List<BuffTriggerDescriptionData>();

        [FoldoutGroup("元数据")] [ReadOnly] public int totalEffects;
        [FoldoutGroup("元数据")] [ReadOnly] public int totalTriggers;
        [FoldoutGroup("元数据")] [ReadOnly] public int aiGeneratedCount;
        [FoldoutGroup("元数据")] [ReadOnly] public string lastUpdateTime;

        /// <summary>
        /// 根据类型名获取Effect描述数据
        /// </summary>
        public BuffEffectDescriptionData GetEffectDescriptionByType(string typeName)
        {
            return effects.Find(e => e.typeName == typeName);
        }

        /// <summary>
        /// 根据类型名获取Trigger描述数据
        /// </summary>
        public BuffTriggerDescriptionData GetTriggerDescriptionByType(string typeName)
        {
            return triggers.Find(t => t.typeName == typeName);
        }

        /// <summary>
        /// 添加或更新Effect描述
        /// </summary>
        public void AddOrUpdateEffect(BuffEffectDescriptionData data)
        {
            var existing = effects.Find(e => e.typeName == data.typeName);
            if (existing != null)
            {
                // 更新现有数据
                existing.displayName = data.displayName;
                existing.category = data.category;
                existing.description = data.description;
                existing.searchKeywords = data.searchKeywords;
                existing.lastModifiedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

                // 更新参数描述
                if (data.parameterDescriptions != null)
                {
                    if (existing.parameterDescriptions == null)
                        existing.parameterDescriptions = new SerializableDictionary<string, string>();

                    existing.parameterDescriptions.Clear();
                    foreach (var kvp in data.parameterDescriptions)
                    {
                        existing.parameterDescriptions[kvp.Key] = kvp.Value;
                    }
                }
            }
            else
            {
                // 添加新数据
                effects.Add(data);
            }

            UpdateMetadata();
        }

        /// <summary>
        /// 添加或更新Trigger描述
        /// </summary>
        public void AddOrUpdateTrigger(BuffTriggerDescriptionData data)
        {
            var existing = triggers.Find(t => t.typeName == data.typeName);
            if (existing != null)
            {
                // 更新现有数据
                existing.displayName = data.displayName;
                existing.category = data.category;
                existing.description = data.description;
                existing.searchKeywords = data.searchKeywords;
                existing.lastModifiedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

                // 更新参数描述
                if (data.parameterDescriptions != null)
                {
                    if (existing.parameterDescriptions == null)
                        existing.parameterDescriptions = new SerializableDictionary<string, string>();

                    existing.parameterDescriptions.Clear();
                    foreach (var kvp in data.parameterDescriptions)
                    {
                        existing.parameterDescriptions[kvp.Key] = kvp.Value;
                    }
                }
            }
            else
            {
                // 添加新数据
                triggers.Add(data);
            }

            UpdateMetadata();
        }

        /// <summary>
        /// 更新元数据
        /// </summary>
        public void UpdateMetadata()
        {
            totalEffects = effects.Count;
            totalTriggers = triggers.Count;
            aiGeneratedCount = effects.FindAll(e => e.isAIGenerated).Count + triggers.FindAll(t => t.isAIGenerated).Count;
            lastUpdateTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        }
    }
}

