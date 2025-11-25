"""
渐进式技能生成 - 阶段1（骨架生成）单元测试
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

# 添加项目路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.schemas import SkillSkeletonSchema, TrackPlanItem
from orchestration.nodes.progressive_skill_nodes import (
    ProgressiveSkillGenerationState,
    validate_skeleton,
    skeleton_generator_node,
    format_similar_skills,
    should_continue_to_track_generation,
)


# ==================== Schema 测试 ====================

class TestSkillSkeletonSchema:
    """测试 SkillSkeletonSchema"""

    def test_valid_skeleton(self):
        """测试有效的骨架数据"""
        data = {
            "skillName": "冰封之怒",
            "skillId": "frozen-rage-001",
            "skillDescription": "释放冰霜之力，冻结范围内敌人并造成持续伤害，是一个强大的控制技能",
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
                }
            ]
        }

        skeleton = SkillSkeletonSchema.model_validate(data)

        assert skeleton.skillName == "冰封之怒"
        assert skeleton.skillId == "frozen-rage-001"
        assert skeleton.totalDuration == 180
        assert len(skeleton.trackPlan) == 2
        assert skeleton.trackPlan[0].trackName == "Animation Track"

    def test_invalid_skill_id_format(self):
        """测试无效的 skillId 格式"""
        data = {
            "skillName": "测试技能",
            "skillId": "Invalid ID With Spaces",  # 包含空格和大写
            "skillDescription": "这是一个测试技能，用于验证 Schema",
            "totalDuration": 60,
            "trackPlan": [
                {
                    "trackName": "Animation Track",
                    "purpose": "播放测试动画",
                    "estimatedActions": 1,
                    "priority": 1
                }
            ]
        }

        with pytest.raises(ValidationError):
            SkillSkeletonSchema.model_validate(data)

    def test_total_duration_too_short(self):
        """测试 totalDuration 过短"""
        data = {
            "skillName": "测试技能",
            "skillId": "test-001",
            "skillDescription": "这是一个测试技能，用于验证 Schema",
            "totalDuration": 10,  # 小于 30
            "trackPlan": [
                {
                    "trackName": "Animation Track",
                    "purpose": "播放测试动画",
                    "estimatedActions": 1,
                    "priority": 1
                }
            ]
        }

        with pytest.raises(ValidationError):
            SkillSkeletonSchema.model_validate(data)

    def test_duplicate_track_names(self):
        """测试重复的 trackName"""
        data = {
            "skillName": "测试技能",
            "skillId": "test-001",
            "skillDescription": "这是一个测试技能，用于验证 Schema",
            "totalDuration": 60,
            "trackPlan": [
                {
                    "trackName": "Animation Track",
                    "purpose": "播放测试动画第一个",
                    "estimatedActions": 1,
                    "priority": 1
                },
                {
                    "trackName": "Animation Track",  # 重复
                    "purpose": "播放测试动画第二个",
                    "estimatedActions": 1,
                    "priority": 2
                }
            ]
        }

        with pytest.raises(ValidationError):
            SkillSkeletonSchema.model_validate(data)


# ==================== 验证函数测试 ====================

class TestValidateSkeleton:
    """测试 validate_skeleton 函数"""

    def test_valid_skeleton(self):
        """测试有效骨架"""
        skeleton = {
            "skillName": "测试技能",
            "skillId": "test-001",
            "totalDuration": 60,
            "trackPlan": [
                {
                    "trackName": "Animation Track",
                    "purpose": "播放动画",
                    "estimatedActions": 2,
                    "priority": 1
                }
            ]
        }

        errors = validate_skeleton(skeleton)
        assert errors == []

    def test_missing_skill_name(self):
        """测试缺少 skillName"""
        skeleton = {
            "skillId": "test-001",
            "totalDuration": 60,
            "trackPlan": [{"trackName": "Test", "purpose": "test", "estimatedActions": 1}]
        }

        errors = validate_skeleton(skeleton)
        assert any("skillName" in e for e in errors)

    def test_invalid_total_duration(self):
        """测试无效的 totalDuration"""
        skeleton = {
            "skillName": "测试",
            "skillId": "test-001",
            "totalDuration": 20,  # 小于 30
            "trackPlan": [{"trackName": "Test", "purpose": "test", "estimatedActions": 1}]
        }

        errors = validate_skeleton(skeleton)
        assert any("totalDuration" in e for e in errors)

    def test_empty_track_plan(self):
        """测试空的 trackPlan"""
        skeleton = {
            "skillName": "测试",
            "skillId": "test-001",
            "totalDuration": 60,
            "trackPlan": []
        }

        errors = validate_skeleton(skeleton)
        assert any("trackPlan" in e for e in errors)

    def test_duplicate_track_name_in_plan(self):
        """测试 trackPlan 中重复的 trackName"""
        skeleton = {
            "skillName": "测试",
            "skillId": "test-001",
            "totalDuration": 60,
            "trackPlan": [
                {"trackName": "Animation Track", "purpose": "test1", "estimatedActions": 1},
                {"trackName": "Animation Track", "purpose": "test2", "estimatedActions": 1}  # 重复
            ]
        }

        errors = validate_skeleton(skeleton)
        assert any("重复" in e for e in errors)

    def test_invalid_estimated_actions(self):
        """测试无效的 estimatedActions"""
        skeleton = {
            "skillName": "测试",
            "skillId": "test-001",
            "totalDuration": 60,
            "trackPlan": [
                {"trackName": "Animation Track", "purpose": "test", "estimatedActions": 25}  # 超过 20
            ]
        }

        errors = validate_skeleton(skeleton)
        assert any("estimatedActions" in e for e in errors)


# ==================== 辅助函数测试 ====================

class TestFormatSimilarSkills:
    """测试 format_similar_skills 函数"""

    def test_empty_skills(self):
        """测试空技能列表"""
        result = format_similar_skills([])
        assert result == "无参考技能"

    def test_format_skills(self):
        """测试格式化技能"""
        skills = [
            {
                "skill_name": "火焰冲击",
                "skill_data": {
                    "totalDuration": 150,
                    "tracks": [
                        {"trackName": "Animation Track", "actions": [1, 2]},
                        {"trackName": "Effect Track", "actions": [1]}
                    ]
                }
            }
        ]

        result = format_similar_skills(skills)

        assert "火焰冲击" in result
        assert "Animation Track" in result
        assert "150" in result


# ==================== 条件判断函数测试 ====================

class TestShouldContinueToTrackGeneration:
    """测试 should_continue_to_track_generation 函数"""

    def test_no_errors_continue(self):
        """测试无错误时继续"""
        state = {
            "skeleton_validation_errors": []
        }

        result = should_continue_to_track_generation(state)
        assert result == "generate_tracks"

    def test_has_errors_fail(self):
        """测试有错误时失败"""
        state = {
            "skeleton_validation_errors": ["error1", "error2"]
        }

        result = should_continue_to_track_generation(state)
        assert result == "skeleton_failed"


# ==================== 集成测试（需要 Mock LLM）====================

class TestSkeletonGeneratorNode:
    """测试 skeleton_generator_node（使用 Mock）"""

    @pytest.mark.skip(reason="需要完整的 Mock 环境配置，在阶段2完善")
    @patch('orchestration.nodes.skill_nodes.get_llm')
    @patch('orchestration.prompts.prompt_manager.get_prompt_manager')
    def test_successful_generation(self, mock_prompt_mgr, mock_get_llm):
        """测试成功生成骨架（集成测试，需要 Mock LLM）"""
        # 准备 Mock 响应
        mock_skeleton = SkillSkeletonSchema(
            skillName="测试技能",
            skillId="test-skill-001",
            skillDescription="这是一个测试技能，用于单元测试验证，包含多种攻击效果和特效展示",
            totalDuration=120,
            frameRate=30,
            trackPlan=[
                TrackPlanItem(
                    trackName="Animation Track",
                    purpose="播放攻击动画和特效动画，包含前摇和后摇",
                    estimatedActions=2,
                    priority=1
                ),
                TrackPlanItem(
                    trackName="Effect Track",
                    purpose="造成伤害和施加效果，包含范围检测和伤害计算",
                    estimatedActions=3,
                    priority=2
                )
            ]
        )

        # 配置 Mock LLM
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.__or__ = MagicMock(return_value=MagicMock())
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_get_llm.return_value = mock_llm

        # 配置 Mock Prompt
        mock_prompt = MagicMock()
        mock_prompt.__or__ = MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=mock_skeleton)))
        mock_prompt_mgr.return_value.get_prompt.return_value = mock_prompt

        # 构建测试状态
        state = {
            "requirement": "生成一个简单的近战攻击技能",
            "similar_skills": []
        }

        # 执行测试
        result = skeleton_generator_node(state)

        # 验证结果
        assert "skill_skeleton" in result
        assert "track_plan" in result
        assert "skeleton_validation_errors" in result
        assert result["current_track_index"] == 0
        assert result["generated_tracks"] == []


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
