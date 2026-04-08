import httpx
from datetime import datetime
from typing import List, Tuple
from loguru import logger
from service.papers.schema import PaperInfo
from service.papers.search_api_provider import SearchAPIProvider

class CrossrefProvider(SearchAPIProvider):
    @property
    def api_name(self) -> str:
        return "Crossref"

    async def search_papers(self, query: str, start: int = 0, max_results: int = 10, api_key: str = "") -> Tuple[List[PaperInfo], int]:
        logger.info(f"搜索Crossref论文: query='{query}', start={start}, max={max_results}")
        
        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "offset": start,
            "rows": max_results,
            "select": "title,author,abstract,URL,published,link,DOI,subject"
        }
        
        headers = {
            "User-Agent": "DeepPaperResearcher/1.0 (mailto:admin@drap.com)"
        }
        # Crossref Plus API uses Crossref-Plus-API-Token header
        if api_key:
            headers["Crossref-Plus-API-Token"] = api_key
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                message = data.get("message", {})
                items = message.get("items", [])
                
                papers = []
                for item in items:
                    authors = []
                    for a in item.get("author", []):
                        name_parts = []
                        if a.get("given"): name_parts.append(a.get("given"))
                        if a.get("family"): name_parts.append(a.get("family"))
                        if name_parts:
                            authors.append(" ".join(name_parts))
                    
                    pdf_url = None
                    for link in item.get("link", []):
                        if link.get("content-type") == "application/pdf":
                            pdf_url = link.get("URL")
                            break
                            
                    pub_parts = None
                    if item.get("published"):
                        pub_parts = item["published"].get("date-parts", [[None]])[0]
                    elif item.get("created"):
                        pub_parts = item["created"].get("date-parts", [[None]])[0]
                        
                    pub_date = None
                    if pub_parts and pub_parts[0]:
                        year = pub_parts[0]
                        month = pub_parts[1] if len(pub_parts) > 1 and pub_parts[1] else 1
                        day = pub_parts[2] if len(pub_parts) > 2 and pub_parts[2] else 1
                        try:
                            pub_date = datetime(year, month, day)
                        except ValueError:
                            pass
                            
                    title_list = item.get("title", [])
                    title = title_list[0] if title_list else "Unknown Title"
                    
                    papers.append(PaperInfo(
                        title=title,
                        authors=authors,
                        abstract=item.get("abstract"),
                        paper_url=item.get("URL"),
                        pdf_url=pdf_url,
                        published_date=pub_date,
                        categories=item.get("subject", []),
                        source_id=item.get("DOI")
                    ))
                
                total = message.get("total-results", 0)
                return papers, total
                
        except Exception as e:
            logger.error(f"Crossref搜索失败: {e}", exc_info=True)
            raise e
