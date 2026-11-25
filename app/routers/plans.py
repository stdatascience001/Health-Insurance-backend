from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.connection import get_db
from app.core.dependency import get_current_admin
from app.models.user import User
from app.models.plan import Plan
from app.schemas.plan import PlanCreate

router = APIRouter(prefix="/admin/plans", tags=["Plans"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    existing_plan = db.query(Plan).filter(
        Plan.name == data.name
    ).first()

    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plan already exists."
        )

    new_plan = Plan(
        name=data.name,
        description=data.description,
        premium_amount=data.premium_amount,
        coverage_amount=data.coverage_amount,
        duration_months=data.duration_months
    )

    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    return {
        "message": "Health insurance plan created successfully.",
        "plan": new_plan
    }

#Admin: Get ALL the created plans 
@router.get("/")
def get_plans(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(Plan).all()
# Customer: Get available plans
@router.get("/available/plans")
def get_available_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(
        Plan.is_active == True
    ).all()

    return plans

# Admin: Activate or deactivate a plan
@router.patch("/{plan_id}/status")
def update_plan_status(
    plan_id: UUID,
    is_active: bool = Body(..., embed=True),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found."
        )

    plan.is_active = is_active

    try:
        db.commit()
        db.refresh(plan)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update plan status."
        )

    return {
        "message": f"Plan {'activated' if is_active else 'deactivated'} successfully.",
        "plan": plan
    }