"""
REQ-03 结构化查询演示脚本
展示核心功能的使用方法
"""

import sys
import io

# Windows UTF-8编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from structured_query_engine import StructuredQueryEngine, query_skills
from fine_grained_indexer import build_fine_grained_index


def demo_1_build_index():
    """演示1：构建细粒度索引"""
    print("=" * 80)
    print("演示1：构建细粒度索引")
    print("=" * 80)

    stats = build_fine_grained_index(force_rebuild=True)

    print(f"✓ 索引构建完成")
    print(f"  - 总文件数: {stats['total_files']}")
    print(f"  - 已索引: {stats['indexed_files']}")
    print(f"  - 总Action数: {stats['total_actions']}")
    print()


def demo_2_basic_query():
    """演示2：基础查询"""
    print("=" * 80)
    print("演示2：基础查询")
    print("=" * 80)

    # 查询所有DamageAction
    result = query_skills("DamageAction")

    print(f"查询: DamageAction")
    print(f"✓ 找到 {result['total_matches']} 个匹配")
    print()

    if result['results']:
        print("前3个结果:")
        for i, action in enumerate(result['results'][:3], 1):
            print(f"\n{i}. 技能: {action['skill_name']}")
            print(f"   轨道: {action['track_name']}")
            print(f"   帧位置: {action['frame']}")
            print(f"   摘要: {action['summary']}")
    print()


def demo_3_complex_query():
    """演示3：复杂条件查询"""
    print("=" * 80)
    print("演示3：复杂条件查询")
    print("=" * 80)

    queries = [
        "DamageAction where baseDamage > 100",
        "animationClipName contains 'Cast'",
        "MovementAction where speed > 5",
    ]

    for query in queries:
        result = query_skills(query, limit=5)
        print(f"✓ {query}")
        print(f"  匹配数: {result['total_matches']}")
        print(f"  查询时间: {result['query_time_ms']}ms")
        print()


def demo_4_statistics():
    """演示4：统计分析"""
    print("=" * 80)
    print("演示4：统计分析")
    print("=" * 80)

    engine = StructuredQueryEngine()

    # 全局统计
    stats = engine.get_statistics(group_by="action_type")

    print(f"总Action数: {stats['total_actions']}")
    print(f"Action类型数: {len(stats['groups'])}")
    print()

    print("各类型统计（前5个）:")
    for action_type, data in list(stats['groups'].items())[:5]:
        print(f"\n{action_type}:")
        print(f"  数量: {data['count']}")

        # 显示参数统计
        param_keys = [k for k in data.keys() if k.startswith('avg_')]
        for key in param_keys[:2]:
            param_name = key.replace('avg_', '')
            avg_val = data.get(f'avg_{param_name}')
            min_val = data.get(f'min_{param_name}')
            max_val = data.get(f'max_{param_name}')

            if avg_val is not None:
                print(f"  {param_name}: min={min_val}, avg={avg_val}, max={max_val}")
    print()


def demo_5_action_detail():
    """演示5：获取Action详细信息"""
    print("=" * 80)
    print("演示5：获取Action详细信息")
    print("=" * 80)

    engine = StructuredQueryEngine()

    # 先查询找到一个Action
    result = engine.query("AnimationAction", limit=1)

    if result['results']:
        action = result['results'][0]

        print(f"选中Action:")
        print(f"  技能: {action['skill_name']}")
        print(f"  轨道: {action['track_name']}")
        print(f"  类型: {action['action_type']}")
        print()

        # 获取详细信息
        detail = engine.get_action_detail(
            skill_file=action['skill_file'],
            json_path=action['json_path']
        )

        if detail:
            print(f"详细信息:")
            print(f"  数据大小: {detail['size_bytes']} bytes")
            print(f"  上下文: {detail.get('context', {})}")
            print()

            import json
            print("完整JSON数据:")
            print(json.dumps(detail['data'], indent=2, ensure_ascii=False)[:300] + "...")
    else:
        print("没有找到AnimationAction")
    print()


def demo_6_cache_performance():
    """演示6：缓存性能"""
    print("=" * 80)
    print("演示6：缓存性能")
    print("=" * 80)

    engine = StructuredQueryEngine()

    # 清空缓存
    engine.clear_cache()

    query = "DamageAction"

    # 第一次查询（未命中缓存）
    result1 = engine.query(query)
    time1 = result1["query_time_ms"]
    cache_hit1 = result1.get("cache_hit", False)

    # 第二次查询（命中缓存）
    result2 = engine.query(query)
    time2 = result2["query_time_ms"]
    cache_hit2 = result2.get("cache_hit", False)

    print(f"查询: {query}")
    print(f"第一次（未命中缓存）: {time1:.2f}ms")
    print(f"第二次（命中缓存）: {time2:.2f}ms")
    print()

    # 缓存统计
    cache_stats = engine.get_cache_stats()
    print("缓存统计:")
    print(f"  查询缓存命中率: {cache_stats['query_cache']['hit_rate']:.2%}")
    print(f"  缓存大小: {cache_stats['query_cache']['size']}/{cache_stats['query_cache']['max_size']}")
    print()


def main():
    """运行所有演示"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "REQ-03 结构化查询功能演示" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        demo_1_build_index()
        demo_2_basic_query()
        demo_3_complex_query()
        demo_4_statistics()
        demo_5_action_detail()
        demo_6_cache_performance()

        print("=" * 80)
        print("✓ 所有演示完成！")
        print()
        print("更多功能请参考:")
        print("  - docs/mcp_requirements/REQ03_QuickStart.md")
        print("  - docs/mcp_requirements/REQ03_Implementation.md")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
