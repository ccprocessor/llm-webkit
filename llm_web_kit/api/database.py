"""数据库连接管理.

提供数据库连接池和会话管理功能。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from .dependencies import get_logger, get_settings
from .models.db_models import Base

logger = get_logger(__name__)
settings = get_settings()


class DatabaseManager:
    """数据库管理器."""

    def __init__(self):
        """初始化数据库管理器."""
        self._engine = None
        self._async_session_maker = None
        self._initialized = False

    def initialize(self):
        """初始化数据库连接."""
        if self._initialized:
            return

        try:
            # 检查是否配置了数据库连接
            if not settings.database_url:
                logger.warning("未配置数据库连接，请求日志功能将被禁用")
                return

            # 创建异步引擎
            self._engine = create_async_engine(
                settings.database_url,
                echo=settings.debug,
                pool_pre_ping=True,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
            )

            # 创建异步会话工厂
            self._async_session_maker = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            self._initialized = True
            logger.info("数据库连接初始化成功")

        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            self._initialized = False

    async def create_tables(self):
        """创建数据库表."""
        if not self._engine:
            logger.warning("数据库引擎未初始化，跳过创建表")
            return

        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Optional[AsyncSession], None]:
        """获取数据库会话上下文管理器."""
        if not self._async_session_maker:
            logger.warning("数据库会话工厂未初始化")
            yield None
            return

        session = self._async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()

    async def close(self):
        """关闭数据库连接."""
        if self._engine:
            await self._engine.dispose()
            logger.info("数据库连接已关闭")


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器单例."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager


async def get_db_session() -> AsyncGenerator[Optional[AsyncSession], None]:
    """FastAPI 依赖项：获取数据库会话."""
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session
