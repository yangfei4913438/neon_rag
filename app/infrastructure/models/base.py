#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/06 14:30
@Author : YangFei
@File   : base.py
@Desc   : 定义基础模型类，所有ORM模型都将继承自此类
"""

from sqlalchemy.orm import declarative_base

# 定义基础模型类，所有ORM模型都将继承自此类
Base = declarative_base()
