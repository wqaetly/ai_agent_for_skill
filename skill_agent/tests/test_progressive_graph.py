"""
渐进式技能生成 Graph 集成测试
测试三阶段生成流程：骨架生成 → Track 生成循环 → 技能组装
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.graphs.progressive_skill_generation import (
    build_progressive_skill_generation_graph,
    get_progressive_skill_generation_graph,
)
from orchestration.nodes.progressive_skill_nodes import (
    ProgressiveSkillGenerationState,
    validate_skeleton,
    validate_track,
    validate_complete_skill,
    skill_assembler_node,
    finalize_progressive_node,
    should_finalize_or_fail,
)


class TestProgressiveGraphStructure:
    """测试图结构是否正确构建"""

    def test_graph_builds_successfully(self):
        """测试图能够成功构建"""
        graph = build_progressive_skill_generation_graph()
        assert graph is not None

    def test_singleton_pattern(self):
        """测试单例模式正常工作"""
        graph1 = get_progressive_skill_generation_graph()
        graph2 = get_progressive_skill_generation_graph()
        assert graph1 is graph2

    def test_graph_has_required_nodes(self):
        """测试图包含所有必要节点"""
        graph = get_progressive_skill_generation_graph()
        # 通过 mermaid 输出验证节点存在
        mermaid = graph.get_graph().draw_mermaid()

        assert "skeleton_generator" in mermaid
        assert "track_action_generator" in mermaid
        assert "track_validator" in mermaid
        assert "track_fixer" in mermaid
        assert "track_saver" in mermaid
        assert "skill_assembler" in mermaid
        assert "finalize" in mermaid


class TestSkillAssemblerNode:
    """测试技能组装节点"""

    def test_assembler_with_valid_data(self):
        """测试有效数据的组装"""
        state = {
            "skill_skeleton": {
                "skillName": "火焰冲击",
                "skillId": "flame-strike-001",
                "skillDescription": "释放火焰冲击波，造成大范围伤害并施加燃烧效果。",
                "totalDuration": 150,
                "frameRate": 30,
            },
            "generated_tracks": [
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
                            },
                        }
                    ],
                },
                {
                    "trackName": "Effect Track",
                    "enabled": True,
                    "actions": [
                        {
                            "frame": 10,
                            "duration": 50,
                            "enabled": True,
                            "parameters": {
                                "_odin_type": "5|SkillSystem.Actions.SpawnEffectAction, Assembly-CSharp",
                                "effectPrefab": "FireWave",
                            },
                        }
                    ],
                },
            ],
        }

        result = skill_assembler_node(state)

        assert "assembled_skill" in result
        assert "final_validation_errors" in result
        assert result["final_validation_errors"] == []

        skill = result["assembled_skill"]
        assert skill["skillName"] == "火焰冲击"
        assert skill["skillId"] == "flame-strike-001"
        assert len(skill["tracks"]) == 2

    def test_assembler_with_empty_tracks(self):
        """测试空轨道的组装"""
        state = {
            "skill_skeleton": {
                "skillName": "测试技能",
                "skillId": "test-001",
                "skillDescription": "测试技能描述",
                "totalDuration": 100,
                "frameRate": 30,
            },
            "generated_tracks": [],
        }

        result = skill_assembler_node(state)

        assert "final_validation_errors" in result
        assert len(result["final_validation_errors"]) > 0
        assert "tracks 不能为空" in result["final_validation_errors"][0]


class TestValidateCompleteSkill:
    """测试完整技能验证函数"""

    def test_valid_skill(self):
        """测试有效技能验证通过"""
        skill = {
            "skillName": "测试技能",
            "skillId": "test-skill-001",
            "totalDuration": 150,
            "tracks": [
                {
                    "trackName": "Animation Track",
                    "actions": [
                        {"frame": 0, "duration": 30}
                    ]
                }
            ]
        }

        errors = validate_complete_skill(skill)
        assert errors == []

    def test_missing_skill_name(self):
        """测试缺少技能名称"""
        skill = {
            "skillId": "test-001",
            "totalDuration": 100,
            "tracks": [{"trackName": "Test", "actions": []}]
        }

        errors = validate_complete_skill(skill)
        assert any("skillName" in e for e in errors)

    def test_action_exceeds_duration(self):
        """测试 action 超出总时长"""
        skill = {
            "skillName": "测试技能",
            "skillId": "test-001",
            "totalDuration": 100,
            "tracks": [
                {
                    "trackName": "Test Track",
                    "actions": [
                        {"frame": 80, "duration": 50}  # 结束帧 130 > 100
                    ]
                }
            ]
        }

        errors = validate_complete_skill(skill)
        assert any("超出" in e for e in errors)


class TestFinalizeProgressiveNode:
    """测试最终化节点"""

    def test_finalize_success(self):
        """测试成功时的最终化"""
        state = {
            "assembled_skill": {
                "skillName": "成功技能",
                "skillId": "success-001",
                "tracks": [{"trackName": "Test", "actions": []}]
            },
            "final_validation_errors": []
        }

        result = finalize_progressive_node(state)

        assert "final_result" in result
        assert result["is_valid"] is True
        assert result["final_result"]["skillName"] == "成功技能"

    def test_finalize_with_errors(self):
        """测试有错误时的最终化"""
        state = {
            "assembled_skill": {
                "skillName": "有问题技能",
                "skillId": "error-001",
                "tracks": []
            },
            "final_validation_errors": ["tracks 不能为空"]
        }

        result = finalize_progressive_node(state)

        assert "final_result" in result
        assert result["is_valid"] is False


class TestShouldFinalizeOrFail:
    """测试最终化条件判断"""

    def test_finalize_with_valid_skill(self):
        """测试有效技能进入最终化"""
        state = {
            "assembled_skill": {
                "skillName": "有效技能",
                "tracks": [{"trackName": "Test", "actions": []}]
            },
            "final_validation_errors": []
        }

        result = should_finalize_or_fail(state)
        assert result == "finalize"

    def test_finalize_with_errors_but_has_result(self):
        """测试有错误但有结果时仍进入最终化"""
        state = {
            "assembled_skill": {
                "skillName": "有问题技能",
                "tracks": [{"trackName": "Test", "actions": []}]
            },
            "final_validation_errors": ["某个警告"]
        }

        result = should_finalize_or_fail(state)
        assert result == "finalize"

    def test_failed_with_empty_result(self):
        """测试空结果时失败"""
        state = {
            "assembled_skill": {},
            "final_validation_errors": []
        }

        result = should_finalize_or_fail(state)
        assert result == "failed"

    def test_failed_with_no_tracks(self):
        """测试无轨道时失败"""
        state = {
            "assembled_skill": {
                "skillName": "无轨道技能",
                "tracks": []
            },
            "final_validation_errors": []
        }

        result = should_finalize_or_fail(state)
        assert result == "failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
