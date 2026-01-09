'''
开发者: BackendAgent
当前版本: v0.2_papers_upload
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月08日 17:30
更新记录:
    [2026年01月08日 17:30:v0.2_papers_upload:添加论文上传相关请求模型]
    [2026年01月02日 10:16:v0.1_papers:重新定义PaperFetchRequest，符合Controller层职责]
    [2026年01月02日 08:54:v0.1_paper_requests:直接导入business_model，不符合规范]
'''

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class PaperFetchRequest(BaseModel):
    '''
    论文集获取请求模型（Controller层）

    字段说明:
    - url: 论文集页面URL（如arXiv列表页或搜索结果页）
    - source: 论文来源（如'arXiv'），用于指定使用哪个数据源解析器

    使用场景:
    - Controller层接收前端传入的请求
    - FastAPI使用此模型自动验证请求参数
    - 验证通过后传递给Service层处理

    约束:
    - url为必填项，不能为空
    - source默认为"arXiv"，支持多学术网站

    注意:
    - 此模型专门用于Controller层接收请求
    - 不应该在business_model中定义请求模型
    '''
    url: str
    source: str = "arXiv"  # 默认为arXiv，后续可扩展其他来源如IEEE, ACM等


class PaperUploadRequest(BaseModel):
    '''
    论文上传请求模型（Controller层）

    字段说明:
    - title: 论文标题（可选，如果未提供则从PDF元数据提取）
    - authors: 作者列表（可选，如果未提供则从PDF元数据提取）

    使用场景:
    - Controller层接收前端上传的PDF文件
    - 与UploadFile一起使用，支持multipart/form-data
    - 验证通过后传递给PaperService处理

    注意:
    - 此模型用于接收表单字段
    - PDF文件通过UploadFile单独接收
    '''
    title: Optional[str] = None
    authors: Optional[str] = None  # JSON字符串格式

# TODO: 这里其实就是一个业务结果,应该放在业务模型中,并且只controller层应该创建一个通用的Response以此对所有的业务数据进行包装。
class PaperStatusResponse(BaseModel):
    '''
    论文状态响应模型

    字段说明:
    - paper_id: 论文唯一ID
    - status: 处理状态（pending/processing/completed/failed）
    - title: 论文标题
    - authors: 作者列表
    - abstract: 论文摘要
    - progress: 处理进度百分比（0-100）
    - error_message: 错误信息（如果处理失败）
    - created_at: 创建时间
    - updated_at: 更新时间
    '''
    paper_id: str
    status: str
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    progress: int = Field(default=0, ge=0, le=100, description="处理进度百分比")
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


__all__ = ["PaperFetchRequest", "PaperUploadRequest", "PaperStatusResponse"]
