using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

namespace BuffSystem.Data
{
    /// <summary>
    /// Buff模板 - 定义Buff的静态配置数据
    /// </summary>
    [Serializable]
    public class BuffTemplate
    {
        #region 基础信息
        
        [BoxGroup("基础信息")]
        [LabelText("Buff ID")]
        [InfoBox("唯一标识符，建议使用小写英文和数字")]
        public string buffId = "";
        
        [BoxGroup("基础信息")]
        [LabelText("Buff名称")]
        public string buffName = "新Buff";
        
        [BoxGroup("基础信息")]
        [LabelText("显示名称")]
        [InfoBox("在UI中显示的名称")]
        public string displayName = "";
        
        [BoxGroup("基础信息")]
        [LabelText("描述")]
        [TextArea(3, 6)]
        public string description = "";
        
        [BoxGroup("基础信息")]
        [LabelText("Buff类型")]
        public BuffType buffType = BuffType.Buff;
        
        [BoxGroup("基础信息")]
        [LabelText("分类")]
        public BuffCategory category = BuffCategory.Common;
        
        [BoxGroup("基础信息")]
        [LabelText("优先级")]
        [InfoBox("高优先级的Buff先计算")]
        [Range(0, 100)]
        public int priority = 0;
        
        #endregion
        
        #region 持续时间
        
        [BoxGroup("持续时间")]
        [LabelText("持续类型")]
        public DurationType durationType = DurationType.Timed;
        
        [BoxGroup("持续时间")]
        [LabelText("持续时间(秒)")]
        [ShowIf("durationType", DurationType.Timed)]
        [MinValue(0.1f)]
        public float duration = 5f;
        
        [BoxGroup("持续时间")]
        [LabelText("可刷新")]
        [InfoBox("重复施加时是否刷新持续时间")]
        public bool canRefresh = true;
        
        #endregion
        
        #region 叠加配置
        
        [BoxGroup("叠加配置")]
        [LabelText("叠加类型")]
        public StackingType stackingType = StackingType.Refresh;
        
        [BoxGroup("叠加配置")]
        [LabelText("最大层数")]
        [ShowIf("@stackingType == StackingType.Stackable")]
        [Range(1, 99)]
        public int maxStacks = 1;
        
        #endregion
        
        #region 效果列表
        
        [BoxGroup("效果")]
        [LabelText("Buff效果")]
        [ListDrawerSettings(ShowIndexLabels = true, DraggableItems = true)]
        [SerializeReference]
        public List<IBuffEffect> effects = new List<IBuffEffect>();
        
        #endregion
        
        #region 触发器列表
        
        [BoxGroup("触发器")]
        [LabelText("Buff触发器")]
        [ListDrawerSettings(ShowIndexLabels = true, DraggableItems = true)]
        [SerializeReference]
        public List<IBuffTrigger> triggers = new List<IBuffTrigger>();
        
        #endregion
        
        #region 驱散配置
        
        [BoxGroup("驱散配置")]
        [LabelText("可被驱散")]
        public bool canBeDispelled = true;
        
        [BoxGroup("驱散配置")]
        [LabelText("驱散类型")]
        [ShowIf("canBeDispelled")]
        public DispelType dispelType = DispelType.Magic;
        
        [BoxGroup("驱散配置")]
        [LabelText("死亡时移除")]
        public bool removeOnDeath = true;
        
        #endregion
        
        #region 互斥配置
        
        [BoxGroup("互斥配置")]
        [LabelText("互斥组")]
        [InfoBox("同一互斥组的Buff不能共存")]
        public string exclusionGroup = "";
        
        [BoxGroup("互斥配置")]
        [LabelText("不兼容的Buff")]
        public List<string> incompatibleBuffs = new List<string>();
        
        #endregion
        
        #region 标签
        
        [BoxGroup("标签")]
        [LabelText("Buff标签")]
        [InfoBox("用于分类和查询")]
        public List<string> tags = new List<string>();
        
        #endregion
    }

    #region 枚举定义

    /// <summary>
    /// Buff类型
    /// </summary>
    public enum BuffType
    {
        [LabelText("增益")] Buff,
        [LabelText("减益")] Debuff,
        [LabelText("中性")] Neutral
    }

    /// <summary>
    /// Buff分类
    /// </summary>
    public enum BuffCategory
    {
        [LabelText("通用")] Common,
        [LabelText("属性增强")] AttributeBoost,
        [LabelText("属性削弱")] AttributeReduction,
        [LabelText("持续伤害")] DamageOverTime,
        [LabelText("持续治疗")] HealOverTime,
        [LabelText("控制")] CrowdControl,
        [LabelText("护盾")] Shield,
        [LabelText("特殊状态")] SpecialState,
        [LabelText("光环")] Aura,
        [LabelText("被动")] Passive
    }

    /// <summary>
    /// 持续时间类型
    /// </summary>
    public enum DurationType
    {
        [LabelText("定时")] Timed,
        [LabelText("永久")] Permanent,
        [LabelText("次数")] Charges
    }

    /// <summary>
    /// 叠加类型
    /// </summary>
    public enum StackingType
    {
        [LabelText("不叠加(替换)")] None,
        [LabelText("刷新时间")] Refresh,
        [LabelText("叠加层数")] Stackable,
        [LabelText("独立实例")] Independent
    }

    /// <summary>
    /// 驱散类型
    /// </summary>
    public enum DispelType
    {
        [LabelText("无法驱散")] None,
        [LabelText("魔法驱散")] Magic,
        [LabelText("物理驱散")] Physical,
        [LabelText("强驱散")] Strong
    }

    #endregion
}
