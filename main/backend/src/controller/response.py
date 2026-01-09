"""
开发者: BackendAgent
创建时间: 2026年01月10日
描述: 统一响应结构与全局异常处理
"""

from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from common.utils import get_now_time_china
from common.model.errors import BaseAppException

logger = logging.getLogger(__name__)

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: str = get_now_time_china()

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "Response[T]":
        return cls(code=200, message=message, data=data, timestamp=get_now_time_china())

    @classmethod
    def fail(cls, code: int = 400, message: str = "error", data: Any = None) -> "Response[None]":
        return cls(code=code, message=message, data=data, timestamp=get_now_time_china())

async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    
    # 1. 处理自定义业务异常
    if isinstance(exc, BaseAppException):
        logger.warning(f"业务异常: {exc.message} (code={exc.code})")
        return JSONResponse(
            status_code=exc.code if 400 <= exc.code < 600 else 400, # 保持 HTTP 状态码合理
            content=Response.fail(code=exc.code, message=exc.message, data=exc.data).model_dump()
        )
        
    # 2. 处理 FastAPI/Starlette HTTP 异常
    if isinstance(exc, StarletteHTTPException):
        logger.warning(f"HTTP异常: {exc.detail} (status={exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content=Response.fail(code=exc.status_code, message=str(exc.detail)).model_dump()
        )

    # 3. 处理参数验证异常
    if isinstance(exc, RequestValidationError):
        logger.warning(f"参数验证失败: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=Response.fail(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                message="参数验证失败", 
                data=exc.errors()
            ).model_dump()
        )

    # 4. 处理其他未知异常 (500)
    logger.error(f"服务器内部错误: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=Response.fail(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            message="服务器内部错误，请联系管理员"
        ).model_dump()
    )
