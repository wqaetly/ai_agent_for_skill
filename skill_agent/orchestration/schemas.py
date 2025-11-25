"""
Pydantic Schema 定义
用于 LangGraph structured output，确保 DeepSeek 生成符合 Odin 格式的技能配置
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


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
