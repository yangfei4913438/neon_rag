import logging
from redis.asyncio import Redis
from functools import lru_cache

from core.system_config import get_settings, Settings

logger = logging.getLogger(__name__)


class RedisClient:
    """ Redis 客户端封装类 """

    def __init__(self):
        """ 构造函数，完成 Redis 客户端的初始化 """
        self._client: Redis | None = None
        self._settings: Settings = get_settings()

    async def init(self) -> None:
        """ 初始化 Redis 连接 """
        # 判断客户端是否存在
        if self._client:
            logger.warning("Redis 客户端已初始化，跳过重复初始化")
            return

        try:
            # 创建 Redis 客户端实例
            self._client = Redis(
                host=self._settings.redis_host,
                port=self._settings.redis_port,
                db=self._settings.redis_db,
                username=self._settings.redis_username,
                password=self._settings.redis_password,
                ssl=self._settings.redis_use_ssl,
                decode_responses=True,  # 自动解码响应数据为字符串
            )

            # 测试连接
            await self._client.ping()  # type: ignore # 忽略类型检查警告

            logger.info("Redis 客户端初始化成功")
        except Exception as e:
            logger.error("初始化 Redis 客户端失败: %s", e)
            raise

    async def shutdown(self) -> None:
        """ 关闭 Redis 连接 """
        # 如果客户端存在，则关闭连接
        if self._client:
            await self._client.aclose()
            self._client = None

        # 清除缓存(避免重复使用已关闭的客户端)
        get_redis.cache_clear()

        # 输出日志
        logger.info("Redis 客户端连接已关闭")

    @property
    def client(self) -> Redis:
        """ 获取 Redis 客户端实例, 只读属性 """
        if not self._client:
            raise RuntimeError("Redis 客户端未初始化，请先调用初始化方法。")
        return self._client


@lru_cache()
def get_redis() -> RedisClient:
    """ 获取 Redis 实例，使用 lru_cache 缓存以提高性能，避免重复创建 """
    return RedisClient()
