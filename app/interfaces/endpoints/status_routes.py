import logging
from fastapi import APIRouter

from app.interfaces.schemas import Response

logger = logging.getLogger(__name__)
status_router = APIRouter(prefix="/status", tags=["状态模块"])


@status_router.get("/", response_model=Response, summary="系统健康检查", description="检查系统是否运行正常。")
async def health_check():
    """ 健康检查接口，返回系统各服务的运行状态 """
    logger.debug("执行健康检查")

    # TODO: 实现具体的健康检查逻辑

    return Response.success()
