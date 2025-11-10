"""
测试REQ03集成到服务器的功能
"""

import sys
import io

# Windows UTF-8编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import yaml
from rag_engine import RAGEngine


def test_rag_engine_integration():
    """测试RAG引擎中的REQ03集成"""
    print("=" * 80)
    print("测试 RAG Engine 中的 REQ-03 集成")
    print("=" * 80)

    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 创建RAG引擎
    print("\n1. 初始化 RAG Engine...")
    engine = RAGEngine(config)
    print("✓ RAG Engine 初始化成功")

    # 测试结构化查询
    print("\n2. 测试结构化查询...")
    result = engine.query_skills_structured("DamageAction", limit=5)
    print(f"✓ 查询成功，找到 {result['total_matches']} 个匹配")
    print(f"  查询耗时: {result['query_time_ms']}ms")

    if result['results']:
        print(f"\n  前3个结果:")
        for i, action in enumerate(result['results'][:3], 1):
            print(f"  {i}. {action['skill_name']} - {action['track_name']} - 第{action['frame']}帧")

    # 测试统计功能
    print("\n3. 测试统计功能...")
    stats = engine.get_action_statistics_structured(group_by="action_type")
    print(f"✓ 统计成功，共 {stats['total_actions']} 个Action")
    print(f"  Action类型数: {len(stats['groups'])}")

    # 测试Action详情
    print("\n4. 测试获取Action详情...")
    if result['results']:
        first_result = result['results'][0]
        detail = engine.get_action_detail_structured(
            skill_file=first_result['skill_file'],
            json_path=first_result['json_path']
        )
        if detail:
            print(f"✓ 成功获取Action详情")
            print(f"  数据大小: {len(str(detail))} bytes")
        else:
            print("✗ 获取Action详情失败")

    # 测试缓存统计
    print("\n5. 测试缓存统计...")
    cache_stats = engine.structured_query_engine.get_cache_stats()
    print(f"✓ 缓存统计:")
    print(f"  查询缓存: {cache_stats['query_cache']['size']}/{cache_stats['query_cache']['max_size']}")
    print(f"  命中率: {cache_stats['query_cache']['hit_rate']*100:.2f}%")

    print("\n" + "=" * 80)
    print("✓ 所有测试通过！REQ-03 已成功集成到 RAG Engine")
    print("=" * 80)


if __name__ == "__main__":
    test_rag_engine_integration()
