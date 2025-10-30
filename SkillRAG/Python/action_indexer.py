"""
Action脚本索引模块
负责读取Unity导出的action_definitions.json，构建Action索引
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ActionIndexer:
    """Action索引器，处理Action脚本元数据的索引"""

    def __init__(self, config: dict):
        """
        初始化Action索引器

        Args:
            config: 索引配置字典
        """
        self.config = config
        self.actions_directory = config.get(
            "actions_directory",
            "../Data/Actions"
        )
        self.index_cache_path = config.get(
            "action_index_cache",
            "../Data/action_index.json"
        )

        # 确保Actions目录存在
        if not os.path.exists(self.actions_directory):
            logger.warning(f"Actions directory not found: {self.actions_directory}")

        # 加载缓存索引
        self.cached_index = self._load_index_cache()

    def _load_index_cache(self) -> Dict[str, Any]:
        """加载缓存的Action索引信息"""
        if os.path.exists(self.index_cache_path):
            try:
                with open(self.index_cache_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded action index cache with {len(cache.get('actions', []))} actions")
                return cache
            except Exception as e:
                logger.error(f"Error loading action index cache: {e}")

        return {"actions": [], "last_updated": None}

    def _save_index_cache(self, index: Dict[str, Any]):
        """保存Action索引缓存"""
        try:
            cache_dir = os.path.dirname(self.index_cache_path)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            with open(self.index_cache_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved action index cache to {self.index_cache_path}")
        except Exception as e:
            logger.error(f"Error saving action index cache: {e}")

    def load_action_definitions(self) -> List[Dict[str, Any]]:
        """
        扫描并加载所有Action定义文件

        Returns:
            Action定义列表
        """
        if not os.path.exists(self.actions_directory):
            logger.error(f"Actions directory not found: {self.actions_directory}")
            return []

        actions = []

        try:
            # 扫描目录下所有JSON文件
            for filename in os.listdir(self.actions_directory):
                if not filename.endswith('.json'):
                    continue

                filepath = os.path.join(self.actions_directory, filename)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 提取action字段
                    action = data.get('action', {})
                    if action:
                        # 添加文件信息
                        action['_file_name'] = filename
                        action['_file_path'] = filepath
                        action['_export_time'] = data.get('exportTime', '')
                        actions.append(action)
                    else:
                        logger.warning(f"No 'action' field found in {filename}")

                except Exception as e:
                    logger.error(f"Error loading action file {filename}: {e}")

            logger.info(f"Loaded {len(actions)} action definitions from {self.actions_directory}")
            return actions

        except Exception as e:
            logger.error(f"Error scanning actions directory: {e}")
            return []

    def build_action_search_text(self, action: Dict[str, Any]) -> str:
        """
        构建Action的搜索文本，用于向量嵌入

        Args:
            action: Action定义字典

        Returns:
            搜索文本字符串
        """
        # 如果已经有searchText字段，直接使用
        if 'searchText' in action and action['searchText']:
            return action['searchText']

        parts = []

        # 基础信息
        type_name = action.get('typeName', '')
        display_name = action.get('displayName', type_name)
        category = action.get('category', 'Other')

        parts.append(f"Action类型: {type_name}")
        parts.append(f"显示名称: {display_name}")
        parts.append(f"分类: {category}")

        # 功能描述
        if action.get('description'):
            parts.append(f"功能描述: {action['description']}")

        # 参数信息
        parameters = action.get('parameters', [])
        if parameters:
            param_names = [p.get('name', '') for p in parameters]
            parts.append(f"参数: {', '.join(param_names)}")

            # 详细参数描述（前5个）
            for param in parameters[:5]:
                param_name = param.get('name', '')
                param_label = param.get('label', param_name)
                param_desc_parts = [f"{param_label}({param_name})"]

                # 添加参数描述
                if param.get('description'):
                    param_desc_parts.append(param['description'])
                elif param.get('infoBox'):
                    param_desc_parts.append(param['infoBox'])

                # 添加类型信息
                param_type = param.get('type', '')
                if param_type:
                    param_desc_parts.append(f"类型:{param_type}")

                # 添加约束信息
                constraints = param.get('constraints', {})
                if constraints.get('minValue'):
                    param_desc_parts.append(f"最小值:{constraints['minValue']}")
                if constraints.get('min') and constraints.get('max'):
                    param_desc_parts.append(f"范围:{constraints['min']}-{constraints['max']}")

                parts.append(" - ".join(param_desc_parts))

        return "\n".join(parts)

    def build_action_metadata(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建Action的元数据，用于向量数据库存储

        Args:
            action: Action定义字典

        Returns:
            元数据字典
        """
        parameters = action.get('parameters', [])

        metadata = {
            "type_name": action.get('typeName', ''),
            "display_name": action.get('displayName', ''),
            "category": action.get('category', 'Other'),
            "param_count": len(parameters),
            "full_type_name": action.get('fullTypeName', ''),
            "namespace": action.get('namespaceName', ''),
        }

        # 添加参数名列表（用于搜索）
        if parameters:
            param_names = [p.get('name', '') for p in parameters[:10]]  # 限制10个
            metadata["param_names"] = ", ".join(param_names)

        return metadata

    def get_all_actions(self) -> List[Dict[str, Any]]:
        """
        获取所有Action定义

        Returns:
            Action定义列表
        """
        return self.load_action_definitions()

    def get_action_by_type(self, type_name: str) -> Optional[Dict[str, Any]]:
        """
        根据类型名获取Action定义

        Args:
            type_name: Action类型名

        Returns:
            Action定义字典，如果不存在返回None
        """
        actions = self.get_all_actions()
        for action in actions:
            if action.get('typeName') == type_name:
                return action
        return None

    def get_actions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        根据分类获取Action定义列表

        Args:
            category: Action分类

        Returns:
            Action定义列表
        """
        actions = self.get_all_actions()
        return [a for a in actions if a.get('category', '').lower() == category.lower()]

    def prepare_actions_for_indexing(self) -> List[Dict[str, Any]]:
        """
        准备用于索引的Action数据

        Returns:
            包含搜索文本、元数据和ID的Action列表
        """
        actions = self.get_all_actions()
        prepared_actions = []

        for action in actions:
            try:
                prepared = {
                    "id": f"action_{action.get('typeName', '')}",
                    "search_text": self.build_action_search_text(action),
                    "metadata": self.build_action_metadata(action),
                    "original_data": action  # 保留原始数据用于详细查询
                }
                prepared_actions.append(prepared)
            except Exception as e:
                logger.error(f"Error preparing action {action.get('typeName', 'unknown')}: {e}")

        return prepared_actions

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取Action统计信息

        Returns:
            统计信息字典
        """
        actions = self.get_all_actions()

        # 按分类统计
        category_counts = {}
        total_params = 0

        for action in actions:
            category = action.get('category', 'Other')
            category_counts[category] = category_counts.get(category, 0) + 1
            total_params += len(action.get('parameters', []))

        return {
            "total_actions": len(actions),
            "category_counts": category_counts,
            "avg_params_per_action": total_params / len(actions) if actions else 0,
            "actions_directory": self.actions_directory,
            "directory_exists": os.path.exists(self.actions_directory)
        }


def main():
    """测试Action索引器"""
    logging.basicConfig(level=logging.INFO)

    # 测试配置
    config = {
        "actions_directory": "../Data/Actions",
        "action_index_cache": "../Data/action_index.json"
    }

    indexer = ActionIndexer(config)

    # 显示统计信息
    stats = indexer.get_statistics()
    print("\n=== Action统计信息 ===")
    print(f"总Action数: {stats['total_actions']}")
    print(f"平均参数数: {stats['avg_params_per_action']:.1f}")
    print(f"\n按分类统计:")
    for category, count in sorted(stats['category_counts'].items()):
        print(f"  {category}: {count}")

    # 测试准备索引数据
    print("\n=== 准备索引数据 ===")
    prepared = indexer.prepare_actions_for_indexing()
    print(f"准备了 {len(prepared)} 个Action用于索引")

    # 显示示例
    if prepared:
        print(f"\n示例Action搜索文本:")
        print(f"ID: {prepared[0]['id']}")
        print(f"搜索文本:\n{prepared[0]['search_text'][:300]}...")


if __name__ == "__main__":
    main()
