"""
Pydantic Schema 定义
用于 LangGraph structured output，确保 DeepSeek 生成符合 Odin 格式的技能配置
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union, Tuple, TypedDict
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ==== 批次上下文相关定义 ====

class BatchPhase(str, Enum):
    """批次在Track中的阶段"""
    SETUP = "setup"        # 起手阶段（动画前摇、准备特效）
    MAIN = "main"          # 主体阶段（核心伤害、主要效果）
    CLEANUP = "cleanup"    # 收尾阶段（后摇、消散特效）


class SemanticGroup(TypedDict):
    """语义功能组（用于批次划分）"""
    name: str                    # 功能组名称（如"动画"、"伤害"、"特效"）
    keywords: List[str]          # 关键词列表
    suggested_action_types: List[str]  # 建议的Action类型
    estimated_count: int         # 预估Action数量
    phase: str                   # 所属阶段


class CompletedActionSummary(TypedDict):
    """已完成Action摘要（轻量级，用于跨批次传递）"""
    frame: int                   # 起始帧
    duration: int                # 持续帧数
    action_type: str             # 简化类型名（如"DamageAction"）
    key_params: Dict[str, Any]   # 关键参数（如damage、effectName）


class BatchContextState(TypedDict, total=False):
    """
    批次上下文状态

    用于在批次间传递设计意图、约束和已生成信息，
    解决原有纯数量驱动批次划分的语义断层问题
    """
    # 批次标识
    batch_id: int                         # 当前批次索引
    total_batches: int                    # 总批次数
    phase: str                            # 当前阶段 (BatchPhase值)

    # 设计意图
    design_intent: str                    # Track整体设计意图
    current_goal: str                     # 当前批次目标

    # 已生成摘要（结构化）
    completed_actions: List[CompletedActionSummary]  # 已完成Action摘要
    used_action_types: List[str]          # 已使用的Action类型
    occupied_frames: List[Tuple[int, int]]  # 已占用的帧区间 [(start, end), ...]

    # 约束链
    must_follow: List[str]                # 必须遵守的约束
    suggested_types: List[str]            # 建议使用的Action类型
    avoid_patterns: List[str]             # 应避免的模式（从失败中学习）

    # 依赖关系
    prerequisites_met: List[str]          # 已满足的前置条件
    pending_effects: List[str]            # 待触发的效果

    # 验证状态
    violations: List[str]                 # 已触发的语义警告


# ==== 语义验证规则 ====

class SemanticRule(TypedDict):
    """语义规则定义"""
    name: str                             # 规则名称
    condition: str                        # 触发条件（Action类型）
    requires_before: List[str]            # 必须在此之前出现的Action类型
    suggests_after: List[str]             # 建议在此之后的Action类型
    suggests_with: List[str]              # 建议同批次出现的Action类型
    severity: str                         # 严重程度: error/warning/info


# ==== 渐进式技能生成 Schema ====

class TrackPlanItem(BaseModel):
    """Track 计划项（阶段1：骨架生成时使用）"""
    trackName: str = Field(..., description="轨道名称，如：Animation Track, Effect Track")
    purpose: str = Field(
        ...,
        description="轨道用途描述（20-50字），说明该轨道的功能和预期 actions",
        min_length=10,
        max_length=100
    )
    estimatedActions: int = Field(
        ...,
        description="预估包含的 action 数量",
        ge=1,
        le=20
    )
    priority: int = Field(
        1,
        description="生成优先级（1最高）",
        ge=1
    )


class SkillSkeletonSchema(BaseModel):
    """技能骨架 Schema（阶段1输出）"""
    skillName: str = Field(..., description="技能名称", min_length=2, max_length=50)
    skillId: str = Field(
        ...,
        description="技能唯一ID，格式：小写英文-数字，如：flame-strike-001",
        pattern=r"^[a-z0-9-]+$",
        min_length=3,
        max_length=50
    )
    skillDescription: str = Field(
        ...,
        description="技能描述（10-200字）",
        min_length=10,
        max_length=300
    )
    totalDuration: int = Field(
        ...,
        description="技能总时长（帧数）",
        ge=30  # 至少 1 秒（30fps）
    )
    frameRate: int = Field(
        30,
        description="帧率",
        ge=15,
        le=120
    )
    trackPlan: List[TrackPlanItem] = Field(
        ...,
        description="Track 计划列表",
        min_length=1,
        max_length=10
    )

    @field_validator('trackPlan')
    @classmethod
    def validate_track_plan(cls, v: List[TrackPlanItem]) -> List[TrackPlanItem]:
        """验证 trackPlan 的合理性"""
        if not v:
            raise ValueError("trackPlan 不能为空")

        # 检查 trackName 唯一性
        track_names = [item.trackName for item in v]
        if len(track_names) != len(set(track_names)):
            raise ValueError("trackPlan 中存在重复的 trackName")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skillName": "冰封之怒",
                "skillId": "frozen-rage-001",
                "skillDescription": "释放冰霜之力，冻结范围内敌人并造成持续伤害",
                "totalDuration": 180,
                "frameRate": 30,
                "trackPlan": [
                    {
                        "trackName": "Animation Track",
                        "purpose": "播放施法动画和冰霜特效动画",
                        "estimatedActions": 2,
                        "priority": 1
                    },
                    {
                        "trackName": "Effect Track",
                        "purpose": "生成冰霜特效、应用冻结状态、造成伤害",
                        "estimatedActions": 3,
                        "priority": 2
                    },
                    {
                        "trackName": "Audio Track",
                        "purpose": "播放施法音效和冰冻音效",
                        "estimatedActions": 2,
                        "priority": 3
                    }
                ]
            }
        }
    )


# ==== 原有 Schema ====

class SkillAction(BaseModel):
    """技能Action定义（简化版，不含Odin元数据）"""
    frame: int = Field(..., description="动作开始帧", ge=0)
    duration: int = Field(..., description="持续帧数", ge=1)
    enabled: bool = Field(True, description="是否启用")
    parameters: Dict[str, Any] = Field(
        ...,
        description="Action参数（包含_odin_type和具体参数）。必须严格遵守RAG检索的Action定义中的参数类型、枚举值和数值约束"
    )


class SkillTrack(BaseModel):
    """技能轨道定义"""
    trackName: str = Field(..., description="轨道名称，如：Animation Track, Effect Track, Audio Track")
    enabled: bool = Field(True, description="是否启用")
    actions: List[SkillAction] = Field(
        default_factory=list,
        description="轨道内的Action列表"
    )


class OdinSkillSchema(BaseModel):
    """
    Odin技能配置Schema（完整版）

    对应Unity SkillData结构，包含tracks嵌套格式
    """
    skillName: str = Field(..., description="技能名称")
    skillId: str = Field(
        ...,
        description="技能唯一ID，格式：小写英文-数字，如：flame-shockwave-001"
    )
    skillDescription: str = Field(
        ...,
        description="技能描述（30-100字，说明技能效果和特点）"
    )
    totalDuration: int = Field(
        ...,
        description="技能总时长（帧数），必须 >= 所有action的最大结束帧",
        ge=1
    )
    frameRate: int = Field(
        30,
        description="帧率，默认30fps"
    )
    tracks: List[SkillTrack] = Field(
        ...,
        description="技能轨道列表。常见轨道类型：Animation Track（动画）, Effect Track（特效）, Audio Track（音效）, Movement Track（移动）"
    )

    model_config = ConfigDict(
        extra="allow",  # 允许额外字段（如cooldown等可选字段）
        json_schema_extra={
            "example": {
                "skillName": "火焰冲击波",
                "skillId": "flame-shockwave-001",
                "skillDescription": "释放一道火焰冲击波，造成大范围伤害并施加燃烧效果",
                "totalDuration": 150,
                "frameRate": 30,
                "tracks": [
                    {
                        "trackName": "Animation Track",
                        "enabled": True,
                        "actions": [
                            {
                                "frame": 0,
                                "duration": 30,
                                "enabled": True,
                                "parameters": {
                                    "_odin_type": "4|SkillSystem.Actions.AnimationAction, Assembly-CSharp",
                                    "animationClipName": "CastSpell",
                                    "normalizedTime": 0,
                                    "crossFadeDuration": 0.2,
                                    "animationLayer": 0
                                }
                            }
                        ]
                    }
                ]
            }
        }
    )


class SimplifiedSkillSchema(BaseModel):
    """
    简化版技能Schema（向后兼容）

    用于validator等场景，不含tracks嵌套，只有顶层actions数组
    """
    skillName: str = Field(..., description="技能名称")
    skillId: str = Field(..., description="技能ID")
    actions: List[Dict[str, Any]] = Field(..., description="Action列表（扁平结构）")

    # 可选字段
    skillDescription: Optional[str] = None
    cooldown: Optional[float] = Field(None, ge=0, description="冷却时间（秒）")
    manaCost: Optional[int] = Field(None, ge=0, description="消耗魔法值")


# 便捷函数：从OdinSkillSchema转换为SimplifiedSkillSchema
def odin_to_simplified(odin_skill: OdinSkillSchema) -> SimplifiedSkillSchema:
    """
    将完整的Odin格式转换为简化格式（扁平化tracks）

    Args:
        odin_skill: Odin格式的技能配置

    Returns:
        简化格式的技能配置
    """
    # 收集所有tracks中的actions
    all_actions = []
    for track in odin_skill.tracks:
        for action in track.actions:
            all_actions.append({
                "trackName": track.trackName,
                "frame": action.frame,
                "duration": action.duration,
                "enabled": action.enabled,
                "parameters": action.parameters
            })

    return SimplifiedSkillSchema(
        skillName=odin_skill.skillName,
        skillId=odin_skill.skillId,
        skillDescription=odin_skill.skillDescription,
        actions=all_actions
    )


# ==== Action批次级渐进式生成 Schema ====

class ActionBatchPlan(BaseModel):
    """单个Action批次计划（用于更细粒度的渐进式生成）"""
    batch_index: int = Field(..., description="批次索引(0-based)", ge=0)
    action_count: int = Field(..., description="本批次应生成的action数量", ge=1, le=10)
    start_frame_hint: int = Field(..., description="建议起始帧(提示作用)", ge=0)
    end_frame_hint: int = Field(..., description="建议结束帧(提示作用)", ge=1)
    context: str = Field(
        ...,
        description="批次上下文描述，说明该批次actions的时间段和功能（如'前摇阶段'、'爆发阶段'）",
        min_length=5,
        max_length=100
    )


class ActionBatch(BaseModel):
    """Action批次数据（生成节点的输出）"""
    batch_index: int = Field(..., description="批次索引", ge=0)
    actions: List[SkillAction] = Field(
        default_factory=list,
        description="本批次生成的actions（空列表表示跳过的批次）",
        max_length=10
    )
    # 注：移除了 min_length=1，允许空批次用于错误恢复场景


# ==== 单Action级渐进式生成 Schema ====

class SingleActionPlan(BaseModel):
    """单个Action的生成计划"""
    action_index: int = Field(..., description="Action索引(0-based)", ge=0)
    suggested_type: Optional[str] = Field(None, description="建议的Action类型")
    frame_hint: int = Field(..., description="建议起始帧", ge=0)
    duration_hint: int = Field(30, description="建议持续帧数", ge=1)
    purpose: str = Field(
        ...,
        description="该Action的功能描述",
        min_length=2,
        max_length=100
    )


class SingleActionOutput(BaseModel):
    """单个Action生成输出"""
    action: SkillAction = Field(..., description="生成的单个Action")
    reasoning: Optional[str] = Field(
        None,
        description="生成该Action的简要理由（可选）",
        max_length=200
    )



# ==== Buff 系统 Schema ====

class BuffEffectType(str, Enum):
    """Buff效果类型"""
    ATTRIBUTE_MODIFIER = "AttributeModifierEffect"
    DAMAGE_OVER_TIME = "DamageOverTimeEffect"
    HEAL_OVER_TIME = "HealOverTimeEffect"
    SPECIAL_STATE = "SpecialStateEffect"
    SHIELD = "ShieldEffect"


class BuffTriggerType(str, Enum):
    """Buff触发器类型"""
    PERIODIC = "PeriodicTrigger"
    EVENT = "EventTrigger"
    THRESHOLD = "ThresholdTrigger"
    CONDITIONAL = "ConditionalTrigger"


class BuffType(str, Enum):
    """Buff类型"""
    BUFF = "Buff"
    DEBUFF = "Debuff"
    NEUTRAL = "Neutral"


class BuffCategory(str, Enum):
    """Buff分类"""
    COMMON = "Common"
    ATTRIBUTE_BOOST = "AttributeBoost"
    ATTRIBUTE_REDUCTION = "AttributeReduction"
    DAMAGE_OVER_TIME = "DamageOverTime"
    HEAL_OVER_TIME = "HealOverTime"
    CROWD_CONTROL = "CrowdControl"
    SHIELD = "Shield"
    SPECIAL_STATE = "SpecialState"
    AURA = "Aura"
    PASSIVE = "Passive"


class DurationType(str, Enum):
    """持续时间类型"""
    TIMED = "Timed"
    PERMANENT = "Permanent"
    CHARGES = "Charges"


class StackingType(str, Enum):
    """叠加类型"""
    NONE = "None"
    REFRESH = "Refresh"
    STACKABLE = "Stackable"
    INDEPENDENT = "Independent"


class AttributeModifier(BaseModel):
    """属性修改器"""
    attributeType: str = Field(..., description="属性类型，如：Health, AttackDamage, Armor等")
    modifierType: str = Field("Flat", description="修改类型：Flat(固定值), PercentAdd(百分比加成), PercentMult(百分比乘算)")
    value: float = Field(..., description="修改值")


class BuffEffect(BaseModel):
    """Buff效果定义"""
    effectType: str = Field(..., description="效果类型，如：AttributeModifierEffect, DamageOverTimeEffect等")
    effectName: str = Field("", description="效果名称")
    description: str = Field("", description="效果描述")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="效果参数，根据effectType不同而不同"
    )


class BuffTrigger(BaseModel):
    """Buff触发器定义"""
    triggerType: str = Field(..., description="触发器类型，如：PeriodicTrigger, EventTrigger等")
    triggerName: str = Field("", description="触发器名称")
    description: str = Field("", description="触发器描述")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="触发器参数，根据triggerType不同而不同"
    )


class BuffTemplateSchema(BaseModel):
    """
    Buff模板Schema - 用于LLM生成Buff配置

    对应Unity BuffTemplate结构
    """
    buffId: str = Field(
        ...,
        description="Buff唯一ID，格式：小写英文-数字，如：strength-boost-001",
        pattern=r"^[a-z0-9-]+$",
        min_length=3,
        max_length=50
    )
    buffName: str = Field(..., description="Buff名称", min_length=2, max_length=50)
    displayName: str = Field("", description="显示名称（UI中显示）")
    description: str = Field(
        ...,
        description="Buff描述（10-200字）",
        min_length=10,
        max_length=300
    )

    # 类型配置
    buffType: str = Field("Buff", description="Buff类型：Buff(增益), Debuff(减益), Neutral(中性)")
    category: str = Field("Common", description="Buff分类")
    priority: int = Field(0, description="优先级，高优先级先计算", ge=0, le=100)

    # 持续时间配置
    durationType: str = Field("Timed", description="持续时间类型：Timed(定时), Permanent(永久), Charges(次数)")
    duration: float = Field(5.0, description="持续时间（秒）", ge=0.1)
    canRefresh: bool = Field(True, description="重复施加时是否刷新持续时间")

    # 叠加配置
    stackingType: str = Field("Refresh", description="叠加类型：None(替换), Refresh(刷新), Stackable(叠加), Independent(独立)")
    maxStacks: int = Field(1, description="最大层数", ge=1, le=99)

    # 效果列表
    effects: List[BuffEffect] = Field(
        default_factory=list,
        description="Buff效果列表"
    )

    # 触发器列表
    triggers: List[BuffTrigger] = Field(
        default_factory=list,
        description="Buff触发器列表"
    )

    # 驱散配置
    canBeDispelled: bool = Field(True, description="是否可被驱散")
    dispelType: str = Field("Magic", description="驱散类型：Magic(魔法), Physical(物理), Strong(强驱散), None(不可驱散)")
    removeOnDeath: bool = Field(True, description="死亡时是否移除")

    # 互斥配置
    exclusionGroup: str = Field("", description="互斥组，同组Buff不能共存")
    incompatibleBuffs: List[str] = Field(
        default_factory=list,
        description="不可共存的Buff ID列表"
    )

    # 标签
    tags: List[str] = Field(
        default_factory=list,
        description="Buff标签，用于分类和查询"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "buffId": "strength-boost-001",
                "buffName": "力量增强",
                "displayName": "力量增强",
                "description": "增加目标的攻击力，持续10秒，可叠加3层",
                "buffType": "Buff",
                "category": "AttributeBoost",
                "priority": 10,
                "durationType": "Timed",
                "duration": 10.0,
                "canRefresh": True,
                "stackingType": "Stackable",
                "maxStacks": 3,
                "effects": [
                    {
                        "effectType": "AttributeModifierEffect",
                        "effectName": "攻击力提升",
                        "description": "提升攻击力",
                        "parameters": {
                            "modifiers": [
                                {"attributeType": "AttackDamage", "modifierType": "PercentAdd", "value": 0.1}
                            ],
                            "scaleWithStacks": True
                        }
                    }
                ],
                "triggers": [],
                "canBeDispelled": True,
                "dispelType": "Magic",
                "removeOnDeath": True,
                "exclusionGroup": "",
                "incompatibleBuffs": [],
                "tags": ["增益", "攻击", "可叠加"]
            }
        }
    )


class BuffSkeletonSchema(BaseModel):
    """Buff骨架Schema（用于渐进式生成的第一阶段）"""
    buffId: str = Field(
        ...,
        description="Buff唯一ID",
        pattern=r"^[a-z0-9-]+$"
    )
    buffName: str = Field(..., description="Buff名称")
    description: str = Field(..., description="Buff描述")
    buffType: str = Field("Buff", description="Buff类型")
    category: str = Field("Common", description="Buff分类")

    # 效果计划
    effectPlan: List[Dict[str, str]] = Field(
        default_factory=list,
        description="计划的效果列表，每项包含effectType和purpose"
    )

    # 触发器计划
    triggerPlan: List[Dict[str, str]] = Field(
        default_factory=list,
        description="计划的触发器列表，每项包含triggerType和purpose"
    )


class BuffGenerationRequest(BaseModel):
    """Buff生成请求"""
    user_prompt: str = Field(..., description="用户的Buff需求描述")
    buff_type_hint: Optional[str] = Field(None, description="Buff类型提示")
    category_hint: Optional[str] = Field(None, description="分类提示")
    reference_buffs: List[str] = Field(
        default_factory=list,
        description="参考的已有Buff ID列表"
    )