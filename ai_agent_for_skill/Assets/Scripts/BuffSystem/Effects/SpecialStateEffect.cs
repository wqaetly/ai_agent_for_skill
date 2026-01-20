using System;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Effects
{
    /// <summary>
    /// 特殊状态效果 - 施加控制和特殊状态
    /// </summary>
    [Serializable]
    [LabelText("特殊状态")]
    public class SpecialStateEffect : BuffEffectBase
    {
        [BoxGroup("State")]
        [LabelText("状态类型")]
        [EnumToggleButtons]
        public SpecialStateFlags stateFlags = SpecialStateFlags.None;
        
        [BoxGroup("State")]
        [LabelText("状态强度")]
        [InfoBox("用于同类状态的优先级判断，高强度覆盖低强度")]
        [Range(1, 10)]
        public int stateStrength = 1;
        
        [BoxGroup("Visual")]
        [LabelText("状态图标")]
        [PreviewField(50)]
        public Sprite stateIcon;
        
        [BoxGroup("Visual")]
        [LabelText("状态颜色")]
        public Color stateColor = Color.white;
        
        public SpecialStateEffect()
        {
            effectName = "特殊状态";
            description = "施加控制或特殊状态";
        }
        
        public override void OnApply(BuffContext context)
        {
            Debug.Log($"[SpecialState] Applying states {stateFlags} to {context.Target?.name}");
            
            // 实际项目中这里会调用状态系统的API
            // StateSystem.ApplyState(context.Target, stateFlags);
        }
        
        public override void OnRemove(BuffContext context)
        {
            Debug.Log($"[SpecialState] Removing states {stateFlags} from {context.Target?.name}");
            
            // StateSystem.RemoveState(context.Target, stateFlags);
        }
    }
    
    /// <summary>
    /// 特殊状态标志（可组合）
    /// </summary>
    [Flags]
    public enum SpecialStateFlags
    {
        None = 0,
        
        // 控制效果
        [LabelText("眩晕")] Stun = 1 << 0,
        [LabelText("沉默")] Silence = 1 << 1,
        [LabelText("缴械")] Disarm = 1 << 2,
        [LabelText("定身")] Root = 1 << 3,
        [LabelText("减速")] Slow = 1 << 4,
        [LabelText("嘲讽")] Taunt = 1 << 5,
        [LabelText("恐惧")] Fear = 1 << 6,
        [LabelText("魅惑")] Charm = 1 << 7,
        [LabelText("催眠")] Sleep = 1 << 8,
        [LabelText("击飞")] Knockup = 1 << 9,
        [LabelText("击退")] Knockback = 1 << 10,
        [LabelText("拉拽")] Pull = 1 << 11,
        
        // 免疫效果
        [LabelText("魔法免疫")] MagicImmune = 1 << 12,
        [LabelText("物理免疫")] PhysicalImmune = 1 << 13,
        [LabelText("无敌")] Invulnerable = 1 << 14,
        [LabelText("不可选中")] Untargetable = 1 << 15,
        
        // 特殊状态
        [LabelText("隐身")] Invisible = 1 << 16,
        [LabelText("虚化")] Phased = 1 << 17,
        [LabelText("飞行")] Flying = 1 << 18,
        [LabelText("无视地形")] IgnoreTerrain = 1 << 19,
        
        // 组合状态
        [LabelText("完全控制")] FullControl = Stun | Silence | Disarm | Root
    }
}

