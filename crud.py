from sqlalchemy.orm import Session
import models, schemas

def create_evaluation_plan(db: Session, plan: schemas.EvaluationPlanCreate):
    db_plan = models.EvaluationPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_evaluation_plans(db: Session, skip=0, limit=10):
    return db.query(models.EvaluationPlan).offset(skip).limit(limit).all()
