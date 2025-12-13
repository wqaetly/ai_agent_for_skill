"""
测试渐进式技能生成流程
用于诊断为什么生成停留在skeleton阶段
"""

import os
import sys
import json
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()


def test_skeleton_validation():
    """测试骨架验证函数"""
    from orchestration.nodes.progressive_skill_nodes import validate_skeleton

    # 使用实际生成的骨架数据
    skeleton = {
        "skillName": "火球术",
        "skillId": "fireball-001",
        "skillDescription": "释放一个火球，火球持续向目标点移动，并在移动过程中每秒对周围敌人造成魔法伤害",
        "totalDuration": 120,
        "frameRate": 30,
        "trackPlan": [
            {
                "trackName": "Animation Track",
                "purpose": "播放角色施法动画，包括施法前摇和释放火球的动作",
                "estimatedActions": 2,
                "priority": 1
            },
            {
                "trackName": "Effect Track",
                "purpose": "生成火球特效，设置伤害区域，并在移动过程中每秒触发魔法伤害",
                "estimatedActions": 3,
                "priority": 2
            },
            {
                "trackName": "Movement Track",
                "purpose": "控制火球从施法点向目标点的持续移动轨迹",
                "estimatedActions": 1,
                "priority": 3
            },
            {
                "trackName": "Audio Track",
                "purpose": "播放施法音效和火球移动过程中的音效",
                "estimatedActions": 2,
                "priority": 4
            }
        ]
    }

    errors = validate_skeleton(skeleton)
    print(f"\n=== Skeleton Validation Result ===")
    if errors:
        print(f"[FAIL] Validation failed, error count: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print("[PASS] Validation passed")

    return errors


def test_full_flow():
    """测试完整的渐进式生成流程"""
    from orchestration.graphs.progressive_skill_generation import (
        generate_skill_progressive_sync,
        get_progressive_skill_generation_graph
    )

    print("\n=== Test Full Progressive Generation Flow ===")

    requirement = "生成一个火球术技能，释放一个火球向目标移动，持续造成伤害"

    try:
        result = generate_skill_progressive_sync(
            requirement=requirement,
            similar_skills=[],
            max_track_retries=3
        )

        print("\n=== Generation Result ===")
        print(f"is_valid: {result.get('is_valid')}")
        print(f"skeleton_validation_errors: {result.get('skeleton_validation_errors')}")
        print(f"current_track_index: {result.get('current_track_index')}")
        print(f"generated_tracks count: {len(result.get('generated_tracks', []))}")
        print(f"final_validation_errors: {result.get('final_validation_errors')}")

        # 检查骨架
        skeleton = result.get('skill_skeleton', {})
        print(f"\nSkeleton info:")
        print(f"  skillName: {skeleton.get('skillName')}")
        print(f"  trackPlan count: {len(skeleton.get('trackPlan', []))}")

        # 检查组装后的技能
        assembled = result.get('assembled_skill', {})
        print(f"\nAssembled skill:")
        print(f"  tracks count: {len(assembled.get('tracks', []))}")

        # 检查final_result
        final = result.get('final_result', {})
        print(f"\nFinal result:")
        print(f"  tracks count: {len(final.get('tracks', []))}")

        # 保存完整结果供检查
        output_path = os.path.join(
            os.path.dirname(__file__),
            "Data", "generated_skills",
            "test_progressive_result.json"
        )
        with open(output_path, 'w', encoding='utf-8') as f:
            # 过滤掉 messages（可能包含不可序列化的对象）
            result_to_save = {k: v for k, v in result.items() if k != 'messages'}
            json.dump(result_to_save, f, ensure_ascii=False, indent=2)
        print(f"\nFull result saved to: {output_path}")

        return result

    except Exception as e:
        logger.error(f"[ERROR] Generation failed: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Progressive Skill Generation Flow Test")
    print("=" * 60)

    # 1. 先测试骨架验证
    errors = test_skeleton_validation()

    # 2. 如果验证通过，测试完整流程
    if not errors:
        test_full_flow()
    else:
        print("\nSkeleton validation failed, skip full flow test")
