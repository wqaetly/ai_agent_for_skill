"""
快速重建Action索引
"""
import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
os.chdir(current_dir)

import yaml
import logging
from rag_engine import RAGEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print("重建Action索引")
print("=" * 80)

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 创建RAG引擎
logger.info("初始化RAG引擎...")
engine = RAGEngine(config)

# 重建Action索引
logger.info("开始重建Action索引...")
result = engine.index_actions(force_rebuild=True)

print("\n" + "=" * 80)
print("索引结果:")
print("=" * 80)
print(f"状态: {result.get('status')}")
print(f"索引数量: {result.get('count')}")
print(f"耗时: {result.get('elapsed_time', 0):.2f}秒")

if result.get('status') == 'success':
    print("\n✅ Action索引重建成功！")
    
    # 测试搜索
    print("\n测试搜索 '位移':")
    actions = engine.search_actions("位移", top_k=3, return_details=True)
    print(f"找到 {len(actions)} 个结果:")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action.get('display_name')} ({action.get('type_name')})")
        print(f"     相似度: {action.get('similarity', 0):.4f}")
else:
    print(f"\n❌ 索引失败: {result.get('message')}")

print("=" * 80)
