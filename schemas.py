from pydantic import BaseModel
from typing import List, Dict, Literal

class EvaluationPlanBase(BaseModel):
    model: str
    input_type: Literal["text", "text_image"]
    test_suite: str
    thresholds: Dict[str, float]
    impact_tags: List[str] = []
    control_tags: List[str] = []
    reproducibility_lock: bool = False

class EvaluationPlanCreate(EvaluationPlanBase):
    pass

class EvaluationPlanOut(EvaluationPlanBase):
    id: int

    class Config:
        from_attributes = True
