## 项目介绍

本项目主要目的是构建一个企业级的知识库系统，支持多模态数据（文本、图片等）的存储和检索。系统基于向量数据库 `Weaviate` 实现高效的相似度搜索，结合 `FastAPI` 提供高性能的API服务。通过集成多种开源技术栈，实现了一个可扩展、易维护的知识库解决方案，适用于各类企业的信息管理需求。

项目正在开发中，欢迎交流讨论。


## 主要技术栈

- 向量数据库: `Weaviate` 支持离线部署，docker 部署，开源免费。多租户，元数据管理。
- 缓存 `Redis`
- 数据库 `Postgresql`
- 异步调度 `Celery`
- python 框架 `FastAPI`，文档友好，天然支持高并发
- 鉴权  `python-jose[cryptography]`
- 分词  `hanlp`
- 文件存储 `minio`
- WSGI 服务器  `gunicorn`
- 部署 `docker-compose`


## 部署

- AI计算节点
    - `Weaviate`向量数据库
    - `Chinese-CLIP`多模态嵌入模型（文本和图像）
    - `minio` 对象存储系统
- 应用业务节点
    - `Postgresql` 数据库
    - `Redis` 缓存
    - `Celery` 异步任务调度
    - `FastAPI`主应用服务
