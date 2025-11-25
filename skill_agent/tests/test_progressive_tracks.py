"""
渐进式技能生成 - 阶段2（Track 生成）单元测试
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.nodes.progressive_skill_nodes import (
    infer_track_type,
    validate_track,
    format_action_schemas_for_prompt,
    should_fix_track,
    should_continue_tracks,
)


# ==================== Track 类型推断测试 ====================

class TestInferTrackType:
    """测试 infer_track_type 函数"""

    def test_animation_track(self):
        """测试识别 Animation Track"""
        assert infer_track_type("Animation Track") == "animation"
        assert infer_track_type("Anim Track") == "animation"
        assert infer_track_type("animation_track") == "animation"

    def test_effect_track(self):
        """测试识别 Effect Track"""
        assert infer_track_type("Effect Track") == "effect"
        assert infer_track_type("VFX Track") == "effect"
        assert infer_track_type("fx track") == "effect"

    def test_audio_track(self):
        """测试识别 Audio Track"""
        assert infer_track_type("Audio Track") == "audio"
        assert infer_track_type("Sound Track") == "audio"

    def test_movement_track(self):
        """测试识别 Movement Track"""
        assert infer_track_type("Movement Track") == "movement"
        assert infer_track_type("Move Track") == "movement"

    def test_camera_track(self):
        """测试识别 Camera Track"""
        assert infer_track_type("Camera Track") == "camera"
        assert infer_track_type("Cam Track") == "camera"

    def test_other_track(self):
        """测试其他未知类型"""
        assert infer_track_type("Unknown Track") == "other"
        assert infer_track_type("Custom Track") == "other"


# ==================== Track 验证测试 ====================

class TestValidateTrack:
    """测试 validate_track 函数"""

    def test_valid_track(self):
        """测试有效的 Track"""
        track = {
            "trackName": "Animation Track",
            "enabled": True,
            "actions": [
                {
                    "frame": 0,
                    "duration": 30,
                    "enabled": True,
                    "parameters": {
                        "_odin_type": "4|SkillSystem.Actions.AnimationAction, Assembly-CSharp",
                        "animationClipName": "Attack"
                    }
                }
            ]
        }

        errors = validate_track(track, total_duration=150)
        assert errors == []

    def test_missing_track_name(self):
        """测试缺少 trackName"""
        track = {
            "enabled": True,
            "actions": [
                {
                    "frame": 0,
                    "duration": 30,
                    "enabled": True,
                    "parameters": {"_odin_type": "test"}
                }
            ]
        }

        errors = validate_track(track, total_duration=150)
        assert any("trackName" in e for e in errors)

    def test_empty_actions(self):
        """测试空的 actions 数组"""
        track = {
            "trackName": "Test Track",
            "enabled": True,
            "actions": []
        }

        errors = validate_track(track, total_duration=150)
        assert any("actions 数组为空" in e for e in errors)

    def test_invalid_frame(self):
        """测试无效的 frame"""
        track = {
            "trackName": "Test Track",
            "actions": [
                {
                    "frame": -1,  # 负数
                    "duration": 30,
                    "enabled": True,
                    "parameters": {"_odin_type": "test"}
                }
            ]
        }

        errors = validate_track(track, total_duration=150)
        assert any("frame 必须是非负整数" in e for e in errors)

    def test_invalid_duration(self):
        """测试无效的 duration"""
        track = {
            "trackName": "Test Track",
            "actions": [
                {
                    "frame": 0,
                    "duration": 0,  # 必须 >= 1
                    "enabled": True,
                    "parameters": {"_odin_type": "test"}
                }
            ]
        }

        errors = validate_track(track, total_duration=150)
        assert any("duration 必须是正整数" in e for e in errors)

    def test_exceeding_total_duration(self):
        """测试超出总时长"""
        track = {
            "trackName": "Test Track",
            "actions": [
                {
                    "frame": 100,
                    "duration": 60,  # 100 + 60 = 160 > 150
                    "enabled": True,
                    "parameters": {"_odin_type": "test"}
                }
            ]
        }

        errors = validate_track(track, total_duration=150)
        assert any("超出技能总时长" in e for e in errors)

    def test_missing_odin_type(self):
        """测试缺少 _odin_type"""
        track = {
            "trackName": "Test Track",
            "actions": [
                {
                    "frame": 0,
                    "duration": 30,
                    "enabled": True,
                    "parameters": {
                        "someParam": "value"  # 缺少 _odin_type
                    }
                }
            ]
        }

        errors = validate_track(track, total_duration=150)
        assert any("_odin_type" in e for e in errors)


# ==================== 辅助函数测试 ====================

class TestFormatActionSchemas:
    """测试 format_action_schemas_for_prompt 函数"""

    def test_empty_actions(self):
        """测试空 actions"""
        result = format_action_schemas_for_prompt([])
        assert result == "无特定 Action 参考"

    def test_format_actions(self):
        """测试格式化 actions"""
        actions = [
            {
                "action_name": "DamageAction",
                "action_type": "SkillSystem.Actions.DamageAction",
                "description": "造成伤害",
                "parameters": [
                    {"name": "damage", "type": "int", "defaultValue": "100"},
                    {"name": "damageType", "type": "DamageType", "defaultValue": "Physical"}
                ]
            }
        ]

        result = format_action_schemas_for_prompt(actions)

        assert "DamageAction" in result
        assert "damage" in result
        assert "int" in result


# ==================== 条件判断函数测试 ====================

class TestShouldFixTrack:
    """测试 should_fix_track 函数"""

    def test_no_errors_save(self):
        """测试无错误时保存"""
        state = {
            "current_track_errors": [],
            "track_retry_count": 0,
            "max_track_retries": 3
        }

        result = should_fix_track(state)
        assert result == "save"

    def test_has_errors_fix(self):
        """测试有错误且未达上限时修复"""
        state = {
            "current_track_errors": ["error1"],
            "track_retry_count": 1,
            "max_track_retries": 3
        }

        result = should_fix_track(state)
        assert result == "fix"

    def test_max_retries_skip(self):
        """测试达到最大重试次数时跳过"""
        state = {
            "current_track_errors": ["error1"],
            "track_retry_count": 3,
            "max_track_retries": 3
        }

        result = should_fix_track(state)
        assert result == "skip"


class TestShouldContinueTracks:
    """测试 should_continue_tracks 函数"""

    def test_more_tracks_continue(self):
        """测试还有未生成的 track 时继续"""
        state = {
            "current_track_index": 1,
            "track_plan": [
                {"trackName": "Track 1"},
                {"trackName": "Track 2"},
                {"trackName": "Track 3"}
            ]
        }

        result = should_continue_tracks(state)
        assert result == "continue"

    def test_all_tracks_done_assemble(self):
        """测试所有 track 已生成时进入组装"""
        state = {
            "current_track_index": 3,
            "track_plan": [
                {"trackName": "Track 1"},
                {"trackName": "Track 2"},
                {"trackName": "Track 3"}
            ]
        }

        result = should_continue_tracks(state)
        assert result == "assemble"


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
