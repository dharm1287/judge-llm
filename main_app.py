from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
#import crud, schemas
from database import SessionLocal, engine
from fastapi import Query, HTTPException
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from docx import Document
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
import json
from prompts import prompt_template_risk
from utils import *
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from models import TestSuite, Base, TestSuiteVersion, TestSuiteUsageLog
from sample_data import *
import routes
load_dotenv()

app = FastAPI()
app.include_router(routes.router)

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv('OPEN_AI_API_KEY')

# Create tables (use alembic in prod)
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for request
class TestSuiteCreateRequest(BaseModel):
    suite_name: str
    tools_selected: List[str]
    threshold: int
    sample_prompts: List[str]
    rmf_tags: List[str]
    request_governance_approval: Optional[bool] = False

# Pydantic model for response
class TestSuiteCreateResponse(BaseModel):
    suite_id: str
    message: str

prompt_template = prompt_template_risk
# LangChain model
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")



@app.post("/analyze-scope/")
async def analyze_scope(file: UploadFile = File(...)):
    contents = await file.read()
    content_type = file.content_type
    print(f"Received file with content type: {content_type}")
    # Handle based on file type
    if content_type == "application/pdf":
        text = extract_text_from_pdf(contents)
    elif content_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]:
        text = extract_text_from_docx(contents)
    elif content_type == "text/plain":
        text = contents.decode("utf-8")  # Only decode for plain text
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF, DOCX, or TXT file.")

    # Format prompt with document content
    prompt = prompt_template.format(doc_content=text)
    raw_response = llm.predict(prompt)
    # # Get response from LLM

    try:
        response_json = json.loads(raw_response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM response is not valid JSON. Try with simpler or smaller document.")

    return response_json


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for request
class TestSuiteCreateRequest(BaseModel):
    suite_name: str
    tools_selected: List[str]
    threshold: int
    sample_prompts: List[str]
    rmf_tags: List[str]
    request_governance_approval: Optional[bool] = False

# Pydantic model for response
class TestSuiteCreateResponse(BaseModel):
    suite_id: str
    message: str

@app.post("/test-suites/", response_model=TestSuiteCreateResponse)
async def create_test_suite(data: TestSuiteCreateRequest, db: Session = Depends(get_db)):
    suite = TestSuite(
        suite_name=data.suite_name,
        tools_selected=data.tools_selected,
        threshold=data.threshold,
        sample_prompts=data.sample_prompts,
        rmf_tags=data.rmf_tags,
        request_governance_approval=data.request_governance_approval
    )
    db.add(suite)
    db.commit()
    db.refresh(suite)

    return TestSuiteCreateResponse(
        suite_id=str(suite.id),
        message="Test suite created successfully."
    )


@app.get("/test-suites/")
def list_test_suites(db: Session = Depends(get_db)):
    suites = db.query(TestSuite).all()
    #suites = db.query(TestSuite).filter(TestSuite.deleted_at.is_(None)).all()

    return suites

@app.get("/test-suites/{id}")
def get_test_suite(id: str, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return suite


@app.put("/test-suites/{id}")
def update_test_suite(id: str, data: TestSuiteCreateRequest, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    # Save current version before update
    version_entry = TestSuiteVersion(
        parent_id=suite.id,
        suite_name=suite.suite_name,
        tools_selected=suite.tools_selected,
        threshold=suite.threshold,
        sample_prompts=suite.sample_prompts,
        rmf_tags=suite.rmf_tags,
        version=suite.version,
        updated_by="test_user",  # Replace with actual user info
        updated_at=datetime.utcnow()
    )
    db.add(version_entry)

    # Update the main record
    suite.suite_name = data.suite_name
    suite.tools_selected = data.tools_selected
    suite.threshold = data.threshold
    suite.sample_prompts = data.sample_prompts
    suite.rmf_tags = data.rmf_tags
    suite.request_governance_approval = data.request_governance_approval
    suite.version += 1
    suite.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(suite)

    return {"message": "Test suite updated successfully", "suite_id": str(suite.id), "version": suite.version}

@app.get("/test-suites/{id}/versions")
def get_version_history(id: str, db: Session = Depends(get_db)):
    versions = db.query(TestSuiteVersion).filter(TestSuiteVersion.parent_id == id).order_by(TestSuiteVersion.version.desc()).all()
    return versions


@app.delete("/test-suites/{id}")
def delete_test_suite(id: str, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    suite.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Test suite soft-deleted successfully"}

@app.patch("/test-suites/{id}/approve")
def approve_suite(id: str, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    suite.request_governance_approval = True
    suite.approved_by = "admin_user_id"  # Get from auth
    suite.approved_at = datetime.utcnow()

    db.commit()
    return {"message": "Governance approval recorded"}

class UsageLogRequest(BaseModel):
    evaluation_id: str
    used_by: Optional[str] = "anonymous_user"  # Replace with real user if available

@app.post("/test-suites/{id}/log-usage")
def log_test_suite_usage(id: str, log: UsageLogRequest, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == id, TestSuite.deleted_at.is_(None)).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    usage = TestSuiteUsageLog(
        suite_id=id,
        evaluation_id=log.evaluation_id,
        used_by=log.used_by,
        timestamp=datetime.utcnow()
    )

    db.add(usage)
    db.commit()
    return {"message": "Usage logged successfully"}

@app.get("/test-suites/{id}/usage")
def get_suite_usage(id: str, db: Session = Depends(get_db)):
    logs = db.query(TestSuiteUsageLog).filter(TestSuiteUsageLog.suite_id == id).order_by(TestSuiteUsageLog.timestamp.desc()).all()
    return logs

# ------------------------- API Routes for Eval Dashboard -------------------------

@app.get("/api/metrics/overview", response_model=EvaluationMetric)
def get_metrics():
    return dummy_metrics

@app.get("/api/metrics/time-series", response_model=List[TimeSeriesData])
def get_time_series():
    return dummy_time_series

@app.get("/api/metrics/by-use-case", response_model=List[UseCaseMetrics])
def get_by_use_case():
    return dummy_use_cases

@app.get("/api/metrics/by-model", response_model=List[ModelDistribution])
def get_by_model():
    return dummy_models

@app.get("/api/metrics/by-team", response_model=List[TeamDistribution])
def get_by_team():
    return dummy_teams











