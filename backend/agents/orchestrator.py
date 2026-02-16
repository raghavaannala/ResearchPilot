import asyncio
import logging
import time
from typing import Any, Callable
from agents.base_agent import AgentResult, AgentStatus
from agents.ingestion_agent import IngestionAgent
from agents.extraction_agent import ExtractionAgent
from agents.simplification_agent import SimplificationAgent
from agents.related_research_agent import RelatedResearchAgent
from agents.literature_agent import LiteratureAgent
from agents.gap_analysis_agent import GapAnalysisAgent
from agents.code_generation_agent import CodeGenerationAgent

logger = logging.getLogger("orchestrator")


class Orchestrator:
    """
    Supervisor agent that manages the multi-agent execution DAG.
    Dispatches tasks, handles parallelism, and aggregates results.
    """

    STAGES = [
        "reading_paper",
        "extracting_methodology",
        "finding_related_work",
        "comparing_contributions",
        "detecting_research_gaps",
        "generating_hypothesis",
        "building_prototype",
    ]

    def __init__(self, llm_service):
        self.llm = llm_service
        self.agents = {
            "ingestion": IngestionAgent(llm_service),
            "extraction": ExtractionAgent(llm_service),
            "simplification": SimplificationAgent(llm_service),
            "related_research": RelatedResearchAgent(llm_service),
            "literature_review": LiteratureAgent(llm_service),
            "gap_analysis": GapAnalysisAgent(llm_service),
            "code_generation": CodeGenerationAgent(llm_service),
        }
        self.results: dict[str, AgentResult] = {}
        self.progress_callbacks: list[Callable] = []
        self.pipeline_status: dict = {}

    def on_progress(self, callback: Callable):
        self.progress_callbacks.append(callback)

    async def _emit(self, stage: str, status: str, detail: str = ""):
        self.pipeline_status[stage] = {"status": status, "detail": detail}
        for cb in self.progress_callbacks:
            try:
                await cb({
                    "stage": stage,
                    "status": status,
                    "detail": detail,
                    "pipeline": self.pipeline_status,
                })
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    async def run_pipeline(self, raw_input: dict) -> dict:
        """Execute the full analysis pipeline."""
        start_time = time.time()

        # STAGE 1: Ingestion
        await self._emit("reading_paper", "running", "Parsing paper...")
        ingestion_result = await self.agents["ingestion"].execute(raw_input)
        self.results["ingestion"] = ingestion_result
        if ingestion_result.status == AgentStatus.FAILED:
            await self._emit("reading_paper", "failed", ingestion_result.error or "")
            return self._assemble_output(time.time() - start_time)
        await self._emit("reading_paper", "done", "✓")

        # STAGE 2: Knowledge Extraction
        await self._emit("extracting_methodology", "running", "Extracting knowledge...")
        from models.document import StructuredDocument, Section
        doc = StructuredDocument(**ingestion_result.output) if isinstance(ingestion_result.output, dict) else ingestion_result.output
        extraction_result = await self.agents["extraction"].execute(doc)
        self.results["extraction"] = extraction_result
        if extraction_result.status == AgentStatus.FAILED:
            await self._emit("extracting_methodology", "failed", extraction_result.error or "")
            return self._assemble_output(time.time() - start_time)
        await self._emit("extracting_methodology", "done", "✓")

        # STAGE 3: Parallel — Simplification + Related Research + Code Gen
        await self._emit("finding_related_work", "running", "Finding related papers...")
        await self._emit("comparing_contributions", "running", "Analyzing contributions...")
        await self._emit("building_prototype", "running", "Generating code...")

        simp_task = self.agents["simplification"].execute({
            "document": ingestion_result.output,
            "knowledge": extraction_result.output,
        })
        related_task = self.agents["related_research"].execute(extraction_result.output)
        code_task = self.agents["code_generation"].execute(extraction_result.output)

        results = await asyncio.gather(simp_task, related_task, code_task, return_exceptions=True)

        # Handle results
        for i, (key, res) in enumerate(zip(
            ["simplification", "related_research", "code_generation"], results
        )):
            if isinstance(res, Exception):
                self.results[key] = AgentResult(status=AgentStatus.FAILED, error=str(res))
            else:
                self.results[key] = res

        await self._emit("finding_related_work", "done", "✓")
        await self._emit("comparing_contributions", "done", "✓")
        await self._emit("building_prototype", "done", "✓")

        # STAGE 4: Literature Review (needs related papers)
        await self._emit("detecting_research_gaps", "running", "Building literature review...")
        related_output = self.results.get("related_research")
        if related_output and related_output.status == AgentStatus.SUCCESS:
            lit_result = await self.agents["literature_review"].execute({
                "knowledge": extraction_result.output,
                "related": related_output.output,
            })
            self.results["literature_review"] = lit_result
        else:
            self.results["literature_review"] = AgentResult(
                status=AgentStatus.FAILED, error="Related research unavailable"
            )

        # STAGE 5: Gap Analysis (needs literature review)
        await self._emit("generating_hypothesis", "running", "Analyzing research gaps...")
        lit_output = self.results.get("literature_review")
        gap_result = await self.agents["gap_analysis"].execute({
            "knowledge": extraction_result.output,
            "review": lit_output.output if lit_output and lit_output.status == AgentStatus.SUCCESS else {},
            "related": related_output.output if related_output and related_output.status == AgentStatus.SUCCESS else {},
        })
        self.results["gap_analysis"] = gap_result

        await self._emit("detecting_research_gaps", "done", "✓")
        await self._emit("generating_hypothesis", "done", "✓")

        return self._assemble_output(time.time() - start_time)

    def _assemble_output(self, total_time: float) -> dict:
        """Assemble the final output from all agent results."""
        def safe_output(key: str) -> dict:
            result = self.results.get(key)
            if result and result.status == AgentStatus.SUCCESS and result.output:
                return result.output
            return {}

        return {
            "paper": safe_output("ingestion"),
            "knowledge_card": safe_output("extraction"),
            "explanations": safe_output("simplification"),
            "related_papers": safe_output("related_research"),
            "literature_review": safe_output("literature_review"),
            "gap_analysis": safe_output("gap_analysis"),
            "code_prototype": safe_output("code_generation"),
            "metadata": {
                "total_time": total_time,
                "agent_statuses": {
                    k: {"status": v.status, "time": v.execution_time_seconds, "error": v.error}
                    for k, v in self.results.items()
                },
            },
        }
