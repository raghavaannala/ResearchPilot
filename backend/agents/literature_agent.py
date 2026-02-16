import logging
from agents.base_agent import BaseAgent
from models.review import LiteratureReview, ThematicGroup

logger = logging.getLogger("agent.literature")


class LiteratureAgent(BaseAgent):
    """Agent 5: Literature Review — synthesizes a structured literature review."""

    def __init__(self, llm_service):
        super().__init__("literature_review", llm_service)

    async def run(self, input_data: dict) -> LiteratureReview:
        knowledge = input_data.get("knowledge", {})
        related = input_data.get("related", {})

        if hasattr(knowledge, "model_dump"):
            knowledge = knowledge.model_dump()
        if hasattr(related, "model_dump"):
            related = related.model_dump()

        papers = related.get("papers", [])
        if not papers:
            return LiteratureReview(
                introduction="No related papers found to build a literature review.",
                conclusion="Insufficient data for literature review.",
            )

        # Build paper summaries for the LLM
        paper_list = "\n".join(
            f"- [{p.get('title', 'Unknown')}] ({p.get('year', 'N/A')}) [{p.get('venue', '')}]: "
            f"{p.get('abstract', '')[:300]}"
            for p in papers[:15]
        )

        prompt = f"""Based on the primary research paper and related papers below, generate a comprehensive literature review.

PRIMARY PAPER:
Problem: {knowledge.get('problem_statement', '')}
Methodology: {knowledge.get('methodology', {}).get('approach', '')}
Keywords: {', '.join(knowledge.get('keywords', []))}

RELATED PAPERS:
{paper_list}

Return a JSON object with:
- introduction: 2-3 paragraphs introducing the research area
- thematic_groups: Array of objects, each with: theme (string), papers (array of paper titles), summary (paragraph)
- chronological_narrative: 2-3 paragraphs describing how the field evolved
- comparison_table: Array of objects with: paper (title), method, dataset, result
- methodology_evolution: Paragraph on how methodologies have evolved
- conclusion: Summary paragraph
- citation_count: total number of papers reviewed"""

        result = await self.llm.generate_json(prompt)

        groups = []
        for g in result.get("thematic_groups", []):
            groups.append(ThematicGroup(
                theme=g.get("theme", ""),
                papers=g.get("papers", []),
                summary=g.get("summary", ""),
            ))

        return LiteratureReview(
            introduction=result.get("introduction", ""),
            thematic_groups=groups,
            chronological_narrative=result.get("chronological_narrative", ""),
            comparison_table=result.get("comparison_table", []),
            methodology_evolution=result.get("methodology_evolution", ""),
            conclusion=result.get("conclusion", ""),
            citation_count=result.get("citation_count", len(papers)),
        )
