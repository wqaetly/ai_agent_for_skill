"""
测试新的综合推荐逻辑
验证Action推荐是否同时考虑了语义匹配和使用频率
"""

import yaml
import logging
from rag_engine import RAGEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_recommendation(recommendation, index):
    """打印单个推荐结果"""
    print(f"\n{'='*60}")
    print(f"推荐 #{index}")
    print(f"{'='*60}")
    print(f"Action类型: {recommendation['action_type']}")
    print(f"显示名称: {recommendation.get('display_name', 'N/A')}")
    print(f"分类: {recommendation.get('category', 'N/A')}")
    print(f"功能描述: {recommendation.get('description', 'N/A')}")
    print(f"\n评分详情:")
    print(f"  - 综合得分: {recommendation['combined_score']:.3f} (0-1)")
    print(f"  - 语义相似度: {recommendation['semantic_similarity']:.3f}")
    print(f"  - 使用频率: {recommendation['frequency']} 次")

    if recommendation.get('examples'):
        print(f"\n参数示例:")
        for i, example in enumerate(recommendation['examples'][:2], 1):
            print(f"  示例 {i} (来自: {example['skill_name']})")
            if example.get('parameters'):
                for key, value in list(example['parameters'].items())[:3]:
                    print(f"    - {key}: {value}")


def test_recommendations():
    """测试不同场景的推荐结果"""

    # 加载配置
    print("加载配置...")
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 创建RAG引擎
    print("初始化RAG引擎...")
    engine = RAGEngine(config)

    # 测试场景
    test_cases = [
        {
            "context": "击飞",
            "description": "测试击飞效果推荐（应该推荐ControlAction，而不是AudioAction）",
            "expected_top": "ControlAction"
        },
        {
            "context": "造成伤害",
            "description": "测试伤害类Action推荐",
            "expected_top": "DamageAction"
        },
        {
            "context": "治疗恢复生命值",
            "description": "测试治疗类Action推荐",
            "expected_top": "HealAction"
        },
        {
            "context": "移动角色位置",
            "description": "测试移动类Action推荐",
            "expected_top": "MovementAction"
        },
        {
            "context": "施加眩晕控制效果",
            "description": "测试控制类Action推荐",
            "expected_top": "ControlAction"
        },
        {
            "context": "播放音效",
            "description": "测试音频类Action推荐",
            "expected_top": "AudioAction"
        }
    ]

    # 执行测试
    passed = 0
    failed = 0

    for test_case in test_cases:
        context = test_case['context']
        description = test_case['description']
        expected_top = test_case.get('expected_top')

        print(f"\n\n{'#'*80}")
        print(f"测试场景: {description}")
        print(f"查询上下文: \"{context}\"")
        if expected_top:
            print(f"期望第一推荐: {expected_top}")
        print(f"{'#'*80}")

        # 获取推荐
        try:
            recommendations = engine.recommend_actions(
                context=context,
                top_k=3
            )

            if recommendations:
                print(f"\n找到 {len(recommendations)} 个推荐结果")

                # 检查第一个推荐是否正确
                top_action = recommendations[0]['action_type']
                if expected_top:
                    if top_action == expected_top:
                        print(f"✅ 通过: 第一推荐 = {top_action}")
                        passed += 1
                    else:
                        print(f"❌ 失败: 第一推荐 = {top_action} (期望 {expected_top})")
                        failed += 1

                for i, rec in enumerate(recommendations, 1):
                    print_recommendation(rec, i)
            else:
                print("\n未找到推荐结果")
                if expected_top:
                    failed += 1

        except Exception as e:
            logger.error(f"推荐失败: {e}", exc_info=True)
            print(f"\n❌ 推荐失败: {e}")
            if expected_top:
                failed += 1

    # 显示配置权重
    print(f"\n\n{'='*80}")
    print("当前推荐权重配置:")
    print(f"{'='*80}")
    semantic_weight = config['rag'].get('recommend_semantic_weight', 0.6)
    usage_weight = config['rag'].get('recommend_usage_weight', 0.4)
    min_similarity = config['rag'].get('recommend_min_similarity', 0.0)
    print(f"  - 语义相似度权重: {semantic_weight:.1%}")
    print(f"  - 使用频率权重: {usage_weight:.1%}")
    print(f"  - 最低相似度阈值: {min_similarity:.2f}")
    print(f"\n说明: 调整这些参数可以改变推荐偏好")
    print(f"  - 提高semantic_weight: 更重视Action功能的语义匹配")
    print(f"  - 提高usage_weight: 更重视Action在实际技能中的使用频率")
    print(f"  - 提高min_similarity: 过滤更多语义不相关的Action")

    # 显示测试汇总
    print(f"\n\n{'='*80}")
    print("测试汇总:")
    print(f"{'='*80}")
    total_tests = len([t for t in test_cases if t.get('expected_top')])
    if total_tests > 0:
        print(f"总测试数: {total_tests}")
        print(f"✅ 通过: {passed} ({passed/total_tests*100:.1f}%)")
        print(f"❌ 失败: {failed} ({failed/total_tests*100:.1f}%)")

        if failed == 0:
            print(f"\n🎉 所有测试通过！RAG推荐逻辑工作正常。")
        else:
            print(f"\n⚠️ 有 {failed} 个测试失败，建议检查：")
            print(f"   1. Action的description是否已填充完整")
            print(f"   2. Action索引是否已重建")
            print(f"   3. 调整config.yaml中的权重参数")


if __name__ == "__main__":
    print("="*80)
    print("RAG Action推荐系统测试")
    print("测试综合推荐逻辑（语义匹配 + 使用频率）")
    print("="*80)

    test_recommendations()

    print("\n\n测试完成!")
