import httpx
from datetime import datetime
from typing import List, Tuple
from loguru import logger
from service.papers.schema import PaperInfo
from service.papers.search_api_provider import SearchAPIProvider

class SemanticScholarProvider(SearchAPIProvider):
    @property
    def api_name(self) -> str:
        return "Semantic Scholar"

    async def search_papers(self, query: str, start: int = 0, max_results: int = 10, api_key: str = "") -> Tuple[List[PaperInfo], int]:
        logger.info(f"搜索SemanticScholar论文: query='{query}', start={start}, max={max_results}")
        
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "offset": start,
            "limit": max_results,
            "fields": "title,authors,abstract,url,year,publicationDate,openAccessPdf,venue,externalIds"
        }
        
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                papers = []
                for item in data.get("data", []):
                    authors = [a.get("name") for a in item.get("authors", [])] if item.get("authors") else []
                    
                    pdf_url = None
                    if item.get("openAccessPdf"):
                        pdf_url = item["openAccessPdf"].get("url")
                        
                    pub_date_str = item.get("publicationDate")
                    pub_date = None
                    if pub_date_str:
                        try:
                            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                        except ValueError:
                            pass
                            
                    source_id = None
                    if item.get("externalIds") and item["externalIds"].get("ArXiv"):
                        source_id = item["externalIds"]["ArXiv"]
                    elif item.get("paperId"):
                        source_id = item.get("paperId")
                        
                    url_val = item.get("url")
                        
                    papers.append(PaperInfo(
                        title=item.get("title", "Unknown Title"),
                        authors=authors,
                        abstract=item.get("abstract"),
                        paper_url=url_val,
                        pdf_url=pdf_url,
                        published_date=pub_date,
                        categories=[],
                        source_id=source_id
                    ))
                
                total = data.get("total", 0)
                return papers, total
                
        except Exception as e:
            logger.error(f"SemanticScholar搜索失败: {e}", exc_info=True)
            raise e
