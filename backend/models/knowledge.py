from pydantic import BaseModel
from typing import Optional


class MethodologyBreakdown(BaseModel):
    approach: str
    steps: list[str] = []
    algorithms: list[str] = []
    model_architecture: Optional[str] = None
    training_details: Optional[str] = None


class DatasetInfo(BaseModel):
    name: str
    description: str
    size: Optional[str] = None
    source: Optional[str] = None


class Result(BaseModel):
    metric: str
    value: str
    comparison: Optional[str] = None


class KnowledgeCard(BaseModel):
    problem_statement: str
    hypothesis: Optional[str] = None
    methodology: MethodologyBreakdown
    datasets: list[DatasetInfo] = []
    evaluation_metrics: list[str] = []
    key_results: list[Result] = []
    contributions: list[str] = []
    limitations: list[str] = []
    keywords: list[str] = []
