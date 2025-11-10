#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/11 00:10
@Author : YangFei
@File   : minio.py
@Desc   : 本地 MinIO 存储实现类，用于与 MinIO 对象存储服务交互
"""
import logging
from typing import Optional
from functools import lru_cache

from minio import Minio
from minio.error import S3Error

from core.system_config import get_settings

logger = logging.getLogger(__name__)

class MinIO:
    """ MinIO 客户端封装类 """

    def __init__(self):
        """ 构造函数，完成 MinIO 客户端的初始化 """
        self._client: Optional[Minio] = None
        self._settings = get_settings()

    async def init(self) -> None:
        """ 初始化 MinIO 连接 """
        if self._client:
            logger.warning("MinIO 客户端已初始化，跳过重复初始化")
            return

        try:
            # 创建 MinIO 客户端实例
            self._client = Minio(
                endpoint=self._settings.minio_endpoint,
                access_key=self._settings.minio_access_key,
                secret_key=self._settings.minio_secret_key,
                secure=self._settings.minio_secure,
            )
            # 测试连接
            self._client.list_buckets()
            logger.info("MinIO 客户端初始化成功")
        except S3Error as e:
            logger.error("初始化 MinIO 客户端失败: %s", e)
            raise

    async def shutdown(self) -> None:
        """ 关闭 MinIO 连接 """
        if self._client:
            self._client = None

        get_minio.cache_clear()
        logger.info("MinIO 客户端连接已关闭")

    @property
    def client(self) -> Minio:
        """ 获取 MinIO 客户端实例, 只读属性 """
        if not self._client:
            raise RuntimeError("MinIO 客户端未初始化，请先调用 init 方法")
        return self._client


@lru_cache()
def get_minio() -> MinIO:
    """ 获取 MinIO 客户端实例，使用 lru_cache 缓存以提高性能，避免重复创建实例 """
    return MinIO()