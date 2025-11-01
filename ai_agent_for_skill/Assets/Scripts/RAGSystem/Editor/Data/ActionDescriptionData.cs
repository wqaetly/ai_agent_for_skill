using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Editor.Data
{
    /// <summary>
    /// 单个Action的描述数据
    /// </summary>
    [Serializable]
    public class ActionDescriptionData
    {
        [ReadOnly]
        [LabelText("Action类型")]
        public string typeName;

        [ReadOnly]
        [LabelText("命名空间")]
        public string namespaceName;

        [LabelText("显示名称")]
        [InfoBox("策划可修改，用于UI显示")]
        public string displayName;

        [LabelText("分类")]
        [InfoBox("策划可修改，用于分类筛选")]
        public string category;

        [TextArea(5, 10)]
        [LabelText("功能描述")]
        [InfoBox("AI生成或策划手动编写，用于RAG语义搜索的核心文本\n\n建议包含：\n- 核心功能说明\n- 关键参数说明\n- 典型使用场景\n- 与其他Action的区别", InfoMessageType.Info)]
        public string description;

        [TextArea(3, 8)]
        [LabelText("搜索关键词")]
        [InfoBox("可选，额外的搜索关键词，用逗号分隔\n例如：位移,移动,冲刺,闪现", InfoMessageType.None)]
        public string searchKeywords;

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
}
