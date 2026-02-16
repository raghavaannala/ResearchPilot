import logging
from agents.base_agent import BaseAgent
from models.explanation import SimplifiedExplanation

logger = logging.getLogger("agent.simplification")


class SimplificationAgent(BaseAgent):
    """Agent 3: Simplification — generates multi-level explanations of the paper."""

    def __init__(self, llm_service):
        super().__init__("simplification", llm_service)

    async def run(self, input_data: dict) -> SimplifiedExplanation:
        knowledge = input_data.get("knowledge", {})
        document = input_data.get("document", {})

        if hasattr(knowledge, "model_dump"):
            knowledge = knowledge.model_dump()
        if hasattr(document, "model_dump"):
            document = document.model_dump()

        paper_context = f"""
Paper Title: {document.get('title', 'Unknown')}
Abstract: {document.get('abstract', '')}
Problem: {knowledge.get('problem_statement', '')}
Methodology: {knowledge.get('methodology', {}).get('approach', '')}
Key Results: {', '.join(str(r) for r in knowledge.get('key_results', []))}
Contributions: {', '.join(knowledge.get('contributions', []))}
"""

        system_prompt = """You are an expert science communicator. Generate explanations of this research paper at three levels.
Return a JSON object with:
- eli5_summary: 3-5 sentences explaining the paper as if to a curious 10-year-old. No jargon.
- undergraduate_summary: 1-2 clear paragraphs for a college student. Minimal jargon, explain technical terms.
- expert_summary: A detailed technical summary for domain experts. Use proper terminology.
- key_takeaways: 5-7 bullet points capturing the most important findings.
- visual_analogies: 2-3 creative analogies to help understand the core concepts."""

        result = await self.llm.generate_json(paper_context, system_prompt)

        return SimplifiedExplanation(
            eli5_summary=result.get("eli5_summary", ""),
            undergraduate_summary=result.get("undergraduate_summary", ""),
            expert_summary=result.get("expert_summary", ""),
            key_takeaways=result.get("key_takeaways", []),
            visual_analogies=result.get("visual_analogies", []),
        )
