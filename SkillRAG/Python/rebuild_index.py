"""
重建向量索引脚本
用于重建技能向量索引，包含新的 action_type_list 字段
"""

import json
import yaml
import logging
import sys
from pathlib import Path

from rag_engine import RAGEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    # 尝试 YAML 配置
    if Path(config_path).exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"已加载配置文件: {config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)

    # 尝试 JSON 配置（备用）
    json_config_path = "config.json"
    if Path(json_config_path).exists():
        try:
            with open(json_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"已加载配置文件: {json_config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)

    logger.warning(f"配置文件不存在，使用默认配置")
    return get_default_config()


def get_default_config() -> dict:
    """获取默认配置"""
    return {
        "embedding": {
            "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "cache_dir": "../Data/embeddings_cache",
            "batch_size": 32
        },
        "vector_store": {
            "persist_directory": "../Data/chroma_db",
            "collection_name": "skill_collection"
        },
        "skill_indexer": {
            "skills_directory": "../../ai_agent_for_skill/Assets/Skills",
            "index_cache": "../Data/skill_index.json",
            "index_action_details": True
        },
        "action_indexer": {
            "action_definitions_path": "../../ai_agent_for_skill/Assets/Scripts/SkillSystem/Actions",
            "collection_name": "action_collection"
        },
        "rag": {
            "top_k": 5,
            "similarity_threshold": 0.5,
            "cache_enabled": True,
            "cache_ttl": 3600
        }
    }


def verify_index(rag_engine: RAGEngine):
    """验证索引结果"""
    logger.info("验证索引...")

    # 执行测试查询
    test_queries = [
        "火焰攻击",
        "治疗技能",
        "移动技能"
    ]

    for query in test_queries:
        try:
            results = rag_engine.search_skills(query, top_k=3, return_details=True)
            logger.info(f"测试查询 '{query}': 找到 {len(results)} 个结果")

            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"  {i}. {result.get('skill_name', 'N/A')} "
                               f"(相似度: {result.get('similarity', 0):.4f})")

                    # 验证 action_type_list 字段
                    action_type_list = result.get('action_type_list')
                    if action_type_list:
                        try:
                            types = json.loads(action_type_list)
                            logger.info(f"     Action类型: {', '.join(types)}")
                        except json.JSONDecodeError:
                            logger.warning(f"     无法解析 action_type_list: {action_type_list}")
                    else:
                        logger.warning(f"     缺少 action_type_list 字段")
        except Exception as e:
            logger.error(f"测试查询失败 '{query}': {e}")

    logger.info("索引验证完成")


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("开始重建向量索引")
    logger.info("=" * 80)

    # 1. 加载配置
    config = load_config()

    # 2. 初始化 RAG 引擎
    logger.info("初始化 RAG 引擎...")
    rag_engine = RAGEngine(config)

    # 3. 重建索引（force_rebuild=True）
    logger.info("开始重建索引...")
    try:
        result = rag_engine.index_skills(force_rebuild=True)

        logger.info("=" * 80)
        logger.info("索引重建完成")
        logger.info(f"状态: {result.get('status', 'unknown')}")
        logger.info(f"索引技能数: {result.get('count', 0)}")
        if 'time_elapsed' in result:
            logger.info(f"耗时: {result['time_elapsed']:.2f}秒")
        logger.info("=" * 80)

        # 4. 验证索引
        verify_index(rag_engine)

        # 5. 打印统计信息
        stats = rag_engine._stats  # 直接访问内部统计
        logger.info("\n统计信息:")
        logger.info(f"  总查询数: {stats.get('total_queries', 0)}")
        logger.info(f"  缓存命中数: {stats.get('cache_hits', 0)}")
        logger.info(f"  总索引数: {stats.get('total_indexed', 0)}")
        logger.info(f"  最后索引时间: {stats.get('last_index_time', 'N/A')}")

        logger.info("\n✓ 索引重建成功！")
        return 0

    except Exception as e:
        logger.error(f"索引重建失败: {e}", exc_info=True)
        logger.error("\n✗ 索引重建失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
