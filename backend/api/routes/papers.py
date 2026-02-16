import os
import uuid
import json
import asyncio
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from config import get_settings
from services.llm_service import get_llm_service
from agents.orchestrator import Orchestrator
from db.database import async_session
from db.models import Paper, Analysis
from sqlalchemy import select

logger = logging.getLogger("api.papers")
router = APIRouter(prefix="/api/v1/papers", tags=["papers"])

# In-memory store for pipeline progress events (per paper_id)
pipeline_events: dict[str, list[dict]] = {}
pipeline_results: dict[str, dict] = {}


async def run_analysis_pipeline(paper_id: str, input_data: dict):
    """Background task: run the full multi-agent pipeline."""
    llm = get_llm_service()
    orchestrator = Orchestrator(llm)

    # Track progress events
    events = []
    pipeline_events[paper_id] = events

    async def on_progress(event):
        event["paper_id"] = paper_id
        events.append(event)

    orchestrator.on_progress(on_progress)

    # Update paper status
    async with async_session() as session:
        paper = (await session.execute(select(Paper).where(Paper.id == paper_id))).scalar_one_or_none()
        if paper:
            paper.status = "processing"
            await session.commit()

    try:
        result = await orchestrator.run_pipeline(input_data)
        pipeline_results[paper_id] = result

        # Save to database
        async with async_session() as session:
            paper = (await session.execute(select(Paper).where(Paper.id == paper_id))).scalar_one_or_none()
            if paper:
                paper.status = "completed"
                paper.title = result.get("paper", {}).get("title", paper.title)
                paper.authors = json.dumps(result.get("paper", {}).get("authors", []))

            analysis = Analysis(
                paper_id=paper_id,
                knowledge_card=result.get("knowledge_card"),
                simplified_explanation=result.get("explanations"),
                related_papers=result.get("related_papers"),
                literature_review=result.get("literature_review"),
                gap_analysis=result.get("gap_analysis"),
                code_prototype=result.get("code_prototype"),
                pipeline_status=result.get("metadata", {}).get("agent_statuses"),
                total_execution_time=result.get("metadata", {}).get("total_time"),
            )
            session.add(analysis)
            await session.commit()

    except Exception as e:
        logger.error(f"Pipeline failed for paper {paper_id}: {e}")
        async with async_session() as session:
            paper = (await session.execute(select(Paper).where(Paper.id == paper_id))).scalar_one_or_none()
            if paper:
                paper.status = "failed"
                await session.commit()
        pipeline_events[paper_id].append({"stage": "error", "status": "failed", "detail": str(e)})


@router.post("/")
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
    arxiv_id: str | None = Form(None),
):
    """Upload a paper for analysis — accepts PDF, URL, or arXiv ID."""
    settings = get_settings()
    paper_id = str(uuid.uuid4())

    if file:
        # Save uploaded file
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, f"{paper_id}.pdf")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        source_type = "pdf"
        source_ref = file.filename
        input_data = {"source_type": "pdf", "file_path": file_path}

    elif arxiv_id:
        source_type = "arxiv"
        source_ref = arxiv_id.strip()
        input_data = {"source_type": "arxiv", "source_ref": source_ref}
        file_path = None

    elif url:
        source_type = "url"
        source_ref = url.strip()
        input_data = {"source_type": "url", "source_ref": source_ref}
        file_path = None

    else:
        raise HTTPException(status_code=400, detail="Provide a file, URL, or arXiv ID")

    # Save to DB
    async with async_session() as session:
        paper = Paper(
            id=paper_id,
            source_type=source_type,
            source_ref=source_ref,
            file_path=file_path,
            status="uploaded",
        )
        session.add(paper)
        await session.commit()

    # Start pipeline in background
    background_tasks.add_task(run_analysis_pipeline, paper_id, input_data)

    return {"paper_id": paper_id, "status": "processing"}


@router.get("/")
async def list_papers():
    """List all papers."""
    async with async_session() as session:
        result = await session.execute(
            select(Paper).order_by(Paper.created_at.desc()).limit(50)
        )
        papers = result.scalars().all()
        return [
            {
                "id": p.id,
                "title": p.title,
                "source_type": p.source_type,
                "source_ref": p.source_ref,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in papers
        ]


@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    """Get paper details and status."""
    async with async_session() as session:
        paper = (await session.execute(select(Paper).where(Paper.id == paper_id))).scalar_one_or_none()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return {
            "id": paper.id,
            "title": paper.title,
            "source_type": paper.source_type,
            "source_ref": paper.source_ref,
            "status": paper.status,
            "created_at": paper.created_at.isoformat() if paper.created_at else None,
        }


@router.get("/{paper_id}/analysis")
async def get_analysis(paper_id: str):
    """Get full analysis results."""
    # Check in-memory first
    if paper_id in pipeline_results:
        return pipeline_results[paper_id]

    # Check database
    async with async_session() as session:
        analysis = (await session.execute(
            select(Analysis).where(Analysis.paper_id == paper_id)
        )).scalar_one_or_none()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found or still processing")
        return {
            "paper": {},
            "knowledge_card": analysis.knowledge_card,
            "explanations": analysis.simplified_explanation,
            "related_papers": analysis.related_papers,
            "literature_review": analysis.literature_review,
            "gap_analysis": analysis.gap_analysis,
            "code_prototype": analysis.code_prototype,
            "metadata": {
                "total_time": analysis.total_execution_time,
                "agent_statuses": analysis.pipeline_status,
            },
        }


@router.get("/{paper_id}/stream")
async def stream_progress(paper_id: str):
    """SSE endpoint for real-time pipeline progress."""
    async def event_generator():
        sent_count = 0
        max_wait = 600  # 10 minute timeout
        waited = 0

        while waited < max_wait:
            events = pipeline_events.get(paper_id, [])
            while sent_count < len(events):
                event = events[sent_count]
                yield f"data: {json.dumps(event)}\n\n"
                sent_count += 1

                # Check if pipeline is done
                if event.get("stage") == "error":
                    yield f"data: {json.dumps({'stage': 'complete', 'status': 'failed'})}\n\n"
                    return

                # Check if all stages are done
                statuses = event.get("pipeline", {})
                if statuses and all(
                    s.get("status") in ("done", "failed") for s in statuses.values()
                ) and len(statuses) >= 7:
                    yield f"data: {json.dumps({'stage': 'complete', 'status': 'done'})}\n\n"
                    return

            await asyncio.sleep(0.5)
            waited += 0.5

    return StreamingResponse(event_generator(), media_type="text/event-stream")
