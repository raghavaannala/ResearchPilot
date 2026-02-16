from pydantic import BaseModel, Field
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
    references: list[str] = []
    figures: list[FigureMetadata] = []
    source_type: str  # "pdf", "url", "arxiv"
    raw_text: str
    page_count: int = 0
