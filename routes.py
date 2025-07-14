from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import crud, schemas
import models
from fastapi import HTTPException
router = APIRouter()
from database import SessionLocal, engine
from models import EvaluationPlan, EvaluationRun, TestSuite, TestSuiteUsageLog
from datetime import datetime
from integrations import run_with_promptfoo, run_with_langchain, run_with_ragas

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/plans/", response_model=schemas.EvaluationPlanOut)
def create_plan(plan: schemas.EvaluationPlanCreate, db: Session = Depends(get_db)):
    return crud.create_evaluation_plan(db, plan)

@router.get("/plans/", response_model=list[schemas.EvaluationPlanOut])
def read_plans(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_evaluation_plans(db, skip, limit)

@router.post("/plans/{plan_id}/execute")
def execute_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(EvaluationPlan).filter(EvaluationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Evaluation plan not found")

    # Fetch the corresponding test suite
    test_suite = db.query(TestSuite).filter(TestSuite.suite_name == plan.test_suite).first()
    if not test_suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    # Run tools based on test suite config
    results = []
    rmf_tags = set()

    for tool in test_suite.tools_selected:
        if tool == "PromptFoo":
            result = run_with_promptfoo(plan, test_suite)
        elif tool == "LangChain":
            result = run_with_langchain(plan, test_suite)
        elif tool == "RAGAS":
            result = run_with_ragas(plan, test_suite)
        else:
            continue  #
        results.append(result)
        rmf_tags.update(result.get("rmf_tags", []))

    # Log Evaluation Run
    run_record = EvaluationRun(
        plan_id=plan.id,
        result=results,
        rmf_tags=list(rmf_tags),
        timestamp=datetime.utcnow()
    )
    db.add(run_record)

    # Log Test Suite Usage
    usage_log = TestSuiteUsageLog(
        suite_id=test_suite.id,
        evaluation_id=str(plan.id),
        used_by="system"  # or from auth context
    )
    db.add(usage_log)

    db.commit()

    return {
        "plan_id": plan.id,
        "status": "Executed",
        "tools_used": test_suite.tools_selected,
        "results": results
    }

