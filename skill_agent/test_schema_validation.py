"""
测试Pydantic Schema验证
验证OdinSkillSchema能否正确解析现有技能文件
"""

import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from orchestration.schemas import OdinSkillSchema, SkillTrack, SkillAction
from core.odin_json_parser import parse_odin_json_file


def test_schema_with_existing_skill():
    """测试Schema能否解析现有技能"""

    # 测试文件路径
    skill_file = Path(__file__).parent.parent / "ai_agent_for_skill" / "Assets" / "Skills" / "FlameShockwave.json"

    if not skill_file.exists():
        print(f"❌ 技能文件不存在: {skill_file}")
        return False

    print(f"📂 读取技能文件: {skill_file.name}")

    try:
        # 1. 使用 odin_json_parser 解析
        parsed_data = parse_odin_json_file(str(skill_file))
        print("✅ Odin JSON 解析成功")

        # 2. 转换为JSON字符串
        json_str = json.dumps(parsed_data, ensure_ascii=False, indent=2)

        # 3. 使用 Pydantic Schema 验证（使用Pydantic V2 API）
        skill_schema = OdinSkillSchema.model_validate_json(json_str)
        print("[OK] Pydantic Schema 验证成功")

        # 4. 输出验证结果
        print(f"\n📊 技能信息:")
        print(f"  名称: {skill_schema.skillName}")
        print(f"  ID: {skill_schema.skillId}")
        print(f"  描述: {skill_schema.skillDescription}")
        print(f"  总时长: {skill_schema.totalDuration} 帧")
        print(f"  帧率: {skill_schema.frameRate} fps")
        print(f"  轨道数量: {len(skill_schema.tracks)}")

        for i, track in enumerate(skill_schema.tracks):
            print(f"\n  轨道 {i+1}: {track.trackName}")
            print(f"    - 启用: {track.enabled}")
            print(f"    - Action数量: {len(track.actions)}")
            for j, action in enumerate(track.actions[:2]):  # 只显示前2个
                print(f"      Action {j+1}: frame={action.frame}, duration={action.duration}")
                odin_type = action.parameters.get('_odin_type', 'N/A')
                print(f"        类型: {odin_type}")

        return True

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_generation():
    """测试从零创建Schema"""

    print("\n" + "="*60)
    print("测试手动创建Skill Schema")
    print("="*60)

    try:
        # 创建一个简单的技能
        skill = OdinSkillSchema(
            skillName="测试技能",
            skillId="test-skill-001",
            skillDescription="这是一个用于测试Schema的技能，包含基本的动画和特效",
            totalDuration=90,
            frameRate=30,
            tracks=[
                SkillTrack(
                    trackName="Animation Track",
                    enabled=True,
                    actions=[
                        SkillAction(
                            frame=0,
                            duration=30,
                            enabled=True,
                            parameters={
                                "_odin_type": "4|SkillSystem.Actions.AnimationAction, Assembly-CSharp",
                                "animationClipName": "Attack",
                                "normalizedTime": 0,
                                "crossFadeDuration": 0.2,
                                "animationLayer": 0
                            }
                        )
                    ]
                ),
                SkillTrack(
                    trackName="Effect Track",
                    enabled=True,
                    actions=[
                        SkillAction(
                            frame=15,
                            duration=1,
                            enabled=True,
                            parameters={
                                "_odin_type": "7|SkillSystem.Actions.DamageAction, Assembly-CSharp",
                                "damage": 100,
                                "damageType": 0,
                                "radius": 3.0
                            }
                        )
                    ]
                )
            ]
        )

        print("✅ Schema创建成功")

        # 转换为JSON（使用Pydantic V2 API）
        json_output = skill.model_dump_json(indent=2)
        print(f"\n[JSON] 生成的JSON:\n{json_output[:500]}...")

        # 验证能否重新解析（使用Pydantic V2 API）
        reparsed = OdinSkillSchema.model_validate_json(json_output)
        print("[OK] JSON重新解析成功")

        return True

    except Exception as e:
        print(f"❌ Schema创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 设置UTF-8输出（Windows兼容性）
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("[TEST] 开始测试 Pydantic Schema")
    print("="*60)

    # 测试1：解析现有技能
    test1_passed = test_schema_with_existing_skill()

    # 测试2：手动创建Schema
    test2_passed = test_schema_generation()

    print("\n" + "="*60)
    print("[RESULT] 测试结果:")
    print(f"  测试1（解析现有技能）: {'[PASS]' if test1_passed else '[FAIL]'}")
    print(f"  测试2（创建Schema）: {'[PASS]' if test2_passed else '[FAIL]'}")

    if test1_passed and test2_passed:
        print("\n[SUCCESS] 所有测试通过！Schema定义正确。")
        sys.exit(0)
    else:
        print("\n[WARNING] 部分测试失败，请检查Schema定义。")
        sys.exit(1)
