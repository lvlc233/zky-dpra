import httpx
from datetime import datetime
from typing import Any
from loguru import logger
from service.papers.schema import PaperInfo
from service.papers.search_api_provider import SearchAPIProvider

class OpenAlexProvider(SearchAPIProvider):
    @property
    def api_name(self) -> str:
        return "OpenAlex"

    async def search_papers(self, query: str, start: int = 0, max_results: int = 10, api_key: str | None = None) -> tuple[list[PaperInfo], int]:
        """
        Search OpenAlex for papers.
        Documentation: https://docs.openalex.org/api-entities/works
        """
        logger.info(f"搜索OpenAlex论文: query='{query}', start={start}, max={max_results}")
        
        url = "https://api.openalex.org/works"
        
        # OpenAlex uses per_page and page or offset/limit
        # We use search param for simple search
        params = {
            "search": query,
            "per_page": max_results,
            "page": (start // max_results) + 1,
            "filter": "is_oa:true",
            # Polite pool (optional but recommended)
            "mailto": "admin@dpra.com"
        }
        
        if api_key:
            # OpenAlex Premium uses api_key param or header if applicable
            params["api_key"] = api_key
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=15.0)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                meta = data.get("meta", {})
                total_count = meta.get("count", 0)
                
                papers = []
                for item in results:
                    # 1. Title
                    title = item.get("display_name") or "Unknown Title"
                    
                    # 2. Authors
                    authors = []
                    for auth in item.get("authorships", []):
                        author_name = auth.get("author", {}).get("display_name")
                        if author_name:
                            authors.append(author_name)
                    
                    # 3. Abstract (Inverted Index)
                    abstract = self._reconstruct_abstract(item.get("abstract_inverted_index"))
                    
                    # 4. Dates
                    pub_date = None
                    pub_date_str = item.get("publication_date")
                    if pub_date_str:
                        try:
                            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                        except ValueError:
                            pass
                    
                    if not pub_date and item.get("publication_year"):
                        try:
                            pub_date = datetime(item["publication_year"], 1, 1)
                        except:
                            pass
                    
                    # 5. PDF URL (Best Open Access Location)
                    pdf_url = None
                    best_oa = item.get("best_oa_location")
                    if best_oa:
                        pdf_url = best_oa.get("pdf_url")
                    
                    # If no PDF URL, check other locations
                    if not pdf_url:
                        for loc in item.get("locations", []):
                            if loc.get("pdf_url"):
                                pdf_url = loc.get("pdf_url")
                                break
                    
                    # If is_oa:true is requested, skip papers that have NO PDF URL at all
                    # (To prevent importing landing pages that fail to load as PDF)
                    if params.get("filter") == "is_oa:true" and not pdf_url:
                        logger.info(f"跳过没有直接PDF链接的OA论文: {title}")
                        continue
                    
                    # 6. Paper URL (DOI or landing page)
                    paper_url = item.get("doi") or item.get("id")
                    
                    papers.append(PaperInfo(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        paper_url=paper_url,
                        pdf_url=pdf_url,
                        published_date=pub_date,
                        categories=[topic.get("display_name") for topic in item.get("topics", []) if topic.get("display_name")],
                        source_id=item.get("doi")
                    ))
                
                return papers, total_count
                
        except Exception as e:
            logger.error(f"OpenAlex搜索失败: {e}", exc_info=True)
            # Don't raise, just return empty to allow other providers to work
            return [], 0

    def _reconstruct_abstract(self, inverted_index: dict[str, list[int]] | None) -> str | None:
        """
        Reconstruct abstract from OpenAlex's inverted index format.
        """
        if not inverted_index:
            return None
            
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        
        # Sort by position
        word_positions.sort()
        
        # Join words
        return " ".join([word for pos, word in word_positions])
