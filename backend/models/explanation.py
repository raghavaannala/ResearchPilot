from pydantic import BaseModel


class SimplifiedExplanation(BaseModel):
    eli5_summary: str
    undergraduate_summary: str
    expert_summary: str
    key_takeaways: list[str] = []
    visual_analogies: list[str] = []
