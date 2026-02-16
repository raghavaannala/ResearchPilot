from pydantic import BaseModel
from typing import Optional


class RelatedPaper(BaseModel):
    title: str
    authors: list[str] = []
    year: Optional[int] = None
    venue: Optional[str] = None
    abstract: str = ""
    relevance_score: float = 0.0
    relationship_type: str = "related"
    mini_summary: str = ""
    url: Optional[str] = None


class RelatedPaperSet(BaseModel):
    papers: list[RelatedPaper] = []
    search_queries_used: list[str] = []
    total_candidates_found: int = 0
