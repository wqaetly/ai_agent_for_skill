"""
技能生成配置模块
集中管理技能生成流程中的所有可配置参数
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 调用配置"""
    model: str = "deepseek-reasoner"
    temperature: float = 1.0
    fix_temperature: float = 0.3  # 修复时使用更低温度
    timeout: int = 300  # 请求超时（秒）
    max_retries: int = 2  # 最大重试次数
    streaming: bool = True
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """从环境变量加载配置"""
        return cls(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner"),
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "1.0")),
            fix_temperature=float(os.getenv("DEEPSEEK_FIX_TEMPERATURE", "0.3")),
            timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "300")),
            max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "2")),
            streaming=os.getenv("DEEPSEEK_STREAMING", "true").lower() == "true",
        )


@dataclass
class RetryConfig:
    """重试配置"""
    max_skeleton_retries: int = 2  # 骨架最大重试次数
    max_track_retries: int = 3  # 单个 Track 最大重试次数
    max_validation_retries: int = 3  # 验证最大重试次数
    max_batch_retries: int = 2  # 批次最大重试次数
    
    @classmethod
    def from_env(cls) -> "RetryConfig":
        """从环境变量加载配置"""
        return cls(
            max_skeleton_retries=int(os.getenv("SKILL_GEN_MAX_SKELETON_RETRIES", "2")),
            max_track_retries=int(os.getenv("SKILL_GEN_MAX_TRACK_RETRIES", "3")),
            max_validation_retries=int(os.getenv("SKILL_GEN_MAX_VALIDATION_RETRIES", "3")),
            max_batch_retries=int(os.getenv("SKILL_GEN_MAX_BATCH_RETRIES", "2")),
        )


@dataclass
class BatchConfig:
    """批次生成配置"""
    token_budget: int = 100000  # Token 预算
    min_batch_size: int = 2  # 最小批次大小
    max_batch_size: int = 6  # 最大批次大小
    context_window_size: int = 3  # 上下文窗口大小
    
    @classmethod
    def from_env(cls) -> "BatchConfig":
        """从环境变量加载配置"""
        return cls(
            token_budget=int(os.getenv("SKILL_GEN_TOKEN_BUDGET", "100000")),
            min_batch_size=int(os.getenv("SKILL_GEN_MIN_BATCH_SIZE", "2")),
            max_batch_size=int(os.getenv("SKILL_GEN_MAX_BATCH_SIZE", "6")),
            context_window_size=int(os.getenv("SKILL_GEN_CONTEXT_WINDOW", "3")),
        )


@dataclass
class RAGConfig:
    """RAG 检索配置"""
    skill_top_k: int = 3  # 技能检索数量
    action_top_k: int = 5  # Action 检索数量
    similarity_threshold: float = 0.5  # 相似度阈值
    
    @classmethod
    def from_env(cls) -> "RAGConfig":
        """从环境变量加载配置"""
        return cls(
            skill_top_k=int(os.getenv("RAG_SKILL_TOP_K", "3")),
            action_top_k=int(os.getenv("RAG_ACTION_TOP_K", "5")),
            similarity_threshold=float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.5")),
        )


@dataclass
class TimelineValidationConfig:
    """时间线验证配置"""
    audio_sync_tolerance: int = 15  # 动画和音效同步容差（帧）
    max_timeline_gap: int = 60  # 时间轴最大空白警告阈值（帧）
    damage_after_visual_delay: int = 5  # 伤害在视觉效果后的延迟（帧）
    effect_after_anim_delay: int = 3  # 特效在动画后的延迟（帧）
    
    @classmethod
    def from_env(cls) -> "TimelineValidationConfig":
        """从环境变量加载配置"""
        return cls(
            audio_sync_tolerance=int(os.getenv("TIMELINE_AUDIO_SYNC_TOLERANCE", "15")),
            max_timeline_gap=int(os.getenv("TIMELINE_MAX_GAP", "60")),
            damage_after_visual_delay=int(os.getenv("TIMELINE_DAMAGE_DELAY", "5")),
            effect_after_anim_delay=int(os.getenv("TIMELINE_EFFECT_DELAY", "3")),
        )


@dataclass
class MetricsConfig:
    """性能指标配置"""
    max_records: int = 1000  # 每种指标最多保留记录数
    log_interval_chars: int = 500  # 日志记录间隔（字符数）
    
    @classmethod
    def from_env(cls) -> "MetricsConfig":
        """从环境变量加载配置"""
        return cls(
            max_records=int(os.getenv("METRICS_MAX_RECORDS", "1000")),
            log_interval_chars=int(os.getenv("METRICS_LOG_INTERVAL", "500")),
        )


@dataclass
class SkillGenerationConfig:
    """技能生成总配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    timeline: TimelineValidationConfig = field(default_factory=TimelineValidationConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    
    @classmethod
    def from_env(cls) -> "SkillGenerationConfig":
        """从环境变量加载所有配置"""
        return cls(
            llm=LLMConfig.from_env(),
            retry=RetryConfig.from_env(),
            batch=BatchConfig.from_env(),
            rag=RAGConfig.from_env(),
            timeline=TimelineValidationConfig.from_env(),
            metrics=MetricsConfig.from_env(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict
        return asdict(self)


# 全局配置实例（单例）
_config: Optional[SkillGenerationConfig] = None


def get_skill_gen_config() -> SkillGenerationConfig:
    """获取技能生成配置（单例）"""
    global _config
    if _config is None:
        _config = SkillGenerationConfig.from_env()
        logger.info("SkillGenerationConfig initialized from environment")
    return _config


def reset_config():
    """重置配置（主要用于测试）"""
    global _config
    _config = None
