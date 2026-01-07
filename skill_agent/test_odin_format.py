"""
测试Odin序列化格式
验证生成的JSON是否能被Unity正确解析
"""
import json
import sys
sys.path.insert(0, '.')

from core.odin_json_parser import serialize_to_odin, serialize_to_odin_string, OdinJsonSerializer

# 测试数据（包含Vector3）
test_skill = {
    "skillName": "测试技能",
    "skillId": "test-skill-001",
    "skillDescription": "测试Vector3序列化",
    "totalDuration": 120,
    "frameRate": 30,
    "tracks": [
        {
            "trackName": "Movement Track",
            "enabled": True,
            "actions": [
                {
                    "frame": 0,
                    "duration": 30,
                    "enabled": True,
                    "parameters": {
                        "_odin_type": "SkillSystem.Actions.MovementAction, Assembly-CSharp",
                        "movementType": 2,
                        "direction": {"x": 0, "y": 0, "z": 1},
                        "speed": 8.0,
                        "distance": 4.0
                    }
                }
            ]
        }
    ]
}

# 使用新的Odin JSON编码器
print("=== Odin JSON 输出 ===")
odin_string = serialize_to_odin_string(test_skill, indent=4)
print(odin_string)

# 检查Vector3格式是否正确
print("\n=== 格式验证 ===")
# 检查是否包含裸数组索引格式
if '"$type": "3|UnityEngine.Vector3' in odin_string and '0,\n' in odin_string:
    print("[OK] Vector3 使用裸数组索引格式")
else:
    print("[FAIL] Vector3 格式可能不正确")

# 检查是否不包含 "0": 这种字符串键格式
if '"0":' not in odin_string and '"1":' not in odin_string:
    print("[OK] 没有使用字符串键格式")
else:
    print("[FAIL] 仍然使用字符串键格式")

# 对比Unity原始格式
print("\n=== Unity期望格式示例 ===")
print('''
"direction": {
    "$type": "7|UnityEngine.Vector3, UnityEngine.CoreModule",
    0,
    0,
    1
}
''')
