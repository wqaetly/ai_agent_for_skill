"""
Action索引构建脚本
一键构建Action向量索引的主入口
"""

import os
import sys
import yaml
import logging
import argparse
from datetime import datetime

from rag_engine import RAGEngine


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path: str = 'config.yaml') -> dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def check_action_definitions(config: dict) -> bool:
    """检查Action定义目录是否存在"""
    action_config = config.get('action_indexer', {})
    actions_dir = action_config.get('actions_directory', '')

    if not os.path.exists(actions_dir):
        logging.error(f"❌ Actions目录不存在: {actions_dir}")
        logging.error("请先在Unity中运行 Tools -> Skill RAG -> Export Actions to JSON")
        return False

    # 检查是否有JSON文件
    json_files = [f for f in os.listdir(actions_dir) if f.endswith('.json')]
    if not json_files:
        logging.error(f"❌ Actions目录中没有JSON文件: {actions_dir}")
        logging.error("请先在Unity中运行 Tools -> Skill RAG -> Export Actions to JSON")
        return False

    logging.info(f"✅ 找到Actions目录: {actions_dir}")
    logging.info(f"✅ 包含 {len(json_files)} 个Action文件")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='构建Action向量索引')
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重建索引（清空现有数据）'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='配置文件路径'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='仅显示统计信息，不执行索引'
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    print("=" * 70)
    print("Action脚本索引构建工具")
    print("=" * 70)
    print()

    try:
        # 1. 加载配置
        logger.info("加载配置文件...")
        config = load_config(args.config)

        # 2. 检查Action定义文件
        if not check_action_definitions(config):
            sys.exit(1)

        # 3. 初始化RAG引擎
        logger.info("初始化RAG引擎...")
        engine = RAGEngine(config)

        # 4. 显示Action统计信息
        logger.info("获取Action统计信息...")
        stats = engine.action_indexer.get_statistics()

        print()
        print("=" * 70)
        print("Action统计信息")
        print("=" * 70)
        print(f"总Action数: {stats['total_actions']}")
        print(f"平均参数数: {stats['avg_params_per_action']:.1f}")
        print(f"Actions目录: {stats['actions_directory']}")
        print()
        print("按分类统计:")
        for category, count in sorted(stats['category_counts'].items()):
            print(f"  {category}: {count}")
        print("=" * 70)
        print()

        # 如果只是显示统计信息，直接退出
        if args.stats_only:
            logger.info("统计信息显示完成")
            sys.exit(0)

        # 5. 构建索引
        force_rebuild = args.force
        if force_rebuild:
            logger.warning("⚠️  将强制重建Action索引（清空现有数据）")
        else:
            logger.info("将增量更新Action索引")

        print()
        logger.info("开始构建Action向量索引...")
        start_time = datetime.now()

        result = engine.index_actions(force_rebuild=force_rebuild)

        elapsed_time = (datetime.now() - start_time).total_seconds()

        # 6. 显示结果
        print()
        print("=" * 70)
        print("索引构建结果")
        print("=" * 70)

        if result['status'] == 'success':
            print(f"✅ 索引构建成功！")
            print(f"索引Action数: {result['count']}")
            print(f"耗时: {result.get('elapsed_time', elapsed_time):.2f} 秒")
            print()
            print("可以通过以下方式测试:")
            print(f"  1. 访问 http://127.0.0.1:8765/docs 查看API文档")
            print(f"  2. 测试搜索: python test_action_search.py")
        elif result['status'] == 'no_actions':
            print(f"⚠️  未找到Action数据")
        else:
            print(f"❌ 索引构建失败")
            print(f"错误信息: {result.get('message', '未知错误')}")
            sys.exit(1)

        print("=" * 70)

    except FileNotFoundError as e:
        logger.error(f"文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 索引构建失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
