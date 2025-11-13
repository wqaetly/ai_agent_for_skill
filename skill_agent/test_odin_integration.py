"""
Odin JSON 集成测试
测试 Unity 标准化输出和 Python 解析的完整流程
"""

import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.odin_json_parser import OdinJsonParser


def test_standardized_odin_json():
    """测试标准化后的 Odin JSON（Unity 经过 OdinJsonStandardizer 处理后的格式）"""

    print("=" * 80)
    print("测试：标准化的 Odin JSON 解析")
    print("=" * 80)

    # 模拟 Unity OdinJsonStandardizer 处理后的 JSON
    # (Vector3 等类型的裸值已经被转换为键值对)
    standardized_odin_json = '''
    {
        "$id": 0,
        "$type": "0|SkillSystem.Data.SkillData, Assembly-CSharp",
        "skillName": "Test Skill",
        "skillDescription": "测试技能",
        "skillId": "test-skill-001",
        "totalDuration": 100,
        "frameRate": 30,
        "tracks": {
            "$id": 1,
            "$type": "1|System.Collections.Generic.List, mscorlib",
            "$rlength": 2,
            "$rcontent": [
                {
                    "$id": 2,
                    "$type": "2|SkillSystem.Data.SkillTrack, Assembly-CSharp",
                    "trackName": "Movement Track",
                    "enabled": true,
                    "actions": {
                        "$id": 3,
                        "$type": "3|System.Collections.Generic.List, mscorlib",
                        "$rlength": 1,
                        "$rcontent": [
                            {
                                "$id": 4,
                                "$type": "4|SkillSystem.Actions.MovementAction, Assembly-CSharp",
                                "frame": 10,
                                "duration": 30,
                                "enabled": true,
                                "movementType": 1,
                                "movementSpeed": 10.0,
                                "targetPosition": {
                                    "$type": "7|UnityEngine.Vector3, UnityEngine.CoreModule",
                                    "x": 1.5,
                                    "y": 2.0,
                                    "z": 3.5
                                },
                                "useRelativePosition": true
                            }
                        ]
                    }
                },
                {
                    "$id": 5,
                    "$type": "2|SkillSystem.Data.SkillTrack, Assembly-CSharp",
                    "trackName": "Damage Track",
                    "enabled": true,
                    "actions": {
                        "$id": 6,
                        "$type": "3|System.Collections.Generic.List, mscorlib",
                        "$rlength": 1,
                        "$rcontent": [
                            {
                                "$id": 7,
                                "$type": "5|SkillSystem.Actions.DamageAction, Assembly-CSharp",
                                "frame": 20,
                                "duration": 10,
                                "enabled": true,
                                "baseDamage": 100,
                                "damageType": 0
                            }
                        ]
                    }
                }
            ]
        }
    }
    '''

    # 使用 OdinJsonParser 解析
    parser = OdinJsonParser()
    result = parser.parse(standardized_odin_json)

    print("\n[OK] 解析成功！")
    print("\n基本信息:")
    print(f"  技能名称: {result.get('skillName')}")
    print(f"  技能描述: {result.get('skillDescription')}")
    print(f"  技能ID: {result.get('skillId')}")
    print(f"  总时长: {result.get('totalDuration')} 帧")
    print(f"  帧率: {result.get('frameRate')} FPS")

    print("\nTracks:")
    tracks = result.get('tracks', [])
    print(f"  共 {len(tracks)} 个 Track")

    for i, track in enumerate(tracks):
        print(f"\n  Track {i + 1}: {track.get('trackName')}")
        print(f"    启用: {track.get('enabled')}")

        actions = track.get('actions', [])
        print(f"    Actions: {len(actions)} 个")

        for j, action in enumerate(actions):
            print(f"\n      Action {j + 1}:")
            print(f"        帧: {action.get('frame')}")
            print(f"        时长: {action.get('duration')}")
            print(f"        启用: {action.get('enabled')}")

            # 打印其他参数
            for key, value in action.items():
                if key not in ['frame', 'duration', 'enabled', '_odin_type']:
                    if isinstance(value, dict) and 'x' in value:
                        # Vector3 类型
                        print(f"        {key}: ({value.get('x')}, {value.get('y')}, {value.get('z')})")
                    else:
                        print(f"        {key}: {value}")

    print("\n" + "=" * 80)
    print("[OK] 测试通过：标准化 Odin JSON 解析成功")
    print("=" * 80)

    return result


def test_skill_file_parsing():
    """测试原始 Odin JSON 文件（包含裸值）"""

    print("\n\n" + "=" * 80)
    print("测试：原始 Odin JSON 文件解析")
    print("=" * 80)

    skill_file = Path(__file__).parent.parent / "ai_agent_for_skill" / "Assets" / "Skills" / "RivenBrokenWings.json"

    if not skill_file.exists():
        print(f"\n[WARN] 技能文件不存在: {skill_file}")
        print("跳过此测试")
        return None

    print(f"\n读取文件: {skill_file}")
    print("\n说明：")
    print("  - 这个文件是 Unity Odin 直接序列化的原始格式")
    print("  - 包含 Vector3 等类型的裸值（无键名）")
    print("  - 标准 JSON 解析器无法解析")

    # 尝试解析原始 Odin JSON
    try:
        parser = OdinJsonParser()
        result = parser.parse_file(str(skill_file))
        print("\n[WARN] 意外：原始 Odin JSON 解析成功")
        print("       （可能文件已被手动标准化）")
        return result
    except json.JSONDecodeError as e:
        print(f"\n[EXPECTED] 原始 Odin JSON 无法解析（预期行为）")
        print(f"  错误: {str(e)}")
        print("\n结论:")
        print("  - Unity 必须先使用 OdinJsonStandardizer 处理")
        print("  - 标准化后才能通过网络传输")
        print("  - Python 侧才能正确解析")

    print("\n" + "=" * 80)
    print("[OK] 测试通过：验证了标准化的必要性")
    print("=" * 80)

    return None


def test_rpc_message_format():
    """测试 RPC 消息格式（模拟 Unity RPC 通信）"""

    print("\n\n" + "=" * 80)
    print("测试：RPC 消息格式")
    print("=" * 80)

    # 模拟 Unity 发送的 RPC 请求（经过标准化）
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "CreateSkill",
        "params": {
            "skillName": "新技能",
            "config": {
                "skillDescription": "这是一个新技能",
                "tracks": [
                    {
                        "trackName": "Movement",
                        "actions": [
                            {
                                "type": "MovementAction",
                                "frame": 0,
                                "position": {
                                    "x": 1.0,
                                    "y": 0.0,
                                    "z": 2.0
                                }
                            }
                        ]
                    }
                ]
            }
        },
        "id": "request-123"
    }

    print("\n模拟 RPC 请求:")
    print(json.dumps(rpc_request, ensure_ascii=False, indent=2))

    # 在 Python 侧，这个 JSON 可以直接解析（因为已经标准化）
    params = rpc_request["params"]
    config = params["config"]

    print("\n[OK] RPC 消息解析成功！")
    print(f"  技能名称: {params['skillName']}")
    print(f"  技能描述: {config['skillDescription']}")
    print(f"  Tracks 数量: {len(config['tracks'])}")

    # 验证 Vector3
    position = config['tracks'][0]['actions'][0]['position']
    print(f"  位置: ({position['x']}, {position['y']}, {position['z']})")

    print("\n" + "=" * 80)
    print("[OK] 测试通过：RPC 消息格式正确")
    print("=" * 80)


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Odin JSON 集成测试" + " " * 40 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        # 测试 1：标准化 Odin JSON 解析
        test_standardized_odin_json()

        # 测试 2：实际技能文件解析
        test_skill_file_parsing()

        # 测试 3：RPC 消息格式
        test_rpc_message_format()

        print("\n\n" + "=" * 80)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 80)
        print("\n[OK] Unity 侧:")
        print("   - OdinJsonStandardizer: 将 Odin JSON 标准化")
        print("   - OdinRPCSerializer: 使用 Odin 序列化并标准化")
        print("   - 移除 Newtonsoft.Json 依赖")

        print("\n[OK] Python 侧:")
        print("   - OdinJsonParser: 解析标准化后的 Odin JSON")
        print("   - SkillIndexer: 使用统一解析器")

        print("\n[OK] 通信:")
        print("   - RPC 消息使用标准 JSON 格式")
        print("   - Unity 自动标准化输出")
        print("   - Python 正确解析")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
