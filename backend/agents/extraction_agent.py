import logging
from agents.base_agent import BaseAgent
from models.knowledge import KnowledgeCard, MethodologyBreakdown, DatasetInfo, Result
from models.document import StructuredDocument

logger = logging.getLogger("agent.extraction")


class ExtractionAgent(BaseAgent):
    """Agent 2: Knowledge Extraction — extracts structured knowledge from a parsed paper."""

    def __init__(self, llm_service):
        super().__init__("extraction", llm_service)

    async def run(self, input_data: StructuredDocument) -> KnowledgeCard:
        doc = input_data

        # Prepare paper content for the LLM
        paper_content = f"Title: {doc.title}\n\nAbstract: {doc.abstract}\n\n"
        for section in doc.sections[:15]:  # Limit to avoid token overflow
            paper_content += f"## {section.title}\n{section.content[:2000]}\n\n"

        system_prompt = """You are a research paper analysis expert. Extract structured knowledge from the given research paper.
You must extract the following fields as a JSON object:
- problem_statement: The core problem the paper addresses
- hypothesis: The main hypothesis (or null if not stated)
- methodology: An object with: approach (string), steps (array of strings), algorithms (array), model_architecture (string or null), training_details (string or null)
- datasets: Array of objects with: name, description, size (or null), source (or null)
- evaluation_metrics: Array of metric names used
- key_results: Array of objects with: metric, value, comparison (or null)
- contributions: Array of key contributions
- limitations: Array of limitations mentioned
- keywords: Array of 5-10 relevant keywords"""

        prompt = f"""Analyze this research paper and extract structured knowledge:

{paper_content}

Return a JSON object with all the fields described in the system instructions."""

        result = await self.llm.generate_json(prompt, system_prompt)

        # Parse into KnowledgeCard
        methodology = result.get("methodology", {})
        if isinstance(methodology, str):
            methodology = {"approach": methodology, "steps": [], "algorithms": []}

        return KnowledgeCard(
            problem_statement=result.get("problem_statement", "Not identified"),
            hypothesis=result.get("hypothesis"),
            methodology=MethodologyBreakdown(
                approach=methodology.get("approach", ""),
                steps=methodology.get("steps", []),
                algorithms=methodology.get("algorithms", []),
                model_architecture=methodology.get("model_architecture"),
                training_details=methodology.get("training_details"),
            ),
            datasets=[DatasetInfo(**d) for d in result.get("datasets", [])],
            evaluation_metrics=result.get("evaluation_metrics", []),
            key_results=[Result(**r) for r in result.get("key_results", [])],
            contributions=result.get("contributions", []),
            limitations=result.get("limitations", []),
            keywords=result.get("keywords", []),
        )
