import logging
from typing import Optional, AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from functools import lru_cache

from core.system_config import get_settings

# 为该模块配置日志记录器
logger = logging.getLogger(__name__)


class Postgres:
    """  Postgres 存储实现类，用于与 PostgreSQL 数据库交互"""

    def __init__(self):
        """ 完成 postgres 存储的初始化工作，如建立数据库连接等 """
        # 初始化成员变量
        # 异步引擎，用于与数据库进行异步通信
        self._engine: Optional[AsyncEngine] = None
        # 创建异步会话工厂，async_sessionmaker 是 SQLAlchemy 提供的异步会话生成器
        self._session_factory: Optional[async_sessionmaker] = None
        # 获取应用程序设置
        self._settings = get_settings()

    async def init(self):
        """ 初始化数据库连接 """
        if self._engine is not None:
            logger.warning("Postgres引擎已经初始化.")
            return

        try:
            # 创建异步引擎
            self._engine = create_async_engine(
                self._settings.sqlalchemy_database_uri,
                # 根据环境决定是否启用 SQLAlchemy 的 SQL 语句日志记录(调试模式下启用，打印所有执行的 SQL 语句)
                echo=True if self._settings.env == "development" else False,
            )
            logger.info("Postgres引擎初始化成功.")

            # 创建异步会话工厂
            self._session_factory = async_sessionmaker(
                bind=self._engine,  # 绑定到刚创建的引擎
                autocommit=False,  # 设置为 False 以防止自动提交
                autoflush=False,  # 设置为 False 以防止自动刷新
            )
            logger.info("Postgres会话工厂初始化成功.")

            # 连接数据库并执行初始命令
            async with self._engine.begin() as async_conn:
                # 检查是否安装了 uuid-ossp 扩展,如果没有则安装它
                await async_conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
                logger.info("成功连接Postgres数据库，并确认扩展 uuid-ossp 已安装.")

        except Exception as e:
            logger.error("初始化Postgres引擎时出错: %s", e)
            raise

    async def shutdown(self):
        """ 关闭数据库连接 """
        # 检查引擎是否已初始化
        if self._engine:
            # 关闭引擎连接
            await self._engine.dispose()

        # 重置成员变量
        self._engine = None
        self._session_factory = None

        # 清除缓存以确保下次获取实例时重新创建
        get_postgres.cache_clear()

        logger.info("Postgres 连接已成功关闭.")

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """ 获取异步会话工厂 """
        if self._session_factory is None:
            raise RuntimeError("Postgres引擎未初始化，请先调用 init 方法进行初始化.")
        return self._session_factory


@lru_cache()
def get_postgres() -> Postgres:
    """ 获取 Postgres 存储实例，使用 LRU 缓存以确保单例模式 """
    return Postgres()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """ fastapi依赖注入函数，用于在每个请求中异步获取数据库会话实例，确保会话的正确创建和关闭 """
    # 获取 Postgres 存储实例
    db = get_postgres()
    session_factory = db.session_factory

    # 使用异步上下文管理器确保会话的正确关闭
    async with session_factory() as session:
        try:
            # 通过 yield 提供会话实例给调用者
            yield session
            # 提交会话中的更改
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("数据库会话中发生错误: %s, 执行回滚操作。", e)
            raise
