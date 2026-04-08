import httpx
from datetime import datetime
from typing import Any
from loguru import logger
from service.papers.schema import PaperInfo
from service.papers.search_api_provider import SearchAPIProvider

class CoreProvider(SearchAPIProvider):
    @property
    def api_name(self) -> str:
        return "CORE"

    async def search_papers(self, query: str, start: int = 0, max_results: int = 10, api_key: str | None = None) -> tuple[list[PaperInfo], int]:
        """
        Search CORE for papers.
        Documentation: https://api.core.ac.uk/docs/v3
        """
        logger.info(f"搜索CORE论文: query='{query}', start={start}, max={max_results}")
        
        if not api_key:
            logger.warning("CORE API 需要 API Key 才能工作。请在设置中配置。")
            return [], 0
            
        url = "https://api.core.ac.uk/v3/search/works/"
        
        # CORE API parameters
        params = {
             "q": query,
             "limit": max_results,
             "offset": start
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "DeepPaperResearcher/1.0"
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, params=params, headers=headers, timeout=15.0)
                
                if response.status_code == 401:
                    logger.error("CORE API Key 无效或未授权。")
                    return [], 0
                elif response.status_code == 429:
                    logger.error("CORE API 请求过于频繁 (Rate Limited)。")
                    return [], 0
                    
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                total_count = data.get("totalHits", 0)
                
                papers = []
                for item in results:
                    # 1. Title
                    title = item.get("title") or "Unknown Title"
                    
                    # 2. Authors
                    authors = []
                    for auth in item.get("authors", []):
                        author_name = auth.get("name", "").strip()
                        if author_name:
                            authors.append(author_name)
                    
                    # 3. Abstract
                    abstract = item.get("abstract")
                    
                    # 4. Dates
                    pub_date = None
                    pub_date_str = item.get("publishedDate")
                    if pub_date_str:
                        # CORE usually returns YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
                        try:
                            if "T" in pub_date_str:
                                pub_date = datetime.fromisoformat(pub_date_str.split("T")[0])
                            else:
                                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                        except ValueError:
                            # Try just year
                            try:
                                # Improvement: fallback to YYYY-01-01
                                year = int(pub_date_str[:4])
                                pub_date = datetime(year, 1, 1)
                            except:
                                pass
                    
                    # 5. PDF URL (downloadUrl)
                    pdf_url = item.get("downloadUrl")
                    
                    # Filter: Only include papers with a download URL to ensure 'free' access
                    if not pdf_url:
                        continue
                        
                    # 6. Paper URL (DOI or URL)
                    paper_url = item.get("doi") or item.get("fullTextUrl") or f"https://core.ac.uk/works/{item.get('id')}"
                    
                    papers.append(PaperInfo(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        paper_url=paper_url,
                        pdf_url=pdf_url,
                        published_date=pub_date,
                        categories=[], # CORE subject mapping is complex
                        source_id=item.get("doi") or str(item.get("id"))
                    ))
                
                return papers, total_count
                
        except Exception as e:
            logger.error(f"CORE搜索失败: {e}", exc_info=True)
            return [], 0
