import httpx
import logging
import re
import xml.etree.ElementTree as ET

logger = logging.getLogger("arxiv_client")

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_PDF_URL = "https://arxiv.org/pdf"


class ArxivClient:
    """Client for arXiv API."""

    @staticmethod
    def normalize_arxiv_id(input_str: str) -> str:
        """Extract arXiv ID from various formats."""
        input_str = input_str.strip()
        # Handle full URLs
        patterns = [
            r"arxiv\.org/abs/(\d+\.\d+)",
            r"arxiv\.org/pdf/(\d+\.\d+)",
            r"^(\d{4}\.\d{4,5})(v\d+)?$",
        ]
        for pattern in patterns:
            match = re.search(pattern, input_str)
            if match:
                return match.group(1)
        return input_str

    @staticmethod
    async def fetch_paper(arxiv_id: str) -> dict:
        """Fetch paper metadata from arXiv API."""
        clean_id = ArxivClient.normalize_arxiv_id(arxiv_id)
        logger.info(f"Fetching arXiv paper: {clean_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                ARXIV_API_URL,
                params={"id_list": clean_id, "max_results": 1},
            )
            response.raise_for_status()

        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        entry = root.find("atom:entry", ns)
        if entry is None:
            raise ValueError(f"No paper found for arXiv ID: {clean_id}")

        title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
        abstract = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
        published = entry.findtext("atom:published", "", ns)[:10]

        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.findtext("atom:name", "", ns)
            if name:
                authors.append(name)

        # Get PDF link
        pdf_url = f"{ARXIV_PDF_URL}/{clean_id}.pdf"

        return {
            "arxiv_id": clean_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "pdf_url": pdf_url,
        }

    @staticmethod
    async def download_pdf(arxiv_id: str, save_path: str) -> str:
        """Download PDF from arXiv."""
        clean_id = ArxivClient.normalize_arxiv_id(arxiv_id)
        pdf_url = f"{ARXIV_PDF_URL}/{clean_id}.pdf"

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(response.content)

        logger.info(f"Downloaded PDF to: {save_path}")
        return save_path
