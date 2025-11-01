using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;


namespace SkillSystem.Editor.Data
{
    /// <summary>
    /// Action描述数据库 - ScriptableObject
    /// 存储所有Action的描述信息，供RAG系统使用
    /// </summary>
    [CreateAssetMenu(fileName = "ActionDescriptionDatabase", menuName = "Skill System/Action Description Database")]
    public class ActionDescriptionDatabase : ScriptableObject
    {
        [Title("Action描述数据库")]
        [InfoBox("此数据库存储所有Action的描述信息\n- AI自动生成的描述可以被策划手动优化\n- 修改后需要重新导出Action JSON并重建RAG索引", InfoMessageType.Warning)]
        [ListDrawerSettings(
            ShowIndexLabels = true,
            ListElementLabelName = "typeName",
            DraggableItems = false,
            ShowPaging = true,
            NumberOfItemsPerPage = 10
        )]
        [Searchable]
        public List<ActionDescriptionData> actions = new List<ActionDescriptionData>();

        [FoldoutGroup("元数据")] [ReadOnly] public int totalActions;

        [FoldoutGroup("元数据")] [ReadOnly] public int aiGeneratedCount;

        [FoldoutGroup("元数据")] [ReadOnly] public int manuallyEditedCount;

        [FoldoutGroup("元数据")] [ReadOnly] public string lastUpdateTime;

        /// <summary>
        /// 根据类型名获取描述数据
        /// </summary>
        public ActionDescriptionData GetDescriptionByType(string typeName)
        {
            return actions.Find(a => a.typeName == typeName);
        }

        /// <summary>
        /// 添加或更新Action描述
        /// </summary>
        public void AddOrUpdateAction(ActionDescriptionData data)
        {
            var existing = actions.Find(a => a.typeName == data.typeName);
            if (existing != null)
            {
                // 更新现有数据
                existing.displayName = data.displayName;
                existing.category = data.category;
                existing.description = data.description;
                existing.searchKeywords = data.searchKeywords;
                existing.lastModifiedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            }
            else
            {
                // 添加新数据
                actions.Add(data);
            }

            UpdateMetadata();
        }

        /// <summary>
        /// 更新元数据
        /// </summary>
        public void UpdateMetadata()
        {
            totalActions = actions.Count;
            aiGeneratedCount = actions.FindAll(a => a.isAIGenerated).Count;
            manuallyEditedCount = actions.FindAll(a => !string.IsNullOrEmpty(a.lastModifiedBy)).Count;
            lastUpdateTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        }

        /// <summary>
        /// 清理不存在的Action
        /// </summary>
        public void CleanupMissingActions(List<string> validTypeNames)
        {
            actions.RemoveAll(a => !validTypeNames.Contains(a.typeName));
            UpdateMetadata();
        }
    }
    
}