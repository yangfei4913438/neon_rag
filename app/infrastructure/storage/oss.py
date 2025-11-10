#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/6 21:17
@Author : YangFei
@File   : oss.py
@Desc   :
"""
import logging
from typing import Optional
from functools import lru_cache

from oss2 import Bucket, Auth
from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

from core.system_config import get_settings, Settings

logger = logging.getLogger(__name__)


class OSS:
    """ 阿里云对象存储服务封装类 """

    def __init__(self):
        """ 初始化 OSS 实例, 完成配置获取和客户端初始化 """
        self._settings: Settings = get_settings()
        self._client: Optional[Bucket] = None

    async def init(self) -> None:
        """ 初始化 OSS 客户端 """
        if self._client:
            logger.warning("OSS 客户端已初始化，跳过重复初始化")
            return

        try:
            # 创建认证对象
            auth = Auth(
                access_key_id=self._settings.oss_access_key_id,
                access_key_secret=self._settings.oss_access_key_secret,
            )

            # 创建 Bucket 客户端实例
            self._client = Bucket(
                auth=auth,
                endpoint=self._settings.oss_endpoint,
                bucket_name=self._settings.oss_bucket_name,
            )

            # 设置 Bucket 生命周期规则，例如自动删除 30 天前的临时文件
            rule = LifecycleRule(
                id='temp_files_rule',
                prefix='temp_files/',
                status=LifecycleRule.ENABLED,
                expiration=LifecycleExpiration(days=30)  # 30 天过期
            )
            # 创建生命周期规则对象
            lifecycle = BucketLifecycle([rule])
            # 应用生命周期规则到 Bucket
            self._client.put_bucket_lifecycle(lifecycle)

            logger.info("OSS 客户端初始化成功")
        except Exception as e:
            logger.error("初始化 OSS 客户端失败: %s", e)
            raise

    async def shutdown(self) -> None:
        """ 关闭 OSS 客户端连接 """
        if self._client is not None:
            # 关闭客户端连接
            if self._client.session and self._client.session.session:
                # 关闭会话
                self._client.session.session.close()
        # 清除客户端实例
        self._client = None
        # 清除缓存(避免重复使用已关闭的客户端)
        get_oss.cache_clear()

        logger.info("OSS 客户端连接已关闭")

    @property
    def client(self) -> Bucket:
        """ 获取 OSS 客户端实例, 只读属性 """
        if not self._client:
            raise RuntimeError("OSS 客户端未初始化，请先调用初始化方法。")
        return self._client

    def file_exists(self, file_path: str) -> bool:
        """ 检查文件是否存在于 OSS
        :param file_path: 文件在 OSS 中的路径, 例如 'folder/file.txt'
        :return: 如果文件存在则返回 True，否则返回 False
        """
        if not self._client:
            raise RuntimeError("OSS 客户端未初始化，请先调用初始化方法。")

        # 检查文件是否存在
        return self._client.object_exists(file_path)

    def file_upload(self, file_path: str, file_content: bytes, header: Optional[dict] = None):
        """ 上传文件到 OSS, 并返回文件的访问 URL """
        if not self._client:
            raise RuntimeError("OSS 客户端未初始化，请先调用初始化方法。")

        # 上传文件到指定路径
        result = self._client.put_object(
            file_path, file_content, headers=header or {})
        if result.status != 200:
            raise RuntimeError(
                f"上传文件到 OSS 失败，请检查相关配置和网络连接。状态码: {result.status}")
        else:
            logger.info("文件成功上传到 OSS，路径: %s", file_path)

    def upload_temp_file(self, file_path: str, file_content: bytes, header: Optional[dict] = None):
        """ 上传临时文件到 OSS, 并返回文件的访问 URL """
        if not self._client:
            raise RuntimeError("OSS 客户端未初始化，请先调用初始化方法。")

        # 上传文件到临时文件目录
        self.file_upload(f"temp_files/{file_path}", file_content, header)

    def file_download(self, file_path: str, local_file_path: str):
        """ 从 OSS 下载文件到本地 """
        if not self._client:
            raise RuntimeError("OSS 客户端未初始化，请先调用初始化方法。")

        try:
            # 检查文件是否存在
            if not self.file_exists(file_path):
                raise FileNotFoundError(f"OSS 上未找到文件: {file_path}")

            # 下载文件到本地指定路径
            self._client.get_object_to_file(file_path, local_file_path)
        except Exception as e:
            logger.error("从 OSS 下载文件失败: %s", e)
            raise

    def file_rename(self, old_file_path: str, new_file_path: str):
        """ 重命名 OSS 上的文件 """
        if not self._client:
            raise RuntimeError("OSS 客户端未初始化，请先调用初始化方法。")

        try:
            # 复制旧文件到新文件路径
            self._client.copy_object(
                source_bucket_name=self._settings.oss_bucket_name,
                source_key=old_file_path,
                target_key=new_file_path
            )
            # 删除旧文件
            self._client.delete_object(old_file_path)
            # 记录日志
            logger.info("OSS 文件重命名成功: %s -> %s", old_file_path, new_file_path)
        except Exception as e:
            logger.error("重命名 OSS 文件失败: %s", e)
            raise

    def delete_file(self, file_path: str):
        """ 删除 OSS 上的文件 """
        if not self._client:
            raise RuntimeError("OSS 客户端未初始化，请先调用初始化方法。")

        try:
            # 删除指定路径的文件
            self._client.delete_object(file_path)
        except Exception as e:
            logger.error("删除 OSS 文件失败: %s", e)
            raise

    def delete_files(self, file_paths: list[str]):
        """ 批量删除 OSS 上的文件 """
        if not self._client:
            raise RuntimeError("OSS 客户端未初始化，请先调用初始化方法。")

        try:
            # 批量删除文件
            self._client.batch_delete_objects(file_paths)
        except Exception as e:
            logger.error("批量删除 OSS 文件失败: %s", e)
            raise


@lru_cache()
def get_oss() -> OSS:
    """ 获取 OSS 实例，使用 lru_cache 缓存以提高性能, 避免重复创建获取 OSS 实例 """
    return OSS()
