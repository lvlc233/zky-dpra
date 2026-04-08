from abc import ABC, abstractmethod
from typing import List, Tuple
from service.papers.schema import PaperInfo

class SearchAPIProvider(ABC):
    """
    Abstract base class for external search API providers wrapper.
    """
    
    @property
    @abstractmethod
    def api_name(self) -> str:
        """
        返回当前 API 的唯一标识名称，必须与 Settings.search_api_configs 中的 api_name 对应。
        """
        pass

    @abstractmethod
    async def search_papers(self, query: str, start: int = 0, max_results: int = 10, api_key: str = "") -> Tuple[List[PaperInfo], int]:
        """
        执行搜索操作。
        
        参数:
        - query: 最终构建好的查询字符串
        - start: 分页的起始偏移量
        - max_results: 每页期望的最大结果数
        - api_key: 数据库中为该 API 配置的 API Key（如果有则传入）
        
        返回:
        - (解析后的 PaperInfo 列表, 总记录数)
        """
        pass
