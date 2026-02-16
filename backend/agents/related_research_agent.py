import logging
from agents.base_agent import BaseAgent
from models.related import RelatedPaper, RelatedPaperSet
from services.semantic_scholar import SemanticScholarClient

logger = logging.getLogger("agent.related_research")


class RelatedResearchAgent(BaseAgent):
    """Agent 4: Related Research — finds and analyzes related papers via Semantic Scholar."""

    def __init__(self, llm_service):
        super().__init__("related_research", llm_service)
        self.scholar = SemanticScholarClient()

    async def run(self, input_data) -> RelatedPaperSet:
        if hasattr(input_data, "model_dump"):
            knowledge = input_data.model_dump()
        else:
            knowledge = input_data

        # Generate search queries from the knowledge card
        keywords = knowledge.get("keywords", [])
        problem = knowledge.get("problem_statement", "")
        methodology = knowledge.get("methodology", {}).get("approach", "")

        search_queries = []
        if keywords:
            search_queries.append(" ".join(keywords[:5]))
        if problem:
            search_queries.append(problem[:100])
        if methodology:
            search_queries.append(methodology[:100])

        # Search for related papers
        all_papers = []
        seen_titles = set()

        for query in search_queries[:3]:
            results = await self.scholar.search_papers(query, limit=8)
            for paper in results:
                title = paper.get("title", "")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_papers.append(paper)

        # Use LLM to score relevance and classify relationships
        related_papers = []
        for paper in all_papers[:15]:
            authors = paper.get("authors", [])
            author_names = [a.get("name", "") for a in authors] if isinstance(authors, list) else []

            related_papers.append(
                RelatedPaper(
                    title=paper.get("title", ""),
                    authors=author_names,
                    year=paper.get("year"),
                    venue=paper.get("venue", ""),
                    abstract=paper.get("abstract", "")[:500] if paper.get("abstract") else "",
                    relevance_score=0.0,
                    relationship_type="related",
                    mini_summary="",
                    url=paper.get("url"),
                )
            )

        # Use LLM to enrich with relevance scores and relationship types
        if related_papers and self.llm:
            related_papers = await self._enrich_with_llm(related_papers, knowledge)

        return RelatedPaperSet(
            papers=sorted(related_papers, key=lambda p: p.relevance_score, reverse=True),
            search_queries_used=search_queries,
            total_candidates_found=len(all_papers),
        )

    async def _enrich_with_llm(self, papers: list[RelatedPaper], knowledge: dict) -> list[RelatedPaper]:
        """Use LLM to score relevance and classify relationships."""
        paper_summaries = "\n".join(
            f"[{i}] {p.title} ({p.year}) - {p.abstract[:200]}"
            for i, p in enumerate(papers)
        )

        prompt = f"""Given the primary paper's focus:
Problem: {knowledge.get('problem_statement', '')}
Methodology: {knowledge.get('methodology', {}).get('approach', '')}
Keywords: {', '.join(knowledge.get('keywords', []))}

Analyze these related papers and for each, provide:
- relevance_score (0.0 to 1.0)
- relationship_type: one of "extends", "contradicts", "applies", "precedes", "related"
- mini_summary: 1-2 sentence summary of how it relates

Related papers:
{paper_summaries}

Return a JSON array with objects containing: index, relevance_score, relationship_type, mini_summary"""

        try:
            result = await self.llm.generate_json(prompt)
            if isinstance(result, list):
                enrichments = result
            elif isinstance(result, dict) and "papers" in result:
                enrichments = result["papers"]
            else:
                enrichments = []

            for item in enrichments:
                idx = item.get("index", -1)
                if 0 <= idx < len(papers):
                    papers[idx].relevance_score = float(item.get("relevance_score", 0.5))
                    papers[idx].relationship_type = item.get("relationship_type", "related")
                    papers[idx].mini_summary = item.get("mini_summary", "")
        except Exception as e:
            logger.warning(f"LLM enrichment failed: {e}")
            for p in papers:
                p.relevance_score = 0.5

        return papers
