from pydantic import BaseModel


class ResearchGap(BaseModel):
    description: str
    gap_type: str = "methodological"
    severity: str = "moderate"
    evidence: str = ""


class FutureDirection(BaseModel):
    title: str
    description: str
    feasibility_score: float = 0.5
    estimated_impact: str = "medium"
    required_resources: list[str] = []


class GapAnalysis(BaseModel):
    gaps: list[ResearchGap] = []
    future_directions: list[FutureDirection] = []
    open_questions: list[str] = []
    overall_assessment: str = ""
