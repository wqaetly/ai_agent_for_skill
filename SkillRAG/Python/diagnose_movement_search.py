"""
诊断"位移"搜索问题
检查Action索引和推荐逻辑
"""

import yaml
import logging
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_engine import RAGEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("诊断 '位移' 搜索问题")
    print("=" * 80)
    
    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    print(f"\n1. 加载配置文件: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 创建RAG引擎
    print("\n2. 初始化RAG引擎...")
    engine = RAGEngine(config)
    
    # 检查Action向量存储
    print("\n3. 检查Action向量存储状态:")
    action_stats = engine.action_vector_store.get_statistics()
    print(f"   - Collection名称: {action_stats.get('collection_name', 'N/A')}")
    print(f"   - 文档数量: {action_stats.get('count', 0)}")
    
    if action_stats.get('count', 0) == 0:
        print("\n   ⚠️ 警告: Action向量存储为空！")
        print("   需要先运行索引构建:")
        print("   python build_action_index.py")
        
        # 尝试构建索引
        print("\n4. 尝试构建Action索引...")
        result = engine.index_actions(force_rebuild=True)
        print(f"   索引结果: {result}")
        
        if result.get('status') != 'success':
            print("\n   ❌ 索引构建失败！")
            return
    
    # 检查Action定义
    print("\n5. 检查MovementAction定义:")
    movement_action = engine.get_action_by_type('MovementAction')
    if movement_action:
        print(f"   ✅ 找到MovementAction")
        print(f"   - 显示名称: {movement_action.get('displayName', 'N/A')}")
        print(f"   - 分类: {movement_action.get('category', 'N/A')}")
        print(f"   - 描述长度: {len(movement_action.get('description', ''))} 字符")
        print(f"   - 搜索文本长度: {len(movement_action.get('searchText', ''))} 字符")
        print(f"\n   搜索文本预览:")
        search_text = movement_action.get('searchText', '')
        print(f"   {search_text[:300]}...")
    else:
        print(f"   ❌ 未找到MovementAction定义")
        return
    
    # 测试直接搜索Action
    print("\n6. 测试直接搜索Action (search_actions):")
    query = "位移"
    print(f"   查询: '{query}'")
    
    action_results = engine.search_actions(
        query=query,
        top_k=5,
        return_details=True
    )
    
    print(f"   找到 {len(action_results)} 个结果:")
    for i, action in enumerate(action_results, 1):
        print(f"   {i}. {action.get('display_name', 'N/A')} ({action.get('type_name', 'N/A')})")
        print(f"      - 相似度: {action.get('similarity', 0):.4f}")
        print(f"      - 分类: {action.get('category', 'N/A')}")
    
    if len(action_results) == 0:
        print("\n   ⚠️ 直接搜索Action返回0个结果！")
        print("   可能的原因:")
        print("   1. 相似度阈值过高 (当前: {})".format(engine.similarity_threshold))
        print("   2. 嵌入模型问题")
        print("   3. 向量索引问题")
        
        # 尝试降低阈值
        print("\n   尝试降低相似度阈值到0.0...")
        old_threshold = engine.similarity_threshold
        engine.similarity_threshold = 0.0
        
        action_results = engine.search_actions(
            query=query,
            top_k=5,
            return_details=True
        )
        
        print(f"   找到 {len(action_results)} 个结果:")
        for i, action in enumerate(action_results, 1):
            print(f"   {i}. {action.get('display_name', 'N/A')} ({action.get('type_name', 'N/A')})")
            print(f"      - 相似度: {action.get('similarity', 0):.4f}")
        
        engine.similarity_threshold = old_threshold
    
    # 测试推荐Action
    print("\n7. 测试推荐Action (recommend_actions):")
    print(f"   上下文: '{query}'")
    
    recommendations = engine.recommend_actions(
        context=query,
        top_k=3
    )
    
    print(f"   推荐 {len(recommendations)} 个Action:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n   {i}. {rec.get('display_name', 'N/A')} ({rec.get('action_type', 'N/A')})")
        print(f"      - 综合得分: {rec.get('combined_score', 0):.4f}")
        print(f"      - 语义相似度: {rec.get('semantic_similarity', 0):.4f}")
        print(f"      - 使用频率: {rec.get('frequency', 0)} 次")
        print(f"      - 分类: {rec.get('category', 'N/A')}")
    
    if len(recommendations) == 0:
        print("\n   ❌ 推荐返回0个结果！")
        print("\n   诊断步骤:")
        
        # 检查配置
        print("\n   a) 检查配置参数:")
        print(f"      - similarity_threshold: {config['rag'].get('similarity_threshold', 'N/A')}")
        print(f"      - recommend_semantic_weight: {config['rag'].get('recommend_semantic_weight', 'N/A')}")
        print(f"      - recommend_usage_weight: {config['rag'].get('recommend_usage_weight', 'N/A')}")
        print(f"      - recommend_min_similarity: {config['rag'].get('recommend_min_similarity', 'N/A')}")
        
        # 检查技能索引
        print("\n   b) 检查技能索引:")
        skill_stats = engine.vector_store.get_statistics()
        print(f"      - 技能数量: {skill_stats.get('count', 0)}")
        
        if skill_stats.get('count', 0) == 0:
            print("      ⚠️ 技能索引为空，需要先索引技能!")
            print("      运行: python build_action_index.py --index-skills")
        
        # 测试搜索技能
        print("\n   c) 测试搜索相关技能:")
        skill_results = engine.search_skills(
            query=query,
            top_k=3,
            return_details=True
        )
        print(f"      找到 {len(skill_results)} 个技能:")
        for skill in skill_results:
            print(f"      - {skill.get('skill_name', 'N/A')} (相似度: {skill.get('similarity', 0):.4f})")
    
    # 总结
    print("\n" + "=" * 80)
    print("诊断总结:")
    print("=" * 80)
    
    if len(recommendations) > 0:
        print("✅ 推荐功能正常工作")
    else:
        print("❌ 推荐功能存在问题")
        print("\n建议的修复步骤:")
        print("1. 确保Action已索引: python build_action_index.py")
        print("2. 确保技能已索引: python build_action_index.py --index-skills")
        print("3. 检查config.yaml中的阈值设置")
        print("4. 检查嵌入模型是否正常工作")

if __name__ == "__main__":
    main()
