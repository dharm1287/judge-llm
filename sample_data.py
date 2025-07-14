from pydantic import BaseModel
from datetime import datetime

# ------------------------- Pydantic Models -------------------------
class EvaluationMetric(BaseModel):
    total_evaluations: int
    pass_rate: float
    flagged_percentage: float

class TimeSeriesData(BaseModel):
    month: str
    evaluations: int

class UseCaseMetrics(BaseModel):
    use_case: str
    evaluations: int
    flagged_percentage: float

class ModelDistribution(BaseModel):
    model: str
    percentage: float

class TeamDistribution(BaseModel):
    team: str
    percentage: float

class EvaluationRecord(BaseModel):
    id: int
    use_case: str
    model: str
    team: str
    status: str
    flagged: bool
    created_at: datetime

# ------------------------- Sample Data -------------------------
dummy_metrics = EvaluationMetric(total_evaluations=128, pass_rate=78.0, flagged_percentage=12.0)
dummy_time_series = [
    TimeSeriesData(month="Jul", evaluations=20),
    TimeSeriesData(month="Aug", evaluations=15),
    TimeSeriesData(month="Sep", evaluations=25),
    TimeSeriesData(month="Oct", evaluations=28),
    TimeSeriesData(month="Nov", evaluations=21),
    TimeSeriesData(month="Dec", evaluations=32),
    TimeSeriesData(month="Jan", evaluations=27),
]
dummy_use_cases = [
    UseCaseMetrics(use_case="Customer Support", evaluations=56, flagged_percentage=8.0),
    UseCaseMetrics(use_case="Document Review", evaluations=34, flagged_percentage=15.0),
    UseCaseMetrics(use_case="Product Feedback", evaluations=22, flagged_percentage=19.0),
    UseCaseMetrics(use_case="Content Generation", evaluations=16, flagged_percentage=6.0),
]
dummy_models = [
    ModelDistribution(model="B", percentage=45.0),
    ModelDistribution(model="C", percentage=35.0),
    ModelDistribution(model="X", percentage=20.0),
]
dummy_teams = [
    TeamDistribution(team="X", percentage=42.0),
    TeamDistribution(team="Y", percentage=33.0),
    TeamDistribution(team="Z", percentage=26.0),
]
