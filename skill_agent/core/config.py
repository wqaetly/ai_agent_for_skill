"""
RAG Core 配置加载器
提供统一的配置管理接口，支持环境变量替换和路径解析
"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CoreConfig:
    """RAG Core 配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 core_config.yaml
        """
        if config_path is None:
            # 默认配置文件路径（相对于当前文件）
            core_dir = Path(__file__).parent
            config_path = core_dir.parent / "core_config.yaml"

        self.config_path = Path(config_path)
        self.config_dir = self.config_path.parent

        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        # 加载配置
        self._config = self._load_config()

        # 解析所有路径（转换相对路径为绝对路径）
        self._resolve_paths()

    def _load_config(self) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换环境变量 ${ENV_VAR_NAME}
        content = self._substitute_env_vars(content)

        # 解析 YAML
        config = yaml.safe_load(content)

        logger.info(f"已加载配置文件: {self.config_path}")
        return config

    def _substitute_env_vars(self, content: str) -> str:
        """替换配置中的环境变量"""
        pattern = re.compile(r'\$\{(\w+)\}')

        def replacer(match):
            env_var = match.group(1)
            value = os.environ.get(env_var)
            if value is None:
                logger.warning(f"环境变量 {env_var} 未设置")
                return match.group(0)  # 保留原始字符串
            return value

        return pattern.sub(replacer, content)

    def _resolve_paths(self):
        """解析配置中的相对路径为绝对路径"""
        # embedding.model_name
        if 'embedding' in self._config and 'model_name' in self._config['embedding']:
            model_path = self._config['embedding']['model_name']
            if not Path(model_path).is_absolute():
                self._config['embedding']['model_name'] = str(
                    (self.config_dir / model_path).resolve()
                )

        # vector_store.persist_directory
        if 'vector_store' in self._config and 'persist_directory' in self._config['vector_store']:
            vec_dir = self._config['vector_store']['persist_directory']
            if not Path(vec_dir).is_absolute():
                self._config['vector_store']['persist_directory'] = str(
                    (self.config_dir / vec_dir).resolve()
                )

        # skill_indexer.skills_directory
        if 'skill_indexer' in self._config and 'skills_directory' in self._config['skill_indexer']:
            skills_dir = self._config['skill_indexer']['skills_directory']
            if not Path(skills_dir).is_absolute():
                self._config['skill_indexer']['skills_directory'] = str(
                    (self.config_dir / skills_dir).resolve()
                )

        # skill_indexer.index_cache
        if 'skill_indexer' in self._config and 'index_cache' in self._config['skill_indexer']:
            cache_path = self._config['skill_indexer']['index_cache']
            if not Path(cache_path).is_absolute():
                self._config['skill_indexer']['index_cache'] = str(
                    (self.config_dir / cache_path).resolve()
                )

        # action_indexer.actions_directory
        if 'action_indexer' in self._config and 'actions_directory' in self._config['action_indexer']:
            actions_dir = self._config['action_indexer']['actions_directory']
            if not Path(actions_dir).is_absolute():
                self._config['action_indexer']['actions_directory'] = str(
                    (self.config_dir / actions_dir).resolve()
                )

        # action_indexer.action_index_cache
        if 'action_indexer' in self._config and 'action_index_cache' in self._config['action_indexer']:
            cache_path = self._config['action_indexer']['action_index_cache']
            if not Path(cache_path).is_absolute():
                self._config['action_indexer']['action_index_cache'] = str(
                    (self.config_dir / cache_path).resolve()
                )

        # logging.file
        if 'logging' in self._config and 'file' in self._config['logging']:
            log_file = self._config['logging']['file']
            if not Path(log_file).is_absolute():
                self._config['logging']['file'] = str(
                    (self.config_dir / log_file).resolve()
                )

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持嵌套键，如 'embedding.model_name'）

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置段

        Args:
            section: 配置段名称（如 'embedding', 'rag'）

        Returns:
            配置段字典
        """
        return self._config.get(section, {})

    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self._config.copy()

    @property
    def embedding(self) -> Dict[str, Any]:
        """嵌入模型配置"""
        return self.get_section('embedding')

    @property
    def vector_store(self) -> Dict[str, Any]:
        """向量存储配置"""
        return self.get_section('vector_store')

    @property
    def skill_indexer(self) -> Dict[str, Any]:
        """技能索引配置"""
        return self.get_section('skill_indexer')

    @property
    def action_indexer(self) -> Dict[str, Any]:
        """Action 索引配置"""
        return self.get_section('action_indexer')

    @property
    def rag(self) -> Dict[str, Any]:
        """RAG 检索配置"""
        return self.get_section('rag')

    @property
    def logging(self) -> Dict[str, Any]:
        """日志配置"""
        return self.get_section('logging')

    def setup_logging(self):
        """根据配置设置日志"""
        log_config = self.logging
        level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file')
        max_bytes = log_config.get('max_bytes', 10485760)
        backup_count = log_config.get('backup_count', 3)
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S')

        # 创建日志目录
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # 使用 RotatingFileHandler
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            # 使用 StreamHandler（输出到控制台）
            handler = logging.StreamHandler()

        # 设置格式
        formatter = logging.Formatter(log_format, datefmt=date_format)
        handler.setFormatter(formatter)

        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(handler)

        logger.info("日志系统已初始化")


# 全局配置实例（单例）
_global_config: Optional[CoreConfig] = None


def get_config(config_path: Optional[str] = None) -> CoreConfig:
    """
    获取全局配置实例

    Args:
        config_path: 配置文件路径（仅首次调用有效）

    Returns:
        CoreConfig 实例
    """
    global _global_config

    if _global_config is None:
        _global_config = CoreConfig(config_path)

    return _global_config


def reset_config():
    """重置全局配置（主要用于测试）"""
    global _global_config
    _global_config = None
