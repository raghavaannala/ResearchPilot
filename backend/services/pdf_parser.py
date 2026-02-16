import fitz  # PyMuPDF
import pdfplumber
import re
import logging
from pathlib import Path

logger = logging.getLogger("pdf_parser")


class PDFParser:
    """Extract structured text from PDF files."""

    @staticmethod
    async def parse(file_path: str) -> dict:
        """
        Parse a PDF file and extract structured content.
        Returns dict with: title, authors, abstract, sections, references, raw_text, page_count
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        # Try PyMuPDF first
        try:
            return PDFParser._parse_with_pymupdf(file_path)
        except Exception as e:
            logger.warning(f"PyMuPDF failed, falling back to pdfplumber: {e}")
            return PDFParser._parse_with_pdfplumber(file_path)

    @staticmethod
    def _parse_with_pymupdf(file_path: str) -> dict:
        doc = fitz.open(file_path)
        raw_text = ""
        sections = []
        current_section = {"title": "Introduction", "content": ""}

        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    text = ""
                    is_heading = False
                    for span in line["spans"]:
                        text += span["text"]
                        # Detect headings by font size > 12 or bold
                        if span["size"] > 12 or "Bold" in span["font"] or "bold" in span["font"]:
                            is_heading = True

                    text = text.strip()
                    if not text:
                        continue

                    raw_text += text + "\n"

                    if is_heading and len(text) > 3 and len(text) < 200:
                        # Save current section
                        if current_section["content"].strip():
                            sections.append(current_section.copy())
                        current_section = {"title": text, "content": ""}
                    else:
                        current_section["content"] += text + " "

        # Save last section
        if current_section["content"].strip():
            sections.append(current_section.copy())

        doc_data = PDFParser._extract_metadata(raw_text, sections)
        doc_data["raw_text"] = raw_text
        doc_data["page_count"] = len(doc)
        doc.close()
        return doc_data

    @staticmethod
    def _parse_with_pdfplumber(file_path: str) -> dict:
        raw_text = ""
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    raw_text += text + "\n"

        sections = PDFParser._split_into_sections(raw_text)
        doc_data = PDFParser._extract_metadata(raw_text, sections)
        doc_data["raw_text"] = raw_text
        doc_data["page_count"] = page_count
        return doc_data

    @staticmethod
    def _split_into_sections(text: str) -> list[dict]:
        """Split raw text into sections using common heading patterns."""
        section_patterns = [
            r"^(\d+\.?\s+[A-Z][A-Za-z\s]+)$",  # "1. Introduction" or "1 Introduction"
            r"^([A-Z][A-Z\s]+)$",  # "ABSTRACT", "INTRODUCTION"
            r"^(Abstract|Introduction|Related Work|Methodology|Method|Methods|Experiments?|Results?|Discussion|Conclusion|References|Acknowledgment)",
        ]

        lines = text.split("\n")
        sections = []
        current = {"title": "Header", "content": ""}

        for line in lines:
            line = line.strip()
            is_heading = False
            for pattern in section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_heading = True
                    break

            if is_heading and len(line) > 3 and len(line) < 200:
                if current["content"].strip():
                    sections.append(current.copy())
                current = {"title": line, "content": ""}
            else:
                current["content"] += line + " "

        if current["content"].strip():
            sections.append(current.copy())

        return sections

    @staticmethod
    def _extract_metadata(raw_text: str, sections: list[dict]) -> dict:
        """Extract title, authors, abstract from the raw text."""
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

        # Title: usually the first non-empty line
        title = lines[0] if lines else "Untitled"

        # Authors: usually lines 2-4 (before the abstract)
        authors = []
        for line in lines[1:5]:
            if len(line) > 5 and not line.startswith("Abstract"):
                # Simple heuristic: line with commas or "and"
                if "," in line or " and " in line:
                    authors.append(line)

        # Abstract: find section titled "Abstract" or first section content
        abstract = ""
        for sec in sections:
            if "abstract" in sec["title"].lower():
                abstract = sec["content"].strip()
                break
        if not abstract and sections:
            abstract = sections[0]["content"][:500].strip()

        # References: find section titled "References"
        references = []
        for sec in sections:
            if "reference" in sec["title"].lower():
                # Split references by numbering patterns
                refs = re.split(r"\[\d+\]|\d+\.\s", sec["content"])
                references = [r.strip() for r in refs if r.strip() and len(r.strip()) > 10]
                break

        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "sections": [{"title": s["title"], "content": s["content"].strip(), "subsections": []} for s in sections],
            "references": references[:50],
            "figures": [],
        }
