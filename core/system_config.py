#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/10 23:15
@Author : YangFei
@File   : config.py
@Desc   : 系统配置项
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """ 项目配置类，从环境变量或 .env 文件加载配置，环境变量会忽略大小写 """

    # 项目环境，如 development、production 等
    env: str = "development"
    log_level: str = "DEBUG"

    # 数据库相关配置
    # 数据库异步操作连接字符串
    sqlalchemy_database_uri: str = "postgresql+asyncpg://postgres:12345678@localhost:5432/neon_rag"
    # 数据库表模型同步连接字符串（开发时使用）
    sqlalchemy_database_sync_uri: str = "postgresql+psycopg2://postgres:12345678@localhost:5432/neon_rag"

    # redis 相关配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_username: str | None = None
    redis_password: str | None = None
    redis_use_ssl: bool = False

    # minio 相关配置
    minio_endpoint: str = "127.0.0.1:9000" # MinIO 服务器地址，格式为 "host:port"
    minio_access_key: str = "minioadmin" # 就是访问账号
    minio_secret_key: str = "minioadmin123" # 就是访问密码
    minio_bucket_name: str = "neon-rag" # 存储桶名称
    minio_secure: bool = False  # 是否使用 HTTPS 连接 MinIO

    # 获取环境变量中的配置
    model_config = SettingsConfigDict(
        env_file=".env",  # 指定环境变量文件
        env_file_encoding="utf-8",  # 指定 .env 文件编码
        extra="ignore",  # 忽略未定义的环境变量，只加载这里已定义的配置项
    )

@lru_cache()
def get_settings() -> Settings:
    """ 获取配置实例，使用 lru_cache 缓存以提高性能, 避免重复创建获取配置实例 """
    return Settings()
