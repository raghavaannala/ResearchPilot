import logging
from agents.base_agent import BaseAgent
from models.gaps import GapAnalysis, ResearchGap, FutureDirection

logger = logging.getLogger("agent.gap_analysis")


class GapAnalysisAgent(BaseAgent):
    """Agent 6: Gap & Future Direction — identifies research gaps and suggests future work."""

    def __init__(self, llm_service):
        super().__init__("gap_analysis", llm_service)

    async def run(self, input_data: dict) -> GapAnalysis:
        knowledge = input_data.get("knowledge", {})
        review = input_data.get("review", {})
        related = input_data.get("related", {})

        if hasattr(knowledge, "model_dump"):
            knowledge = knowledge.model_dump()
        if hasattr(review, "model_dump"):
            review = review.model_dump()
        if hasattr(related, "model_dump"):
            related = related.model_dump()

        limitations = knowledge.get("limitations", [])
        related_papers = related.get("papers", [])

        prompt = f"""You are a senior research reviewer analyzing a paper and its surrounding literature for research gaps and future directions.

PRIMARY PAPER:
Problem: {knowledge.get('problem_statement', '')}
Methodology: {knowledge.get('methodology', {}).get('approach', '')}
Key Results: {knowledge.get('key_results', [])}
Limitations (author-stated): {limitations}
Keywords: {', '.join(knowledge.get('keywords', []))}

LITERATURE REVIEW SUMMARY:
{review.get('conclusion', '')}
Methodology Evolution: {review.get('methodology_evolution', '')}

NUMBER OF RELATED PAPERS: {len(related_papers)}

Analyze from three perspectives:
1. REVIEWER: What methodological weaknesses exist?
2. PRACTITIONER: What real-world application gaps exist?
3. THEORIST: What theoretical questions remain open?

Return a JSON object with:
- gaps: Array of objects with: description, gap_type (one of "methodological", "dataset", "theoretical", "application"), severity ("critical", "moderate", "minor"), evidence (why this is a gap)
- future_directions: Array of objects with: title, description, feasibility_score (0.0-1.0), estimated_impact ("high", "medium", "low"), required_resources (array of strings)
- open_questions: Array of 3-5 open research questions
- overall_assessment: 2-3 sentence overall assessment of the research landscape"""

        result = await self.llm.generate_json(prompt)

        gaps = [ResearchGap(**g) for g in result.get("gaps", [])]
        directions = [FutureDirection(**f) for f in result.get("future_directions", [])]

        return GapAnalysis(
            gaps=gaps,
            future_directions=directions,
            open_questions=result.get("open_questions", []),
            overall_assessment=result.get("overall_assessment", ""),
        )
