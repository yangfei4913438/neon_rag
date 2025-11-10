#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/6 22:17
@Author : YangFei
@File   : demo.py
@Desc   : 
"""
import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UUID, String, Text, DateTime
from sqlalchemy import PrimaryKeyConstraint, text

from .base import Base


class Demo(Base):
    """ 示例模型类，演示如何定义ORM模型 """
    __tablename__ = 'demo'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_demo_id'),
    )

    # Mapped 是 SQLAlchemy 2.0 引入的类型注解，用于声明模型字段的类型。
    id: Mapped[uuid.UUID] = mapped_column(
        # as_uuid=True：将数据库中存储的 UUID 字符串自动转换为 Python 的 uuid.UUID 对象，方便代码中直接使用 UUID 类型的方法（如比较、格式化等）
        UUID(as_uuid=True),
        primary_key=True,  # 设置为主键
        # server_default：指定数据库层面的默认值生成规则，插入新记录时若未手动指定 id，PostgreSQL 会自动调用 uuid_generate_v4() 生成 UUID
        # uuid_generate_v4() 是 PostgreSQL 生成随机 UUID 的内置函数
        server_default=text('uuid_generate_v4()'),
        comment="主键ID"  # 添加字段注释
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default=text("''::character varying"),  # 设置默认值为空字符串, 可变长度字符类型
        comment="名称"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("''::text"),  # 设置默认值为空字符串
        comment="描述"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),  # 设置默认值为当前时间，时间戳精度为0
        onupdate=datetime.now,  # 每次更新记录时，自动设置为当前时间
        comment="更新时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),  # 设置默认值为当前时间，时间戳精度为0
        comment="创建时间"
    )
