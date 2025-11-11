"""
配置加载器
支持YAML配置文件加载、环境变量替换、配置验证
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器 - 支持环境变量和验证"""

    # 环境变量替换正则：${ENV_VAR}
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML解析错误
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        logger.info(f"Loading configuration from: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)

        # 递归替换环境变量
        self.config = self._replace_env_vars(raw_config)

        # 验证配置
        self._validate_config()

        logger.info("Configuration loaded successfully")
        return self.config

    def _replace_env_vars(self, config: Any) -> Any:
        """
        递归替换配置中的环境变量

        Args:
            config: 配置对象（可能是dict, list, str等）

        Returns:
            替换后的配置对象
        """
        if isinstance(config, dict):
            return {k: self._replace_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._replace_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._replace_env_var_in_string(config)
        else:
            return config

    def _replace_env_var_in_string(self, value: str) -> str:
        """
        替换字符串中的环境变量

        支持格式：
        - ${ENV_VAR}  # 必须存在
        - ${ENV_VAR:default_value}  # 可选，带默认值（未实现）

        Args:
            value: 原始字符串

        Returns:
            替换后的字符串
        """
        def replacer(match):
            env_var = match.group(1)

            # 支持默认值语法：${VAR:default}
            if ':' in env_var:
                var_name, default_value = env_var.split(':', 1)
                return os.environ.get(var_name, default_value)
            else:
                # 不存在则返回空字符串（避免启动失败）
                env_value = os.environ.get(env_var)
                if env_value is None:
                    logger.warning(
                        f"Environment variable '{env_var}' not set, using empty string"
                    )
                    return ""
                return env_value

        return self.ENV_VAR_PATTERN.sub(replacer, value)

    def _validate_config(self):
        """验证配置完整性"""
        assert self.config is not None, "Config not loaded"

        # 验证必需的顶级字段
        required_sections = ["server", "embedding", "llm_providers"]
        for section in required_sections:
            if section not in self.config:
                logger.warning(f"Missing config section: {section}")

        # 验证服务器配置
        if "server" in self.config:
            server = self.config["server"]
            if "host" not in server:
                logger.warning("Server host not configured, using default 127.0.0.1")
                server["host"] = "127.0.0.1"

        # 验证LLM提供商配置
        if "llm_providers" in self.config:
            llm_config = self.config["llm_providers"]
            default_provider = llm_config.get("default")

            if default_provider:
                # 检查默认提供商是否配置
                if default_provider not in llm_config:
                    logger.error(
                        f"Default LLM provider '{default_provider}' not found in config"
                    )
                elif not llm_config[default_provider].get("enabled", False):
                    logger.warning(
                        f"Default LLM provider '{default_provider}' is disabled"
                    )

                # 检查API Key
                provider_config = llm_config.get(default_provider, {})
                if not provider_config.get("api_key"):
                    logger.error(
                        f"API key not set for LLM provider '{default_provider}'. "
                        f"Please set the environment variable or update config."
                    )

        logger.info("Configuration validation completed")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号路径）

        Args:
            key_path: 配置路径（如 "server.host"）
            default: 默认值

        Returns:
            配置值

        Example:
            >>> config.get("server.host")
            "127.0.0.1"
            >>> config.get("llm_providers.deepseek.api_key")
            "sk-xxx"
        """
        if self.config is None:
            raise RuntimeError("Config not loaded. Call load() first.")

        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_llm_config(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取LLM提供商配置

        Args:
            provider_name: 提供商名称（None则使用默认）

        Returns:
            LLM配置字典
        """
        if provider_name is None:
            provider_name = self.get("llm_providers.default", "deepseek")

        provider_config = self.get(f"llm_providers.{provider_name}", {})

        if not provider_config:
            raise ValueError(f"LLM provider '{provider_name}' not found in config")

        if not provider_config.get("enabled", False):
            logger.warning(f"LLM provider '{provider_name}' is disabled in config")

        return provider_config

    def reload(self):
        """重新加载配置文件（支持热更新）"""
        logger.info("Reloading configuration...")
        self.load()


# ==================== 全局配置实例 ====================

_global_config: Optional[ConfigLoader] = None


def get_config(config_path: str = "config.yaml") -> ConfigLoader:
    """
    获取全局配置实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigLoader实例
    """
    global _global_config

    if _global_config is None:
        _global_config = ConfigLoader(config_path)
        _global_config.load()

    return _global_config


def reload_config():
    """重新加载全局配置"""
    global _global_config
    if _global_config is not None:
        _global_config.reload()
