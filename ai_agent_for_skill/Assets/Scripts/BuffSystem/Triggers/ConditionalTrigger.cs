using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;
using BuffSystem.Data;

namespace BuffSystem.Triggers
{
    /// <summary>
    /// 条件触发器 - 当满足特定条件时触发
    /// </summary>
    [Serializable]
    [LabelText("条件触发")]
    public class ConditionalTrigger : BuffTriggerBase
    {
        [BoxGroup("Conditions")]
        [LabelText("条件组合方式")]
        public ConditionCombineType combineType = ConditionCombineType.All;
        
        [BoxGroup("Conditions")]
        [LabelText("条件列表")]
        [ListDrawerSettings(ShowIndexLabels = true)]
        public List<TriggerCondition> conditions = new List<TriggerCondition>();
        
        [BoxGroup("Check")]
        [LabelText("检查间隔(秒)")]
        [MinValue(0.1f)]
        public float checkInterval = 0.5f;
        
        [BoxGroup("Effect")]
        [LabelText("触发时执行的效果索引")]
        public int effectIndex = -1;
        
        private float checkTimer = 0f;
        
        public ConditionalTrigger()
        {
            triggerName = "条件触发";
            description = "当满足特定条件时触发";
        }
        
        public override void Initialize(BuffContext context)
        {
            base.Initialize(context);
            checkTimer = 0f;
        }
        
        public override bool ShouldTrigger(BuffContext context, TriggerEventArgs args)
        {
            if (!base.ShouldTrigger(context, args))
                return false;
            
            return EvaluateConditions(context);
        }
        
        public override void Execute(BuffContext context, TriggerEventArgs args)
        {
            base.Execute(context, args);
            
            Debug.Log($"[ConditionalTrigger] Conditions met, triggering effect");
            
            if (effectIndex >= 0 && effectIndex < context.Template.effects.Count)
            {
                context.Template.effects[effectIndex].OnTick(context, 0);
            }
        }
        
        /// <summary>
        /// 更新检查计时器
        /// </summary>
        public bool UpdateCheck(float deltaTime)
        {
            checkTimer += deltaTime;
            if (checkTimer >= checkInterval)
            {
                checkTimer = 0f;
                return true;
            }
            return false;
        }
        
        private bool EvaluateConditions(BuffContext context)
        {
            if (conditions.Count == 0)
                return true;
            
            switch (combineType)
            {
                case ConditionCombineType.All:
                    foreach (var condition in conditions)
                    {
                        if (!condition.Evaluate(context))
                            return false;
                    }
                    return true;
                    
                case ConditionCombineType.Any:
                    foreach (var condition in conditions)
                    {
                        if (condition.Evaluate(context))
                            return true;
                    }
                    return false;
                    
                default:
                    return false;
            }
        }
    }
    
    /// <summary>
    /// 条件组合类型
    /// </summary>
    public enum ConditionCombineType
    {
        [LabelText("全部满足")] All,
        [LabelText("任一满足")] Any
    }
    
    /// <summary>
    /// 触发条件
    /// </summary>
    [Serializable]
    public class TriggerCondition
    {
        [LabelText("条件类型")]
        public ConditionType conditionType = ConditionType.HasBuff;
        
        [LabelText("比较操作")]
        [ShowIf("@conditionType != ConditionType.HasBuff && conditionType != ConditionType.HasState")]
        public CompareOperator compareOperator = CompareOperator.GreaterThan;
        
        [LabelText("比较值")]
        [ShowIf("@conditionType != ConditionType.HasBuff && conditionType != ConditionType.HasState")]
        public float compareValue = 0f;
        
        [LabelText("Buff ID")]
        [ShowIf("conditionType", ConditionType.HasBuff)]
        public string buffId = "";
        
        [LabelText("状态标志")]
        [ShowIf("conditionType", ConditionType.HasState)]
        public int stateFlag = 0;
        
        [LabelText("取反")]
        public bool negate = false;

        public bool Evaluate(BuffContext context)
        {
            bool result = false;

            switch (conditionType)
            {
                case ConditionType.HealthPercent:
                    // result = CompareValue(GetHealthPercent(context.Target), compareValue, compareOperator);
                    break;
                case ConditionType.ManaPercent:
                    // result = CompareValue(GetManaPercent(context.Target), compareValue, compareOperator);
                    break;
                case ConditionType.StackCount:
                    result = CompareValue(context.CurrentStacks, compareValue, compareOperator);
                    break;
                case ConditionType.HasBuff:
                    // result = HasBuff(context.Target, buffId);
                    break;
                case ConditionType.HasState:
                    // result = HasState(context.Target, stateFlag);
                    break;
                case ConditionType.RemainingDuration:
                    result = CompareValue(context.RemainingDuration, compareValue, compareOperator);
                    break;
            }

            return negate ? !result : result;
        }

        private bool CompareValue(float a, float b, CompareOperator op)
        {
            switch (op)
            {
                case CompareOperator.Equal:
                    return Mathf.Approximately(a, b);
                case CompareOperator.NotEqual:
                    return !Mathf.Approximately(a, b);
                case CompareOperator.GreaterThan:
                    return a > b;
                case CompareOperator.GreaterOrEqual:
                    return a >= b;
                case CompareOperator.LessThan:
                    return a < b;
                case CompareOperator.LessOrEqual:
                    return a <= b;
                default:
                    return false;
            }
        }
    }

    /// <summary>
    /// 条件类型
    /// </summary>
    public enum ConditionType
    {
        [LabelText("生命值百分比")] HealthPercent,
        [LabelText("法力值百分比")] ManaPercent,
        [LabelText("层数")] StackCount,
        [LabelText("拥有Buff")] HasBuff,
        [LabelText("拥有状态")] HasState,
        [LabelText("剩余持续时间")] RemainingDuration
    }

    /// <summary>
    /// 比较操作符
    /// </summary>
    public enum CompareOperator
    {
        [LabelText("等于")] Equal,
        [LabelText("不等于")] NotEqual,
        [LabelText("大于")] GreaterThan,
        [LabelText("大于等于")] GreaterOrEqual,
        [LabelText("小于")] LessThan,
        [LabelText("小于等于")] LessOrEqual
    }
}

