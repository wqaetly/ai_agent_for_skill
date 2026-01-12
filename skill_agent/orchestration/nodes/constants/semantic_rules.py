"""
语义规则模块
定义 Action 语义验证规则、Track 类型规则、阶段规则等
"""

from typing import Any, Dict, List

from ...schemas import SemanticRule


# 语义验证规则
SEMANTIC_RULES: List[SemanticRule] = [
    # === 伤害相关规则 ===
    {
        "name": "damage_requires_animation",
        "condition": "DamageAction",
        "requires_before": ["AnimationAction", "SpawnEffectAction"],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "warning"
    },
    {
        "name": "area_damage_needs_effect",
        "condition": "AreaOfEffectAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "CameraAction"],
        "severity": "info"
    },
    {
        "name": "projectile_requires_spawn",
        "condition": "ProjectileAction",
        "requires_before": ["AnimationAction"],
        "suggests_after": ["DamageAction"],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "warning"
    },
    # === Buff/Debuff相关规则 ===
    {
        "name": "buff_needs_effect",
        "condition": "BuffAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },
    {
        "name": "heal_with_effect",
        "condition": "HealAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "AudioAction"],
        "severity": "info"
    },
    {
        "name": "shield_with_visual",
        "condition": "ShieldAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },
    # === 移动相关规则 ===
    {
        "name": "movement_followed_by_action",
        "condition": "MovementAction",
        "requires_before": [],
        "suggests_after": ["DamageAction", "SpawnEffectAction"],
        "suggests_with": [],
        "severity": "info"
    },
    {
        "name": "teleport_needs_effect",
        "condition": "TeleportAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "AudioAction"],
        "severity": "warning"
    },
    {
        "name": "dash_with_trail",
        "condition": "DashAction",
        "requires_before": ["AnimationAction"],
        "suggests_after": ["DamageAction"],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },
    # === 音效相关规则 ===
    {
        "name": "audio_with_animation",
        "condition": "AudioAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["AnimationAction"],
        "severity": "info"
    },
    {
        "name": "play_sound_with_action",
        "condition": "PlaySoundAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["AnimationAction", "SpawnEffectAction"],
        "severity": "info"
    },
    # === 镜头相关规则 ===
    {
        "name": "camera_shake_with_impact",
        "condition": "CameraAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["DamageAction", "SpawnEffectAction"],
        "severity": "info"
    },
    {
        "name": "camera_focus_before_skill",
        "condition": "CameraFocusAction",
        "requires_before": [],
        "suggests_after": ["AnimationAction", "SpawnEffectAction"],
        "suggests_with": [],
        "severity": "info"
    },
    # === 召唤相关规则 ===
    {
        "name": "summon_with_effect",
        "condition": "SummonAction",
        "requires_before": ["AnimationAction"],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "AudioAction"],
        "severity": "warning"
    },
    # === 控制相关规则 ===
    {
        "name": "control_with_animation",
        "condition": "ControlAction",
        "requires_before": ["AnimationAction"],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },
    {
        "name": "stun_with_effect",
        "condition": "StunAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction", "AudioAction"],
        "severity": "info"
    },
    # === 碰撞相关规则 ===
    {
        "name": "collision_after_projectile",
        "condition": "CollisionAction",
        "requires_before": ["ProjectileAction", "SpawnEffectAction"],
        "suggests_after": ["DamageAction"],
        "suggests_with": [],
        "severity": "info"
    },
    # === 资源相关规则 ===
    {
        "name": "resource_with_effect",
        "condition": "ResourceAction",
        "requires_before": [],
        "suggests_after": [],
        "suggests_with": ["SpawnEffectAction"],
        "severity": "info"
    },
]


# 阶段性规则
PHASE_RULES: Dict[str, List[str]] = {
    "setup": [
        "动画Action应放在起手阶段",
        "准备特效应在伤害前生成",
        "镜头聚焦适合放在技能开始",
    ],
    "main": [
        "核心伤害和效果应在主体阶段",
        "Buff/Debuff应用通常在主体阶段",
        "AOE伤害适合放在主体阶段中段",
    ],
    "cleanup": [
        "后摇动画应在收尾阶段",
        "消散特效应在收尾阶段",
        "技能结束音效放在收尾",
    ],
}


# Track类型特定规则
TRACK_TYPE_RULES: Dict[str, Dict[str, Any]] = {
    "animation": {
        "primary_actions": ["AnimationAction"],
        "forbidden_actions": ["DamageAction", "BuffAction"],
        "typical_count": (1, 5),
    },
    "effect": {
        "primary_actions": ["SpawnEffectAction", "DamageAction", "BuffAction", "HealAction"],
        "forbidden_actions": [],
        "typical_count": (2, 10),
    },
    "audio": {
        "primary_actions": ["AudioAction", "PlaySoundAction"],
        "forbidden_actions": ["DamageAction", "MovementAction"],
        "typical_count": (1, 5),
    },
    "movement": {
        "primary_actions": ["MovementAction", "TeleportAction", "DashAction"],
        "forbidden_actions": [],
        "typical_count": (1, 3),
    },
    "camera": {
        "primary_actions": ["CameraAction", "CameraFocusAction"],
        "forbidden_actions": ["DamageAction", "BuffAction"],
        "typical_count": (1, 3),
    },
}


# 功能关键词到Action类型的映射
SEMANTIC_KEYWORD_MAP: Dict[str, List[str]] = {
    "动画": ["AnimationAction"],
    "播放": ["AnimationAction", "PlaySoundAction"],
    "前摇": ["AnimationAction"],
    "后摇": ["AnimationAction"],
    "施法": ["AnimationAction"],
    "伤害": ["DamageAction"],
    "攻击": ["DamageAction"],
    "造成": ["DamageAction"],
    "打击": ["DamageAction"],
    "特效": ["SpawnEffectAction"],
    "效果": ["SpawnEffectAction"],
    "生成": ["SpawnEffectAction"],
    "粒子": ["SpawnEffectAction"],
    "buff": ["BuffAction"],
    "增益": ["BuffAction"],
    "debuff": ["DebuffAction"],
    "减益": ["DebuffAction"],
    "状态": ["BuffAction", "DebuffAction"],
    "燃烧": ["DebuffAction"],
    "冻结": ["DebuffAction"],
    "移动": ["MovementAction"],
    "位移": ["MovementAction"],
    "冲刺": ["MovementAction"],
    "传送": ["MovementAction"],
    "音效": ["PlaySoundAction"],
    "声音": ["PlaySoundAction"],
}
