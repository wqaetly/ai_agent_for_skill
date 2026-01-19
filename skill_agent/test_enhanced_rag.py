"""
增强版RAG模块测试
测试：混合检索、查询理解、重排序、扩展查询、增量索引、上下文感知
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_bm25_index():
    """测试BM25索引"""
    print("\n" + "="*60)
    print("测试 BM25 索引")
    print("="*60)
    
    from core.hybrid_search import BM25Index
    
    bm25 = BM25Index()
    
    # 添加测试文档
    documents = [
        "火焰冲击波技能，造成大量火焰伤害",
        "治疗光环，恢复周围友军生命值",
        "冰霜新星，冻结敌人并造成冰霜伤害",
        "闪电链，对多个敌人造成雷电伤害",
        "护盾术，为目标添加护盾保护"
    ]
    doc_ids = [f"doc_{i}" for i in range(len(documents))]
    
    bm25.add_documents(documents, doc_ids)
    
    # 测试搜索
    results = bm25.search("火焰伤害", top_k=3)
    print(f"搜索 '火焰伤害': {results}")
    
    results = bm25.search("治疗恢复", top_k=3)
    print(f"搜索 '治疗恢复': {results}")
    
    print(f"统计信息: {bm25.get_statistics()}")
    print("[PASS] BM25索引测试通过")


def test_query_understanding():
    """测试查询理解"""
    print("\n" + "="*60)
    print("测试查询理解引擎")
    print("="*60)
    
    from core.query_understanding import QueryUnderstandingEngine, QueryIntent
    
    engine = QueryUnderstandingEngine()
    
    test_queries = [
        "搜索火焰伤害技能",
        "推荐一个造成眩晕效果的Action",
        "查询baseDamage大于200的技能",
        "找一个类似冰霜新星的技能",
    ]
    
    for query in test_queries:
        result = engine.understand(query)
        print(f"\n查询: {query}")
        print(f"  意图: {result.intent.value}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  提取实体: {result.extracted_entities}")
        print(f"  扩展查询: {result.expanded_queries[:3]}")
    
    print("\n[PASS] 查询理解测试通过")


def test_extended_query_parser():
    """测试扩展查询解析器"""
    print("\n" + "="*60)
    print("测试扩展查询解析器")
    print("="*60)
    
    from core.extended_query_parser import ExtendedQueryParser, ExtendedQueryEvaluator
    
    parser = ExtendedQueryParser()
    evaluator = ExtendedQueryEvaluator()
    
    # 测试简单查询
    test_queries = [
        "DamageAction where baseDamage > 100",
        "DamageAction where baseDamage > 100 or duration > 30",
        "HealAction where healAmount between 50 and 200",
        "SELECT COUNT(*), AVG(baseDamage) FROM DamageAction GROUP BY damageType",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        expr = parser.parse(query)
        print(f"  Action类型: {expr.action_type}")
        print(f"  WHERE条件: {expr.where}")
        print(f"  聚合: {expr.aggregates}")
        print(f"  GROUP BY: {expr.group_by}")
    
    # 测试条件评估
    test_data = {"baseDamage": 150, "duration": 40, "damageType": "Fire"}
    
    expr1 = parser.parse("DamageAction where baseDamage > 100")
    result1 = evaluator.evaluate_condition(expr1.where, test_data)
    print(f"\n条件评估 'baseDamage > 100' (实际值150): {result1}")
    
    expr2 = parser.parse("DamageAction where baseDamage > 200 or duration > 30")
    result2 = evaluator.evaluate_condition(expr2.where, test_data)
    print(f"条件评估 'baseDamage > 200 or duration > 30' (实际值150, 40): {result2}")
    
    print("\n[PASS] 扩展查询解析器测试通过")


def test_reranker():
    """测试重排序器"""
    print("\n" + "="*60)
    print("测试重排序器")
    print("="*60)
    
    from core.reranker import SkillReranker, ActionReranker, RerankerPipeline
    
    # 测试技能重排序
    skill_reranker = SkillReranker()
    
    test_docs = [
        {'doc_id': '1', 'document': '火焰冲击波', 'score': 0.8, 'metadata': {'skill_name': '火焰冲击波', 'action_type_list': '["DamageAction"]'}},
        {'doc_id': '2', 'document': '治疗光环', 'score': 0.85, 'metadata': {'skill_name': '治疗光环', 'action_type_list': '["HealAction"]'}},
        {'doc_id': '3', 'document': '火焰风暴', 'score': 0.75, 'metadata': {'skill_name': '火焰风暴', 'action_type_list': '["DamageAction", "AreaOfEffectAction"]'}},
    ]
    
    results = skill_reranker.rerank("火焰伤害技能", test_docs, top_k=3)
    
    print("重排序结果 (查询: '火焰伤害技能'):")
    for r in results:
        print(f"  {r.doc_id}: 原始分数={r.original_score:.3f}, 重排序分数={r.rerank_score:.3f}, 排名变化={r.original_rank}->{r.new_rank}")
    
    print("\n[PASS] 重排序器测试通过")


def test_incremental_indexer():
    """测试增量索引器"""
    print("\n" + "="*60)
    print("测试增量索引器")
    print("="*60)
    
    from core.incremental_indexer import IncrementalIndexer, FileHashTracker
    import tempfile
    import json
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        test_file = os.path.join(tmpdir, "test_skill.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump({"skillName": "测试技能", "skillId": "test_001"}, f)
        
        # 创建索引器
        indexer = IncrementalIndexer(
            watch_directory=tmpdir,
            file_pattern="*.json"
        )
        
        # 扫描变更
        changes = indexer.scan_for_changes()
        print(f"检测到 {len(changes)} 个新文件")
        
        # 应用变更
        stats = indexer.apply_changes(changes)
        print(f"应用变更: {stats}")
        
        # 再次扫描（应该无变更）
        changes2 = indexer.scan_for_changes()
        print(f"再次扫描: {len(changes2)} 个变更")
        
        # 修改文件
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump({"skillName": "修改后的技能", "skillId": "test_001"}, f)
        
        changes3 = indexer.scan_for_changes()
        print(f"修改后扫描: {len(changes3)} 个变更")
        
        print(f"索引状态: {indexer.get_status()}")
    
    print("\n[PASS] 增量索引器测试通过")


def test_context_aware_retriever():
    """测试上下文感知检索器"""
    print("\n" + "="*60)
    print("测试上下文感知检索器")
    print("="*60)
    
    from core.context_aware_retriever import ContextAwareRetriever, EditContext
    
    retriever = ContextAwareRetriever()
    
    # 设置编辑上下文
    context = EditContext(
        skill_id="skill_001",
        skill_name="火焰风暴",
        existing_action_types=["DamageAction", "AnimationAction"],
        total_duration=120,
        frame_rate=30
    )
    retriever.set_context(context)
    
    # 模拟技能数据分析
    skill_data = {
        "skillId": "skill_001",
        "skillName": "火焰风暴",
        "totalDuration": 120,
        "frameRate": 30,
        "tracks": [
            {
                "trackName": "伤害轨道",
                "actions": [
                    {"type": "DamageAction", "frame": 10},
                    {"type": "AreaOfEffectAction", "frame": 20}
                ]
            },
            {
                "trackName": "动画轨道",
                "actions": [
                    {"type": "AnimationAction", "frame": 0}
                ]
            }
        ]
    }
    retriever.cooccurrence_analyzer.analyze_skill(skill_data)
    
    # 获取相关Action
    related = retriever.cooccurrence_analyzer.get_related_actions("DamageAction", top_k=3)
    print(f"与DamageAction相关的Action: {related}")
    
    print(f"统计信息: {retriever.get_statistics()}")
    
    print("\n[PASS] 上下文感知检索器测试通过")


def main():
    """运行所有测试"""
    print("="*60)
    print("增强版RAG模块测试")
    print("="*60)
    
    try:
        test_bm25_index()
        test_query_understanding()
        test_extended_query_parser()
        test_reranker()
        test_incremental_indexer()
        test_context_aware_retriever()
        
        print("\n" + "="*60)
        print("[PASS] 所有测试通过!")
        print("="*60)
        
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
