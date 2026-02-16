# ResearchPilot — Multi-Agent Architecture Implementation Plan

## 📌 Project Overview

**ResearchPilot** is an autonomous AI research intelligence system that assists students, researchers, and developers in understanding and utilizing academic research efficiently. Users upload a research paper (PDF/URL/arXiv), and the system performs multi-stage reasoning through a coordinated ensemble of specialized AI agents.

---

## 🏗️ High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                          │
│  Upload PDF/URL/arXiv  ·  Dashboard  ·  Chat  ·  Results Explorer   │
└──────────────────────────┬───────────────────────────────────────────┘
                           │  REST / WebSocket
┌──────────────────────────▼───────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                           │
│   Auth · Rate Limiting · Request Routing · SSE Progress Streaming    │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                  ORCHESTRATOR AGENT (Supervisor)                     │
│                                                                      │
│   Receives user request → Plans execution DAG → Dispatches to        │
│   specialist agents → Aggregates results → Returns final output      │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐    │
│   │                    AGENT MESSAGE BUS                         │    │
│   │          (In-memory queue / Redis Streams / Celery)          │    │
│   └───┬─────┬─────┬──────┬──────┬──────┬──────┬────────────────┘    │
│       │     │     │      │      │      │      │                      │
│   ┌───▼┐ ┌─▼──┐ ┌▼───┐ ┌▼───┐ ┌▼───┐ ┌▼───┐ ┌▼────┐               │
│   │ A1 │ │ A2 │ │ A3 │ │ A4 │ │ A5 │ │ A6 │ │ A7  │               │
│   └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └─────┘               │
│                                                                      │
│   A1 = Paper Ingestion Agent                                         │
│   A2 = Knowledge Extraction Agent                                    │
│   A3 = Simplification Agent                                          │
│   A4 = Related Research Agent                                        │
│   A5 = Literature Review Agent                                       │
│   A6 = Gap & Future Direction Agent                                  │
│   A7 = Code Generation Agent                                         │
└──────────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                      SHARED SERVICES LAYER                           │
│                                                                      │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────────┐  │
│   │  LLM Router│  │  Vector DB │  │  Document   │  │  External   │  │
│   │  (OpenAI / │  │  (Pinecone │  │  Store      │  │  APIs       │  │
│   │   Claude / │  │   / Chroma │  │  (S3/Local) │  │  (arXiv,    │  │
│   │   Gemini)  │  │   / Qdrant)│  │             │  │   Semantic  │  │
│   └────────────┘  └────────────┘  └────────────┘  │   Scholar,  │  │
│                                                    │   CrossRef) │  │
│   ┌────────────┐  ┌────────────┐                   └─────────────┘  │
│   │  Cache     │  │  PostgreSQL│                                     │
│   │  (Redis)   │  │  (Metadata)│                                     │
│   └────────────┘  └────────────┘                                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent Definitions

### Agent 1: Paper Ingestion Agent
| Attribute        | Detail |
|------------------|--------|
| **Responsibility** | Accept PDF upload, URL, or arXiv ID and convert it into a clean, structured text representation |
| **Input**          | Raw PDF bytes, URL string, or arXiv paper ID |
| **Output**         | `StructuredDocument` — title, authors, abstract, sections (intro, methods, results, discussion, references), figures/tables metadata |
| **Tools**          | PyMuPDF / pdfplumber (PDF parsing), BeautifulSoup (HTML scraping), arXiv API client, OCR fallback (Tesseract) |
| **LLM Usage**      | Section boundary detection when heuristics fail |
| **Error Handling** | Retry with OCR if text extraction yields < 200 words; flag scanned-only PDFs |

### Agent 2: Knowledge Extraction Agent
| Attribute        | Detail |
|------------------|--------|
| **Responsibility** | Extract structured knowledge tuples from the parsed paper |
| **Input**          | `StructuredDocument` from Agent 1 |
| **Output**         | `KnowledgeCard` — problem statement, hypothesis, methodology breakdown, datasets used, evaluation metrics, key results, contributions, limitations (author-stated) |
| **Tools**          | LLM with structured output (JSON mode / function calling) |
| **LLM Usage**      | Heavy — multi-turn chain-of-thought extraction with self-verification |
| **Prompt Strategy** | Few-shot examples per field; extract → verify → refine loop |

### Agent 3: Simplification Agent
| Attribute        | Detail |
|------------------|--------|
| **Responsibility** | Generate plain-language explanations at multiple complexity levels |
| **Input**          | `KnowledgeCard` + `StructuredDocument` |
| **Output**         | `SimplifiedExplanation` — ELI5 summary, undergraduate-level summary, expert summary, key takeaway bullets, visual analogy suggestions |
| **Tools**          | LLM with temperature variation |
| **LLM Usage**      | Heavy — audience-adaptive generation |
| **Prompt Strategy** | System prompt sets audience persona; chain: draft → readability check → refine |

### Agent 4: Related Research Agent
| Attribute        | Detail |
|------------------|--------|
| **Responsibility** | Find, retrieve, and analyze related papers |
| **Input**          | `KnowledgeCard` (problem, methodology, keywords) |
| **Output**         | `RelatedPaperSet` — list of related papers with relevance scores, relationship type (extends, contradicts, applies, precedes), mini-summaries |
| **Tools**          | Semantic Scholar API, arXiv API, CrossRef API, Google Scholar (scraping fallback), Vector DB similarity search |
| **LLM Usage**      | Moderate — query formulation, relevance scoring, relationship classification |
| **Rate Limiting**  | Respect API quotas; cache results in Redis with 24h TTL |

### Agent 5: Literature Review Agent
| Attribute        | Detail |
|------------------|--------|
| **Responsibility** | Synthesize a structured literature review from the primary paper and related papers |
| **Input**          | `KnowledgeCard` (primary) + `RelatedPaperSet` |
| **Output**         | `LiteratureReview` — thematic groupings, chronological narrative, comparison table, methodology evolution, citation graph |
| **Tools**          | LLM for synthesis, NetworkX for citation graph construction |
| **LLM Usage**      | Heavy — multi-document synthesis with citation tracking |
| **Prompt Strategy** | Hierarchical merge: summarize clusters → synthesize across clusters → narrative generation |

### Agent 6: Gap & Future Direction Agent
| Attribute        | Detail |
|------------------|--------|
| **Responsibility** | Identify research gaps, limitations, and suggest future research directions |
| **Input**          | `KnowledgeCard` + `LiteratureReview` + `RelatedPaperSet` |
| **Output**         | `GapAnalysis` — identified gaps (methodological, dataset, theoretical), limitation severity ratings, future direction proposals with feasibility scores, open questions |
| **Tools**          | LLM with reasoning chains |
| **LLM Usage**      | Heavy — requires deep reasoning and cross-paper comparison |
| **Prompt Strategy** | Multi-perspective prompting: reviewer persona, practitioner persona, theorist persona → merge insights |

### Agent 7: Code Generation Agent
| Attribute        | Detail |
|------------------|--------|
| **Responsibility** | Generate prototype implementation code based on the paper's methodology |
| **Input**          | `KnowledgeCard` (methodology section, algorithms, model architecture) |
| **Output**         | `CodePrototype` — Python code with comments, requirements.txt, README, architecture diagram description |
| **Tools**          | LLM with code generation, AST validation, optional sandbox execution |
| **LLM Usage**      | Heavy — structured code generation with documentation |
| **Prompt Strategy** | Decompose methodology → pseudocode → Python implementation → test stubs |

---

## 🔄 Orchestration Flow (DAG)

```
                    ┌──────────────────┐
                    │   User Uploads   │
                    │   Paper / URL    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   A1: Ingestion  │  (STAGE 1 — Sequential)
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  A2: Knowledge   │  (STAGE 2 — Sequential)
                    │   Extraction     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼────┐ ┌───────▼───────┐
     │ A3: Simplify  │ │A4: Find │ │ A7: Code Gen  │  (STAGE 3 — Parallel)
     │               │ │Related  │ │               │
     └───────────────┘ └────┬────┘ └───────────────┘
                            │
                   ┌────────▼─────────┐
                   │ A5: Literature   │  (STAGE 4 — Sequential, needs A4)
                   │    Review        │
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │  A6: Gap &       │  (STAGE 5 — Sequential, needs A5)
                   │  Future Dir.     │
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │  Orchestrator    │  (STAGE 6 — Aggregate)
                   │  Final Assembly  │
                   └──────────────────┘
```

**Estimated Total Processing Time:** 2–5 minutes per paper (depending on related papers count)

---

## 📁 Project Structure

```
researchpilot/
├── frontend/                          # Next.js 14 (App Router)
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                   # Landing page
│   │   ├── dashboard/
│   │   │   └── page.tsx               # User dashboard
│   │   ├── paper/[id]/
│   │   │   └── page.tsx               # Paper analysis results
│   │   └── api/                       # Next.js API routes (BFF)
│   ├── components/
│   │   ├── upload/                    # File upload, URL input, arXiv input
│   │   ├── results/                   # Knowledge card, summaries, lit review
│   │   ├── code-viewer/              # Syntax-highlighted code output
│   │   ├── citation-graph/           # Interactive citation network
│   │   └── shared/                    # Buttons, cards, loaders, progress
│   ├── hooks/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   └── tailwind.config.ts
│
├── backend/                           # FastAPI
│   ├── main.py                        # App entrypoint, CORS, middleware
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── papers.py             # POST /papers, GET /papers/{id}
│   │   │   ├── analysis.py           # GET /papers/{id}/analysis
│   │   │   └── health.py
│   │   └── dependencies.py
│   │
│   ├── agents/                        # 🧠 MULTI-AGENT CORE
│   │   ├── __init__.py
│   │   ├── base_agent.py             # Abstract base class for all agents
│   │   ├── orchestrator.py           # Supervisor agent — DAG execution
│   │   ├── ingestion_agent.py        # A1: Paper parsing
│   │   ├── extraction_agent.py       # A2: Knowledge extraction
│   │   ├── simplification_agent.py   # A3: Simplified explanations
│   │   ├── related_research_agent.py # A4: Find related papers
│   │   ├── literature_agent.py       # A5: Literature review synthesis
│   │   ├── gap_analysis_agent.py     # A6: Gaps & future directions
│   │   ├── code_generation_agent.py  # A7: Prototype code generation
│   │   └── message_bus.py            # Inter-agent communication
│   │
│   ├── models/                        # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── document.py               # StructuredDocument
│   │   ├── knowledge.py              # KnowledgeCard
│   │   ├── explanation.py            # SimplifiedExplanation
│   │   ├── related.py                # RelatedPaperSet
│   │   ├── review.py                 # LiteratureReview
│   │   ├── gaps.py                   # GapAnalysis
│   │   └── code.py                   # CodePrototype
│   │
│   ├── services/                      # Shared services
│   │   ├── __init__.py
│   │   ├── llm_router.py             # Multi-provider LLM abstraction
│   │   ├── pdf_parser.py             # PDF text extraction
│   │   ├── arxiv_client.py           # arXiv API wrapper
│   │   ├── semantic_scholar.py       # Semantic Scholar API wrapper
│   │   ├── vector_store.py           # Embedding + vector DB operations
│   │   └── cache.py                  # Redis caching layer
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py               # SQLAlchemy / asyncpg connection
│   │   ├── models.py                 # ORM models
│   │   └── migrations/               # Alembic migrations
│   │
│   ├── config.py                      # Environment configuration
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml                 # PostgreSQL, Redis, Backend, Frontend
├── .env.example
├── README.md
└── IMPLEMENTATION_PLAN.md             # This file
```

---

## 🧩 Technology Stack

| Layer              | Technology                                         |
|--------------------|----------------------------------------------------|
| **Frontend**       | Next.js 14 (App Router), TypeScript, Tailwind CSS  |
| **Backend API**    | FastAPI (Python 3.11+), Uvicorn, Pydantic v2       |
| **Agent Framework**| LangGraph (preferred) or CrewAI or custom          |
| **LLM Providers**  | OpenAI GPT-4o, Anthropic Claude 3.5, Google Gemini |
| **Vector DB**      | ChromaDB (dev) / Qdrant or Pinecone (prod)         |
| **Database**       | PostgreSQL 16                                      |
| **Cache / Queue**  | Redis 7                                            |
| **PDF Parsing**    | PyMuPDF (fitz), pdfplumber, Tesseract OCR          |
| **External APIs**  | arXiv API, Semantic Scholar API, CrossRef API       |
| **Deployment**     | Docker Compose (dev), AWS/GCP (prod)               |
| **Auth**           | NextAuth.js / Clerk                                |

---

## 📐 Core Data Models (Pydantic)

```python
# models/document.py
from pydantic import BaseModel
from typing import Optional

class Section(BaseModel):
    title: str
    content: str
    subsections: list["Section"] = []

class FigureMetadata(BaseModel):
    figure_id: str
    caption: str
    page_number: int

class StructuredDocument(BaseModel):
    title: str
    authors: list[str]
    abstract: str
    sections: list[Section]
    references: list[str]
    figures: list[FigureMetadata] = []
    source_type: str  # "pdf", "url", "arxiv"
    raw_text: str
    page_count: int


# models/knowledge.py
class KnowledgeCard(BaseModel):
    problem_statement: str
    hypothesis: Optional[str]
    methodology: MethodologyBreakdown
    datasets: list[DatasetInfo]
    evaluation_metrics: list[str]
    key_results: list[Result]
    contributions: list[str]
    limitations: list[str]
    keywords: list[str]

class MethodologyBreakdown(BaseModel):
    approach: str
    steps: list[str]
    algorithms: list[str]
    model_architecture: Optional[str]
    training_details: Optional[str]

class DatasetInfo(BaseModel):
    name: str
    description: str
    size: Optional[str]
    source: Optional[str]

class Result(BaseModel):
    metric: str
    value: str
    comparison: Optional[str]  # e.g., "5% improvement over baseline X"


# models/explanation.py
class SimplifiedExplanation(BaseModel):
    eli5_summary: str                # 3-5 sentences, no jargon
    undergraduate_summary: str       # 1-2 paragraphs, some technical terms
    expert_summary: str              # Detailed, assumes domain knowledge
    key_takeaways: list[str]         # 5-7 bullet points
    visual_analogies: list[str]      # Suggested analogies for concepts


# models/related.py
class RelatedPaper(BaseModel):
    title: str
    authors: list[str]
    year: int
    venue: Optional[str]
    abstract: str
    relevance_score: float           # 0.0 - 1.0
    relationship_type: str           # "extends", "contradicts", "applies", "precedes"
    mini_summary: str
    url: Optional[str]

class RelatedPaperSet(BaseModel):
    papers: list[RelatedPaper]
    search_queries_used: list[str]
    total_candidates_found: int


# models/review.py
class ThematicGroup(BaseModel):
    theme: str
    papers: list[str]                # References to paper titles
    summary: str

class LiteratureReview(BaseModel):
    introduction: str
    thematic_groups: list[ThematicGroup]
    chronological_narrative: str
    comparison_table: list[dict]     # [{paper, method, dataset, result}]
    methodology_evolution: str
    conclusion: str
    citation_count: int


# models/gaps.py
class ResearchGap(BaseModel):
    description: str
    gap_type: str                    # "methodological", "dataset", "theoretical", "application"
    severity: str                    # "critical", "moderate", "minor"
    evidence: str                    # Why this is a gap

class FutureDirection(BaseModel):
    title: str
    description: str
    feasibility_score: float         # 0.0 - 1.0
    estimated_impact: str            # "high", "medium", "low"
    required_resources: list[str]

class GapAnalysis(BaseModel):
    gaps: list[ResearchGap]
    future_directions: list[FutureDirection]
    open_questions: list[str]
    overall_assessment: str


# models/code.py
class CodePrototype(BaseModel):
    language: str                    # "python"
    files: list[CodeFile]
    requirements: list[str]
    readme_content: str
    architecture_description: str

class CodeFile(BaseModel):
    filename: str
    content: str
    description: str
```

---

## 🧠 Agent Framework: Base Agent Design

```python
# agents/base_agent.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, TypeVar, Generic
import logging

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

class AgentStatus:
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"

class AgentResult(BaseModel, Generic[OutputT]):
    status: str
    output: OutputT | None = None
    error: str | None = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0
    metadata: dict = {}

class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all ResearchPilot agents."""

    def __init__(self, name: str, llm_router, config: dict = {}):
        self.name = name
        self.llm = llm_router
        self.config = config
        self.logger = logging.getLogger(f"agent.{name}")
        self.status = AgentStatus.IDLE
        self.max_retries = config.get("max_retries", 3)

    async def execute(self, input_data: InputT) -> AgentResult[OutputT]:
        """Execute with retry logic and timing."""
        import time
        start = time.time()
        self.status = AgentStatus.RUNNING
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                self.logger.info(f"[{self.name}] Executing (attempt {retry_count + 1})")
                output = await self.run(input_data)
                validated = await self.validate(output)
                self.status = AgentStatus.SUCCESS
                return AgentResult(
                    status=AgentStatus.SUCCESS,
                    output=validated,
                    execution_time_seconds=time.time() - start,
                    retry_count=retry_count,
                )
            except Exception as e:
                retry_count += 1
                self.logger.error(f"[{self.name}] Error: {e} (retry {retry_count})")
                self.status = AgentStatus.RETRYING
                if retry_count > self.max_retries:
                    self.status = AgentStatus.FAILED
                    return AgentResult(
                        status=AgentStatus.FAILED,
                        error=str(e),
                        execution_time_seconds=time.time() - start,
                        retry_count=retry_count,
                    )

    @abstractmethod
    async def run(self, input_data: InputT) -> OutputT:
        """Core agent logic — must be implemented by subclasses."""
        ...

    async def validate(self, output: OutputT) -> OutputT:
        """Optional validation hook. Override for custom validation."""
        return output

    def get_system_prompt(self) -> str:
        """Return the agent's system prompt."""
        return ""
```

---

## 🔀 Orchestrator Design

```python
# agents/orchestrator.py
import asyncio
from agents.base_agent import BaseAgent, AgentResult

class Orchestrator:
    """
    Supervisor agent that manages the execution DAG.
    Dispatches tasks, handles parallelism, and aggregates results.
    """

    def __init__(self, agents: dict[str, BaseAgent], llm_router, config):
        self.agents = agents
        self.llm = llm_router
        self.config = config
        self.results: dict[str, AgentResult] = {}
        self.progress_callbacks = []

    def on_progress(self, callback):
        self.progress_callbacks.append(callback)

    async def _emit_progress(self, stage: str, status: str, detail: str = ""):
        for cb in self.progress_callbacks:
            await cb({"stage": stage, "status": status, "detail": detail})

    async def run_pipeline(self, raw_input) -> dict:
        """Execute the full analysis pipeline."""

        # STAGE 1: Ingestion
        await self._emit_progress("ingestion", "running", "Parsing paper...")
        ingestion_result = await self.agents["ingestion"].execute(raw_input)
        self.results["ingestion"] = ingestion_result
        if ingestion_result.status == "failed":
            raise RuntimeError(f"Ingestion failed: {ingestion_result.error}")
        await self._emit_progress("ingestion", "done")

        # STAGE 2: Knowledge Extraction
        await self._emit_progress("extraction", "running", "Extracting knowledge...")
        extraction_result = await self.agents["extraction"].execute(
            ingestion_result.output
        )
        self.results["extraction"] = extraction_result
        await self._emit_progress("extraction", "done")

        # STAGE 3: Parallel — Simplification + Related Research + Code Gen
        await self._emit_progress("parallel", "running", "Running parallel analysis...")
        simplification_task = self.agents["simplification"].execute(
            {"document": ingestion_result.output, "knowledge": extraction_result.output}
        )
        related_task = self.agents["related_research"].execute(extraction_result.output)
        code_task = self.agents["code_generation"].execute(extraction_result.output)

        simplification_result, related_result, code_result = await asyncio.gather(
            simplification_task, related_task, code_task,
            return_exceptions=True
        )
        self.results["simplification"] = simplification_result
        self.results["related_research"] = related_result
        self.results["code_generation"] = code_result
        await self._emit_progress("parallel", "done")

        # STAGE 4: Literature Review (requires related papers)
        await self._emit_progress("literature", "running", "Building literature review...")
        literature_result = await self.agents["literature_review"].execute(
            {"knowledge": extraction_result.output, "related": related_result.output}
        )
        self.results["literature_review"] = literature_result
        await self._emit_progress("literature", "done")

        # STAGE 5: Gap Analysis (requires literature review)
        await self._emit_progress("gaps", "running", "Analyzing research gaps...")
        gap_result = await self.agents["gap_analysis"].execute(
            {
                "knowledge": extraction_result.output,
                "review": literature_result.output,
                "related": related_result.output,
            }
        )
        self.results["gap_analysis"] = gap_result
        await self._emit_progress("gaps", "done")

        # STAGE 6: Aggregate
        return self._assemble_final_output()

    def _assemble_final_output(self) -> dict:
        """Combine all agent results into the final response."""
        return {
            "paper": self.results["ingestion"].output.model_dump(),
            "knowledge_card": self.results["extraction"].output.model_dump(),
            "explanations": self.results["simplification"].output.model_dump(),
            "related_papers": self.results["related_research"].output.model_dump(),
            "literature_review": self.results["literature_review"].output.model_dump(),
            "gap_analysis": self.results["gap_analysis"].output.model_dump(),
            "code_prototype": self.results["code_generation"].output.model_dump(),
            "metadata": {
                "total_time": sum(
                    r.execution_time_seconds for r in self.results.values()
                    if hasattr(r, "execution_time_seconds")
                ),
                "agent_statuses": {
                    k: v.status for k, v in self.results.items()
                },
            },
        }
```

---

## 🔗 LLM Router (Multi-Provider)

```python
# services/llm_router.py
from enum import Enum
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

class LLMRouter:
    """
    Routes LLM calls to the optimal provider based on task requirements.
    Supports fallback chaining and cost optimization.
    """

    TASK_ROUTING = {
        "extraction":     (LLMProvider.OPENAI, "gpt-4o"),        # Best structured output
        "simplification": (LLMProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"),  # Best prose
        "related_search": (LLMProvider.GEMINI, "gemini-1.5-pro"),  # Best long context
        "literature":     (LLMProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"),  # Best synthesis
        "gap_analysis":   (LLMProvider.OPENAI, "gpt-4o"),        # Best reasoning
        "code_gen":       (LLMProvider.OPENAI, "gpt-4o"),        # Best code generation
    }

    def __init__(self, config):
        self.openai = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.anthropic = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.gemini = genai.GenerativeModel("gemini-1.5-pro")

    async def generate(self, task: str, messages: list, **kwargs) -> str:
        provider, model = self.TASK_ROUTING.get(
            task, (LLMProvider.OPENAI, "gpt-4o-mini")
        )
        try:
            return await self._call(provider, model, messages, **kwargs)
        except Exception:
            # Fallback to secondary provider
            return await self._call(LLMProvider.OPENAI, "gpt-4o-mini", messages, **kwargs)

    async def _call(self, provider, model, messages, **kwargs) -> str:
        if provider == LLMProvider.OPENAI:
            response = await self.openai.chat.completions.create(
                model=model, messages=messages, **kwargs
            )
            return response.choices[0].message.content
        elif provider == LLMProvider.ANTHROPIC:
            response = await self.anthropic.messages.create(
                model=model, messages=messages, max_tokens=4096, **kwargs
            )
            return response.content[0].text
        elif provider == LLMProvider.GEMINI:
            response = await self.gemini.generate_content_async(
                [m["content"] for m in messages]
            )
            return response.text
```

---

## 🌐 API Design

### REST Endpoints

| Method | Endpoint                        | Description                                |
|--------|---------------------------------|--------------------------------------------|
| POST   | `/api/v1/papers`                | Upload paper (PDF/URL/arXiv)               |
| GET    | `/api/v1/papers/{id}`           | Get paper details                          |
| GET    | `/api/v1/papers/{id}/status`    | Get analysis pipeline status               |
| GET    | `/api/v1/papers/{id}/analysis`  | Get full analysis results                  |
| GET    | `/api/v1/papers/{id}/knowledge` | Get knowledge card only                    |
| GET    | `/api/v1/papers/{id}/related`   | Get related papers only                    |
| GET    | `/api/v1/papers/{id}/review`    | Get literature review only                 |
| GET    | `/api/v1/papers/{id}/gaps`      | Get gap analysis only                      |
| GET    | `/api/v1/papers/{id}/code`      | Get generated code only                    |
| GET    | `/api/v1/papers/{id}/explain`   | Get simplified explanations                |
| WS     | `/api/v1/papers/{id}/stream`    | WebSocket for real-time progress updates   |

### SSE Progress Streaming

```python
# api/routes/papers.py
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import json

router = APIRouter(prefix="/api/v1/papers")

@router.post("/")
async def upload_paper(
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
    arxiv_id: str | None = Form(None),
):
    # Validate input (at least one must be provided)
    paper = await save_paper(file, url, arxiv_id)
    # Kick off background analysis
    background_tasks.add_task(run_analysis_pipeline, paper.id)
    return {"paper_id": paper.id, "status": "processing"}

@router.get("/{paper_id}/stream")
async def stream_progress(paper_id: str):
    async def event_generator():
        async for event in get_pipeline_events(paper_id):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 🗄️ Database Schema

```sql
-- Papers table
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    authors TEXT[],
    source_type VARCHAR(10) NOT NULL,  -- 'pdf', 'url', 'arxiv'
    source_ref TEXT,                    -- original URL or arXiv ID
    file_path TEXT,                     -- stored PDF path
    status VARCHAR(20) DEFAULT 'uploaded',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    user_id UUID REFERENCES users(id)
);

-- Analysis results (one per paper, stores full JSON output)
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    knowledge_card JSONB,
    simplified_explanation JSONB,
    related_papers JSONB,
    literature_review JSONB,
    gap_analysis JSONB,
    code_prototype JSONB,
    pipeline_status JSONB,             -- per-agent status tracking
    total_execution_time FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent execution log (for debugging and monitoring)
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    agent_name VARCHAR(50),
    status VARCHAR(20),
    input_summary TEXT,
    output_summary TEXT,
    error_message TEXT,
    execution_time FLOAT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User accounts
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📅 Phased Implementation Plan

### Phase 1: Foundation (Week 1-2)
> **Goal:** Core infrastructure, basic ingestion, and knowledge extraction

| Task | Priority | Est. Hours |
|------|----------|------------|
| Project scaffolding (FastAPI + Next.js) | P0 | 4 |
| Docker Compose setup (Postgres, Redis) | P0 | 3 |
| Database schema + Alembic migrations | P0 | 3 |
| `BaseAgent` abstract class implementation | P0 | 4 |
| `LLMRouter` with OpenAI support | P0 | 4 |
| PDF parsing service (PyMuPDF + pdfplumber) | P0 | 6 |
| arXiv API client | P0 | 3 |
| **Agent 1: Ingestion Agent** — full implementation | P0 | 8 |
| **Agent 2: Knowledge Extraction Agent** — full implementation | P0 | 10 |
| Basic upload API endpoint | P0 | 3 |
| Unit tests for Agents 1 & 2 | P1 | 6 |

**Deliverable:** Upload a PDF → get structured document + knowledge card

---

### Phase 2: Explanation & Discovery (Week 3-4)
> **Goal:** Simplification, related paper discovery, basic orchestration

| Task | Priority | Est. Hours |
|------|----------|------------|
| **Agent 3: Simplification Agent** — full implementation | P0 | 8 |
| **Agent 4: Related Research Agent** — full implementation | P0 | 12 |
| Semantic Scholar API integration | P0 | 4 |
| CrossRef API integration | P1 | 3 |
| `Orchestrator` — DAG execution engine | P0 | 10 |
| SSE progress streaming | P0 | 4 |
| Redis caching for API responses | P1 | 3 |
| Frontend: Upload page | P0 | 6 |
| Frontend: Progress tracker component | P0 | 4 |
| Frontend: Knowledge card display | P0 | 5 |
| Frontend: Simplified explanations view | P0 | 4 |
| Integration tests | P1 | 6 |

**Deliverable:** End-to-end pipeline for ingestion → extraction → simplification + related papers

---

### Phase 3: Synthesis & Analysis (Week 5-6)
> **Goal:** Literature review, gap analysis, code generation

| Task | Priority | Est. Hours |
|------|----------|------------|
| **Agent 5: Literature Review Agent** — full implementation | P0 | 12 |
| **Agent 6: Gap Analysis Agent** — full implementation | P0 | 10 |
| **Agent 7: Code Generation Agent** — full implementation | P0 | 10 |
| Vector DB integration (ChromaDB) | P0 | 6 |
| Embedding pipeline for papers | P0 | 4 |
| Frontend: Literature review display | P0 | 6 |
| Frontend: Gap analysis visualization | P0 | 5 |
| Frontend: Code viewer with syntax highlighting | P0 | 5 |
| Frontend: Citation graph (vis.js / D3) | P1 | 8 |
| Multi-provider LLM routing (add Anthropic, Gemini) | P1 | 4 |
| End-to-end integration tests | P0 | 6 |

**Deliverable:** Complete 7-agent pipeline, full analysis output

---

### Phase 4: Polish & Production (Week 7-8)
> **Goal:** Production readiness, UX polish, deployment

| Task | Priority | Est. Hours |
|------|----------|------------|
| Authentication (NextAuth.js) | P0 | 6 |
| User dashboard (paper history, saved analyses) | P0 | 8 |
| Rate limiting and API key management | P0 | 3 |
| Error handling & graceful degradation | P0 | 6 |
| Logging, monitoring (Sentry, structured logs) | P1 | 4 |
| Frontend: Responsive design polish | P0 | 6 |
| Frontend: Dark mode | P1 | 3 |
| Frontend: Export results (PDF/Markdown) | P1 | 6 |
| Performance optimization (caching, batch embeddings) | P1 | 4 |
| CI/CD pipeline (GitHub Actions) | P1 | 4 |
| Cloud deployment (Docker → AWS ECS or GCP Cloud Run) | P1 | 8 |
| Load testing | P2 | 4 |
| Documentation | P1 | 4 |

**Deliverable:** Production-ready deployed application

---

## 🔑 Environment Variables

```env
# .env.example

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/researchpilot

# Redis
REDIS_URL=redis://localhost:6379/0

# Vector DB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# External APIs
SEMANTIC_SCHOLAR_API_KEY=...       # Optional, increases rate limits
CROSSREF_EMAIL=your@email.com     # Polite pool access

# Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50

# App
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
DEBUG=true
```

---

## 🧪 Testing Strategy

| Test Type        | Tool            | Scope                                  |
|------------------|-----------------|----------------------------------------|
| Unit Tests       | pytest + pytest-asyncio | Individual agent logic, parsing, models |
| Integration Tests| pytest          | Multi-agent pipeline, API endpoints    |
| LLM Tests        | Mock + snapshot  | Prompt quality (golden output comparison) |
| API Tests        | httpx + pytest  | Full request/response cycle            |
| Frontend Tests   | Vitest + Testing Library | Component rendering, interactions |
| E2E Tests        | Playwright      | Upload → results flow                  |

---

## ⚡ Performance Considerations

1. **Parallel Agent Execution** — Agents 3, 4, 7 run concurrently after Stage 2
2. **Streaming Results** — SSE pushes partial results to the frontend as each agent completes
3. **Caching** — Redis caches related paper API responses (24h TTL) and embeddings
4. **Chunked LLM Calls** — Long papers are split into chunks for extraction; results merged
5. **Queue-Based Processing** — Heavy analysis runs as background tasks (Celery or asyncio tasks)
6. **Vector Similarity** — Avoid redundant API calls by checking vector DB for already-indexed papers

---

## 🛡️ Error Handling & Resilience

- **Agent-Level Retries**: Each agent retries up to 3 times with exponential backoff
- **Partial Results**: If one agent fails, the pipeline returns partial results for completed agents
- **LLM Fallback**: If primary LLM provider fails, router falls back to secondary provider
- **Graceful Degradation**: If external APIs (Semantic Scholar) are down, skip related paper enrichment
- **Circuit Breaker**: Track consecutive failures per external service; disable after threshold

---

## 🚀 Quick Start Commands

```bash
# 1. Clone and install
git clone https://github.com/your-org/researchpilot.git
cd researchpilot

# 2. Start infrastructure
docker-compose up -d postgres redis chromadb

# 3. Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

# 4. Frontend
cd frontend
npm install
npm run dev

# 5. Open http://localhost:3000
```

---

## 📊 Agent Communication Protocol

Each agent communicates through the orchestrator using a standardized message format:

```python
class AgentMessage(BaseModel):
    source_agent: str
    target_agent: str
    message_type: str       # "input", "output", "error", "progress"
    payload: dict
    timestamp: datetime
    correlation_id: str     # Links messages in same pipeline run
```

This ensures:
- **Traceability** — Every inter-agent message is logged
- **Debuggability** — Replay any pipeline run from message history
- **Extensibility** — New agents can be added without modifying existing ones

---

## ✅ Summary

| Component | Count |
|-----------|-------|
| Specialized Agents | 7 |
| LLM Providers | 3 (OpenAI, Anthropic, Gemini) |
| External APIs | 3 (arXiv, Semantic Scholar, CrossRef) |
| Pipeline Stages | 6 (including parallel) |
| Database Tables | 4 |
| API Endpoints | 11 |
| Development Phases | 4 (8 weeks) |

**Key Architectural Decisions:**
1. **LangGraph-style DAG** over linear chains — enables parallel execution
2. **Multi-provider LLM routing** — optimizes cost and quality per task
3. **Pydantic schemas everywhere** — type safety across agent boundaries
4. **SSE streaming** — real-time progress without polling
5. **Agent-level retry + fallback** — resilient to individual failures
