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
            "action_name": "SpawnEffectAction",
            "action_type": "SkillSystem.Actions.SpawnEffectAction, Assembly-CSharp",
            "description": "生成特效（火焰、冰霜、闪电等视觉效果）",
            "parameters": [
                {"name": "effectPrefabPath", "type": "string", "description": "特效预制体路径"},
                {"name": "spawnPosition", "type": "Vector3", "defaultValue": "(0,0,0)"},
                {"name": "duration", "type": "float", "defaultValue": "1.0"}
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
            "action_name": "ApplyBuffAction",
            "action_type": "SkillSystem.Actions.ApplyBuffAction, Assembly-CSharp",
            "description": "施加Buff/Debuff效果（减速、燃烧、冰冻等）",
            "parameters": [
                {"name": "buffId", "type": "string", "description": "Buff ID"},
                {"name": "duration", "type": "float", "description": "持续时间"},
                {"name": "stackCount", "type": "int", "defaultValue": "1"}
            ]
        }
    ],
    "audio": [
        {
            "action_name": "PlaySoundAction",
            "action_type": "SkillSystem.Actions.PlaySoundAction, Assembly-CSharp",
            "description": "播放音效（施法音效、命中音效、环境音效）",
            "parameters": [
                {"name": "soundClipPath", "type": "string", "description": "音效文件路径"},
                {"name": "volume", "type": "float", "defaultValue": "1.0"},
                {"name": "pitch", "type": "float", "defaultValue": "1.0"},
                {"name": "loop", "type": "bool", "defaultValue": "false"}
            ]
        }
    ],
    "movement": [
        {
            "action_name": "DashAction",
            "action_type": "SkillSystem.Actions.DashAction, Assembly-CSharp",
            "description": "角色冲刺/位移",
            "parameters": [
                {"name": "direction", "type": "Vector3", "defaultValue": "(0,0,1)"},
                {"name": "distance", "type": "float", "description": "位移距离"},
                {"name": "speed", "type": "float", "description": "移动速度"}
            ]
        },
        {
            "action_name": "MoveAction",
            "action_type": "SkillSystem.Actions.MoveAction, Assembly-CSharp",
            "description": "角色位移",
            "parameters": [
                {"name": "direction", "type": "Vector3", "defaultValue": "(0,0,1)"},
                {"name": "distance", "type": "float", "defaultValue": "2.0"},
                {"name": "speed", "type": "float", "defaultValue": "5.0"}
            ]
        }
    ],
    "camera": [
        {
            "action_name": "CameraShakeAction",
            "action_type": "SkillSystem.Actions.CameraShakeAction, Assembly-CSharp",
            "description": "镜头震动效果",
            "parameters": [
                {"name": "intensity", "type": "float", "defaultValue": "0.5"},
                {"name": "duration", "type": "float", "defaultValue": "0.3"}
            ]
        }
    ],
    "other": [
        {
            "action_name": "GenericAction",
            "action_type": "SkillSystem.Actions.GenericAction, Assembly-CSharp",
            "description": "通用Action",
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
