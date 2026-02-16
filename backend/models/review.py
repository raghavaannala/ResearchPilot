from pydantic import BaseModel


class ThematicGroup(BaseModel):
    theme: str
    papers: list[str] = []
    summary: str = ""


class LiteratureReview(BaseModel):
    introduction: str = ""
    thematic_groups: list[ThematicGroup] = []
    chronological_narrative: str = ""
    comparison_table: list[dict] = []
    methodology_evolution: str = ""
    conclusion: str = ""
    citation_count: int = 0
