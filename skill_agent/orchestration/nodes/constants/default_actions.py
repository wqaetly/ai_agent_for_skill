"""
默认 Action 模板
当 RAG 检索失败时使用，确保 LLM 有正确的 Action 类型参考
"""

from typing import Any, Dict, List


DEFAULT_ACTIONS_BY_TRACK_TYPE: Dict[str, List[Dict[str, Any]]] = {
    "animation": [
        {
            "action_name": "AnimationAction",
            "action_type": "SkillSystem.Actions.AnimationAction, Assembly-CSharp",
            "description": "播放角色动画（攻击、施法、受击等）",
            "parameters": [
                {"name": "animationClipName", "type": "string", "description": "动画片段名称"},
                {"name": "normalizedTime", "type": "float", "defaultValue": "0"},
                {"name": "crossFadeDuration", "type": "float", "defaultValue": "0.1"},
                {"name": "animationLayer", "type": "int", "defaultValue": "0"}
            ]
        }
    ],
    "effect": [
        {
            "action_name": "CollisionAction",
            "action_type": "SkillSystem.Actions.CollisionAction, Assembly-CSharp",
            "description": "碰撞检测（用于伤害判定、触发效果等）",
            "parameters": [
                {"name": "shape", "type": "string", "description": "碰撞形状"},
                {"name": "position", "type": "Vector3", "defaultValue": "(0,0,0)"},
                {"name": "size", "type": "Vector3", "defaultValue": "(1,1,1)"}
            ]
        },
        {
            "action_name": "DamageAction",
            "action_type": "SkillSystem.Actions.DamageAction, Assembly-CSharp",
            "description": "造成伤害（物理、魔法、真实伤害）",
            "parameters": [
                {"name": "damageAmount", "type": "float", "description": "伤害数值"},
                {"name": "damageType", "type": "DamageType", "defaultValue": "Physical"},
                {"name": "radius", "type": "float", "defaultValue": "1.0"}
            ]
        },
        {
            "action_name": "BuffAction",
            "action_type": "SkillSystem.Actions.BuffAction, Assembly-CSharp",
            "description": "施加Buff/Debuff效果（减速、燃烧、冰冻等）",
            "parameters": [
                {"name": "buffId", "type": "string", "description": "Buff ID"},
                {"name": "duration", "type": "float", "description": "持续时间"},
                {"name": "stackCount", "type": "int", "defaultValue": "1"}
            ]
        },
        {
            "action_name": "AreaOfEffectAction",
            "action_type": "SkillSystem.Actions.AreaOfEffectAction, Assembly-CSharp",
            "description": "范围效果（AOE伤害、治疗等）",
            "parameters": [
                {"name": "centerPosition", "type": "Vector3", "defaultValue": "(0,0,0)"},
                {"name": "radius", "type": "float", "defaultValue": "3.0"},
                {"name": "duration", "type": "float", "defaultValue": "1.0"}
            ]
        }
    ],
    "audio": [
        {
            "action_name": "AudioAction",
            "action_type": "SkillSystem.Actions.AudioAction, Assembly-CSharp",
            "description": "播放音效（施法音效、命中音效、环境音效）",
            "parameters": [
                {"name": "audioClipName", "type": "string", "description": "音效文件名称"},
                {"name": "volume", "type": "float", "defaultValue": "1.0"},
                {"name": "pitch", "type": "float", "defaultValue": "1.0"},
                {"name": "loop", "type": "bool", "defaultValue": "false"}
            ]
        }
    ],
    "movement": [
        {
            "action_name": "MovementAction",
            "action_type": "SkillSystem.Actions.MovementAction, Assembly-CSharp",
            "description": "角色位移/冲刺",
            "parameters": [
                {"name": "targetPosition", "type": "Vector3", "defaultValue": "(0,0,0)"},
                {"name": "duration", "type": "float", "defaultValue": "0.5"},
                {"name": "speed", "type": "float", "description": "移动速度"}
            ]
        },
        {
            "action_name": "TeleportAction",
            "action_type": "SkillSystem.Actions.TeleportAction, Assembly-CSharp",
            "description": "瞬间传送",
            "parameters": [
                {"name": "targetPosition", "type": "Vector3", "defaultValue": "(0,0,10)"},
                {"name": "duration", "type": "float", "defaultValue": "0.1"}
            ]
        }
    ],
    "camera": [
        {
            "action_name": "CameraAction",
            "action_type": "SkillSystem.Actions.CameraAction, Assembly-CSharp",
            "description": "镜头效果（震动、缩放等）",
            "parameters": [
                {"name": "positionOffset", "type": "Vector3", "defaultValue": "(0,0,0)"},
                {"name": "rotationOffset", "type": "Vector3", "defaultValue": "(0,0,0)"},
                {"name": "duration", "type": "float", "defaultValue": "0.3"}
            ]
        }
    ],
    "other": [
        {
            "action_name": "LogAction",
            "action_type": "SkillSystem.Actions.LogAction, Assembly-CSharp",
            "description": "日志输出（调试用）",
            "parameters": []
        }
    ]
}


def get_default_actions_for_track_type(track_type: str) -> List[Dict[str, Any]]:
    """
    获取指定 Track 类型的默认 Action 模板
    
    当 RAG 检索失败时使用，确保 LLM 有参考格式
    """
    return DEFAULT_ACTIONS_BY_TRACK_TYPE.get(
        track_type, 
        DEFAULT_ACTIONS_BY_TRACK_TYPE["other"]
    )
