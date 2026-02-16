import os
import logging
from agents.base_agent import BaseAgent
from models.document import StructuredDocument, Section
from services.pdf_parser import PDFParser
from services.arxiv_client import ArxivClient
from config import get_settings

logger = logging.getLogger("agent.ingestion")


class IngestionAgent(BaseAgent):
    """Agent 1: Paper Ingestion — parses PDFs, URLs, and arXiv papers into StructuredDocument."""

    def __init__(self, llm_service=None):
        super().__init__("ingestion", llm_service)

    async def run(self, input_data: dict) -> StructuredDocument:
        source_type = input_data.get("source_type", "pdf")
        settings = get_settings()

        if source_type == "arxiv":
            return await self._process_arxiv(input_data["source_ref"], settings.UPLOAD_DIR)
        elif source_type == "pdf":
            return await self._process_pdf(input_data["file_path"])
        elif source_type == "url":
            return await self._process_url(input_data["source_ref"], settings.UPLOAD_DIR)
        else:
            raise ValueError(f"Unknown source type: {source_type}")

    async def _process_arxiv(self, arxiv_id: str, upload_dir: str) -> StructuredDocument:
        # Fetch metadata
        metadata = await ArxivClient.fetch_paper(arxiv_id)

        # Download PDF
        os.makedirs(upload_dir, exist_ok=True)
        pdf_path = os.path.join(upload_dir, f"{metadata['arxiv_id']}.pdf")
        await ArxivClient.download_pdf(arxiv_id, pdf_path)

        # Parse PDF
        parsed = await PDFParser.parse(pdf_path)

        return StructuredDocument(
            title=metadata.get("title", parsed.get("title", "Untitled")),
            authors=metadata.get("authors", parsed.get("authors", [])),
            abstract=metadata.get("abstract", parsed.get("abstract", "")),
            sections=[Section(**s) for s in parsed.get("sections", [])],
            references=parsed.get("references", []),
            figures=[],
            source_type="arxiv",
            raw_text=parsed.get("raw_text", ""),
            page_count=parsed.get("page_count", 0),
        )

    async def _process_pdf(self, file_path: str) -> StructuredDocument:
        parsed = await PDFParser.parse(file_path)

        return StructuredDocument(
            title=parsed.get("title", "Untitled"),
            authors=parsed.get("authors", []),
            abstract=parsed.get("abstract", ""),
            sections=[Section(**s) for s in parsed.get("sections", [])],
            references=parsed.get("references", []),
            figures=[],
            source_type="pdf",
            raw_text=parsed.get("raw_text", ""),
            page_count=parsed.get("page_count", 0),
        )

    async def _process_url(self, url: str, upload_dir: str) -> StructuredDocument:
        # Check if it's an arXiv URL
        if "arxiv.org" in url:
            arxiv_id = ArxivClient.normalize_arxiv_id(url)
            return await self._process_arxiv(arxiv_id, upload_dir)

        # For other URLs, try to download as PDF
        import httpx
        os.makedirs(upload_dir, exist_ok=True)
        pdf_path = os.path.join(upload_dir, "downloaded_paper.pdf")

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(response.content)

        return await self._process_pdf(pdf_path)
