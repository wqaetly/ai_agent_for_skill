"""
集中管理的常量配置

支持环境变量覆盖，优先级：环境变量 > 默认值
使用 pydantic-settings 实现类型安全的配置管理
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """服务器配置"""

    model_config = SettingsConfigDict(
        env_prefix="",  # 不使用前缀，直接匹配环境变量名
        case_sensitive=False,
    )

    # LangGraph 服务
    LANGGRAPH_HOST: str = "0.0.0.0"
    LANGGRAPH_PORT: int = 2024

    # Unity RPC 服务
    UNITY_RPC_HOST: str = "127.0.0.1"
    UNITY_RPC_PORT: int = 8766

    # WebUI
    WEBUI_PORT: int = 7860


class RetrySettings(BaseSettings):
    """重试配置"""

    model_config = SettingsConfigDict(
        env_prefix="RETRY_",
        case_sensitive=False,
    )

    # 标准生成重试次数
    MAX_RETRIES: int = 3

    # 渐进式生成 Track 重试次数
    MAX_TRACK_RETRIES: int = 3

    # 批次生成重试次数
    MAX_BATCH_RETRIES: int = 2


class RAGSettings(BaseSettings):
    """RAG 检索配置"""

    model_config = SettingsConfigDict(
        env_prefix="RAG_",
        case_sensitive=False,
    )

    # 搜索默认返回数量
    DEFAULT_TOP_K: int = 5

    # 推荐默认返回数量
    RECOMMEND_TOP_K: int = 3

    # 参数推荐默认返回数量
    PARAMETER_TOP_K: int = 5

    # 相似度阈值（低于此值的结果将被过滤）
    SIMILARITY_THRESHOLD: float = 0.1


class CacheSettings(BaseSettings):
    """缓存配置"""

    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        case_sensitive=False,
    )

    # 查询缓存 TTL（秒）
    QUERY_CACHE_TTL: int = 3600

    # 查询缓存最大条目数
    QUERY_CACHE_MAXSIZE: int = 1000

    # 嵌入缓存最大条目数
    EMBEDDING_CACHE_MAXSIZE: int = 1000

    # 统计缓存最大条目数
    STATS_CACHE_MAXSIZE: int = 20


class ValidationSettings(BaseSettings):
    """验证配置"""

    model_config = SettingsConfigDict(
        env_prefix="VALIDATION_",
        case_sensitive=False,
    )

    # 最小技能时长（帧数，30fps 下约 1 秒）
    MIN_SKILL_DURATION: int = 30

    # 默认帧率
    DEFAULT_FRAME_RATE: int = 30

    # 最大帧率
    MAX_FRAME_RATE: int = 120

    # 最小帧率
    MIN_FRAME_RATE: int = 15

    # 单 Track 最大 Action 数
    MAX_ACTIONS_PER_TRACK: int = 20

    # 单批次最大 Action 数
    MAX_ACTIONS_PER_BATCH: int = 10


class TimeoutSettings(BaseSettings):
    """超时配置"""

    model_config = SettingsConfigDict(
        env_prefix="TIMEOUT_",
        case_sensitive=False,
    )

    # DeepSeek API 超时（秒）
    DEEPSEEK_TIMEOUT: int = 120

    # 子进程超时（秒）
    SUBPROCESS_TIMEOUT: int = 5

    # 端口释放等待时间（秒）
    PORT_RELEASE_WAIT: int = 2


class CORSSettings(BaseSettings):
    """CORS 跨域配置

    安全说明：
    - 开发环境：默认允许 localhost 的常用端口
    - 生产环境：必须设置 ALLOWED_ORIGINS 环境变量为具体域名

    环境变量示例：
    ALLOWED_ORIGINS=https://myapp.example.com,https://api.example.com
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )

    # 允许的源列表（逗号分隔）
    # 默认只允许本地开发地址
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:7860,http://127.0.0.1:3000,http://127.0.0.1:7860"

    # 是否允许携带凭证
    ALLOW_CREDENTIALS: bool = True

    # 允许的 HTTP 方法
    ALLOW_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"

    # 允许的请求头
    ALLOW_HEADERS: str = "Content-Type,Authorization,X-Requested-With"

    @property
    def origins_list(self) -> list[str]:
        """将逗号分隔的字符串转换为列表"""
        if not self.ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def methods_list(self) -> list[str]:
        """将逗号分隔的方法字符串转换为列表"""
        if not self.ALLOW_METHODS:
            return ["*"]
        return [method.strip() for method in self.ALLOW_METHODS.split(",") if method.strip()]

    @property
    def headers_list(self) -> list[str]:
        """将逗号分隔的头部字符串转换为列表"""
        if not self.ALLOW_HEADERS:
            return ["*"]
        return [header.strip() for header in self.ALLOW_HEADERS.split(",") if header.strip()]


# ==================== 单例获取函数 ====================


@lru_cache()
def get_server_settings() -> ServerSettings:
    """获取服务器配置（单例）"""
    return ServerSettings()


@lru_cache()
def get_retry_settings() -> RetrySettings:
    """获取重试配置（单例）"""
    return RetrySettings()


@lru_cache()
def get_rag_settings() -> RAGSettings:
    """获取 RAG 配置（单例）"""
    return RAGSettings()


@lru_cache()
def get_cache_settings() -> CacheSettings:
    """获取缓存配置（单例）"""
    return CacheSettings()


@lru_cache()
def get_validation_settings() -> ValidationSettings:
    """获取验证配置（单例）"""
    return ValidationSettings()


@lru_cache()
def get_timeout_settings() -> TimeoutSettings:
    """获取超时配置（单例）"""
    return TimeoutSettings()


@lru_cache()
def get_cors_settings() -> CORSSettings:
    """获取 CORS 配置（单例）"""
    return CORSSettings()


# ==================== 便捷访问（向后兼容） ====================

# 直接导出常用配置实例
server = get_server_settings()
retry = get_retry_settings()
rag = get_rag_settings()
cache = get_cache_settings()
validation = get_validation_settings()
timeout = get_timeout_settings()
cors = get_cors_settings()
