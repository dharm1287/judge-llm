from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Literal
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy import ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
Base = declarative_base()
#Base.metadata.create_all(bind=engine)



# ------------------------- Database Models for Test Suites -------------------------

class TestSuite(Base):
    __tablename__ = "test_suites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_name = Column(String)
    threshold = Column(Integer)
    

    tools_selected = Column(ARRAY(String), nullable=False)
    sample_prompts = Column(ARRAY(String))
    rmf_tags = Column(ARRAY(String))
    #request_governance_approval = Column(Integer, default=0)
    request_governance_approval = Column(Boolean, default=False)

    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)

    versions = relationship("TestSuiteVersion", back_populates="parent")

class TestSuiteVersion(Base):
    __tablename__ = "test_suite_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("test_suites.id"))
    suite_name = Column(String)
    tools_selected = Column(JSON)
    threshold = Column(Integer)
    sample_prompts = Column(JSON)
    rmf_tags = Column(JSON)
    version = Column(Integer)
    updated_by = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship("TestSuite", back_populates="versions")

class TestSuiteUsageLog(Base):
    __tablename__ = "test_suite_usage_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("test_suites.id"))
    evaluation_id = Column(String)  # could be a UUID or string reference
    used_by = Column(String)        # replace with real user id from auth if available
    timestamp = Column(DateTime, default=datetime.utcnow)

    suite = relationship("TestSuite", backref="usage_logs")


# ------------------------- Database Models for Eval Dashboard -------------------------
class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    use_case = Column(String, index=True)
    model = Column(String)
    team = Column(String)
    status = Column(String)  # pass / fail
    flagged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer)
    action = Column(String)  # e.g., flag, approve, reject
    user = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

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

from sqlalchemy import Column, Integer, String, Boolean, JSON

class EvaluationPlan(Base):
    __tablename__ = "evaluation_plans"
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, nullable=False)
    input_type = Column(String, nullable=False)
    test_suite = Column(String, nullable=False)
    thresholds = Column(JSON, nullable=False)
    impact_tags = Column(JSON, default=[])
    control_tags = Column(JSON, default=[])
    reproducibility_lock = Column(Boolean, default=False)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("evaluation_plans.id"))
    result = Column(JSON, nullable=False)
    rmf_tags = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

