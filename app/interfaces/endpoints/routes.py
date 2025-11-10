from fastapi import APIRouter
from .status_routes import status_router


def create_routes() -> APIRouter:
    """ 创建并返回应用的主路由器，包含所有子路由器 """
    # 创建主路由器
    main_router = APIRouter()

    # 包含状态模块路由
    main_router.include_router(status_router)

    # 返回主路由器
    return main_router


router = create_routes()
