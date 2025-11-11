"""API 依赖项管理.

包含 FastAPI 应用的依赖项、配置管理和共享服务。
"""

import logging
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """应用配置设置."""

    # API 配置
    api_title: str = "LLM Web Kit API"
    api_version: str = "1.0.0"
    api_description: str = "基于 LLM 的 Web 内容解析和提取 API 服务"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # 日志配置
    log_level: str = "INFO"

    # 模型配置
    model_path: Optional[str] = None
    max_content_length: int = 10 * 1024 * 1024  # 10MB
    crawl_url: str = "http://10.140.0.94:9500/crawl"

    # 缓存配置
    cache_ttl: int = 3600  # 1小时

    # 数据库配置
    database_url: Optional[str] = None  # 从环境变量 DATABASE_URL 读取
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # pydantic v2 配置写法
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置单例."""
    return Settings()


def get_logger(name: str = __name__) -> logging.Logger:
    """获取配置好的日志记录器."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(get_settings().log_level)
    return logger


# 全局依赖项
settings = get_settings()

# InferenceService 单例
_inference_service_singleton = None


def get_inference_service():
    """获取 InferenceService 单例."""
    global _inference_service_singleton
    if _inference_service_singleton is None:
        from .services.inference_service import InferenceService
        _inference_service_singleton = InferenceService()
    return _inference_service_singleton
