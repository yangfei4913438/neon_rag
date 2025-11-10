#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/10 23:17
@Author : YangFei
@File   : main.py
@Desc   : 入口文件
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from core.system_config import get_settings
from core.log_config import setup_logging

from app.interfaces.endpoints import router
from app.interfaces.errors import register_exception_handlers

from app.infrastructure.storage.redis import get_redis
from app.infrastructure.storage.postgres import get_postgres
from app.infrastructure.storage.minio import get_minio

# 1. 获取配置实例(一定要基于 fastapi 项目运行，否则路径解析会出问题，例如找不到 core 模块)
settings = get_settings()

# 2. 初始化日志系统
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ 创建 FastAPI 应用的异步生命周期的上下文管理器 """
    # 启动时初始化资源
    logger.info("Neon Rag 正在初始化...")

    # 初始化 Redis、Postgres 和 OSS 客户端
    await get_redis().init()
    await get_postgres().init()
    await get_minio().init()

    try:
        # yield 之前的代码在应用启动时执行
        yield  # 生命周期中间点

        # yield 之后的代码在应用关闭时执行
    finally:
        # 关闭时释放资源
        logger.info("Neon Rag 正在关闭...")
        # 关闭 Redis、Postgres 和 OSS 客户端连接
        await get_redis().shutdown()
        await get_postgres().shutdown()
        await get_minio().shutdown()


# 3. 定义 FastAPI 路由 tags 标签
tags_metadata = [
    {
        "name": "状态模块",
        "description": "包含 **状态检测** 等 API 接口。用于检测系统的运行状态。",
    },
]

# 4. 创建 FastAPI 应用实例
app = FastAPI(
    title="NeonRag企业级知识库平台",
    description="一个开源的企业级知识库系统，专为本地部署设计。专注于文档的处理，支持多种文本和图片格式文件的上传与管理，帮助企业高效的管理内部知识资源。",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,  # 异步生命周期管理
)


# 5. 添加跨域中间件
app.add_middleware(
    # 可在此添加中间件，例如 CORS、请求日志等
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源访问
    allow_credentials=True,  # 允许携带凭证
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有请求头
)

# 6. 注册全局异常处理器
register_exception_handlers(app)

# 7. 导入并注册路由
app.include_router(router=router, prefix="/api")

# 开发环境启动项目
# 使用 . 替代路径中的 /，避免跨平台问题
# uvicorn app.main:app --reload