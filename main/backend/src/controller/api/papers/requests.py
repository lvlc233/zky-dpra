'''
开发者: BackendAgent
当前版本: v0.1_papers
创建时间: 2026年01月02日 10:16
更新时间: 2026年01月02日 10:16
更新记录:
    [2026年01月02日 10:16:v0.1_papers:重新定义PaperFetchRequest，符合Controller层职责]
    [2026年01月02日 08:54:v0.1_paper_requests:直接导入business_model，不符合规范]
'''

from pydantic import BaseModel


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


__all__ = ["PaperFetchRequest"]
