"""
Track 类型识别模块
"""

from typing import Dict, List


TRACK_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "animation": [
        "animation", "anim", "animator",
        "动画", "動畫", "动作", "動作"
    ],
    "effect": [
        "effect", "fx", "vfx", "visual", "particle",
        "特效", "效果", "伤害", "傷害", "damage", "buff", "debuff",
        "技能效果", "攻击效果", "攻擊效果"
    ],
    "audio": [
        "audio", "sound", "sfx", "music",
        "音效", "音频", "音頻", "声音", "聲音", "音乐", "音樂"
    ],
    "movement": [
        "movement", "move", "position", "translate", "dash", "teleport",
        "移动", "移動", "位移", "冲刺", "衝刺", "传送", "傳送", "位置"
    ],
    "camera": [
        "camera", "cam", "shake", "zoom", "focus",
        "镜头", "鏡頭", "相机", "相機", "震动", "震動", "震屏"
    ],
}


def infer_track_type(track_name: str) -> str:
    """
    根据 track 名称推断类型（支持中英文）

    Args:
        track_name: Track 名称（如 "Animation Track", "动画轨道"）

    Returns:
        Track 类型：animation | effect | audio | movement | camera | other
    """
    track_name_lower = track_name.lower()

    for track_type, keywords in TRACK_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in track_name_lower:
                return track_type

    return "other"
