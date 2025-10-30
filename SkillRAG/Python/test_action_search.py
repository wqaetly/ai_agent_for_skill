"""
Action搜索测试脚本
测试Action向量搜索功能
"""

import yaml
import logging
from rag_engine import RAGEngine


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def test_action_search():
    """测试Action搜索功能"""
    print("=" * 70)
    print("Action搜索功能测试")
    print("=" * 70)
    print()

    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 初始化RAG引擎
    print("初始化RAG引擎...")
    engine = RAGEngine(config)

    # 测试查询列表
    test_queries = [
        ("造成伤害", 3),
        ("移动角色", 3),
        ("播放动画", 3),
        ("治疗单位", 3),
        ("添加增益效果", 3),
        ("召唤单位", 2),
        ("碰撞检测", 2),
        ("播放音效", 2),
    ]

    print()
    print("开始测试搜索...")
    print()

    for query, top_k in test_queries:
        print("-" * 70)
        print(f"查询: {query}")
        print("-" * 70)

        # 执行搜索
        results = engine.search_actions(
            query=query,
            top_k=top_k,
            return_details=False
        )

        if results:
            for i, action in enumerate(results, 1):
                print(f"{i}. {action['display_name']} ({action['type_name']})")
                print(f"   分类: {action['category']}")
                print(f"   相似度: {action['similarity']:.4f}")
        else:
            print("  未找到匹配的Action")

        print()

    # 测试按分类搜索
    print("=" * 70)
    print("按分类搜索测试")
    print("=" * 70)
    print()

    categories = engine.get_action_categories()
    print(f"可用分类: {', '.join(categories)}")
    print()

    # 测试获取分类下的Action
    if categories:
        test_category = categories[0]
        print(f"获取 '{test_category}' 分类下的Action:")
        print("-" * 70)

        actions = engine.get_actions_by_category(test_category)
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action.get('displayName', action.get('typeName'))}")
        print()

    # 测试获取详细信息
    print("=" * 70)
    print("获取Action详细信息测试")
    print("=" * 70)
    print()

    test_action_type = "DamageAction"
    print(f"获取 {test_action_type} 的详细信息:")
    print("-" * 70)

    action_details = engine.get_action_by_type(test_action_type)
    if action_details:
        print(f"类型名: {action_details.get('typeName')}")
        print(f"显示名: {action_details.get('displayName')}")
        print(f"分类: {action_details.get('category')}")
        print(f"命名空间: {action_details.get('namespaceName')}")
        print(f"参数数量: {len(action_details.get('parameters', []))}")
        print()
        print("参数列表:")
        for i, param in enumerate(action_details.get('parameters', [])[:5], 1):
            print(f"  {i}. {param.get('label', param.get('name'))}")
            print(f"     类型: {param.get('type')}")
            print(f"     默认值: {param.get('defaultValue')}")
            if param.get('infoBox'):
                print(f"     说明: {param.get('infoBox')}")
            print()
    else:
        print(f"未找到 {test_action_type}")

    print("=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    setup_logging()
    test_action_search()
