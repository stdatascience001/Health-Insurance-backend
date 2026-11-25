from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from app.database.connection import get_db
from app.core.dependency import get_current_admin
from app.models.user import User
from app.models.plan import Plan
from app.schemas.plan import PlanCreate
from app.models.plan_benefit import PlanBenefit
from app.models.plan_condition import PlanCondition
from app.models.plan_pricing_rule import PlanPricingRule

router = APIRouter(prefix="/admin/plans", tags=["Plans"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    existing_plan = db.query(Plan).filter(Plan.name == data.name).first()

    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Plan already exists."
        )

    try:
        # 1. Create main plan
        new_plan = Plan(
            name=data.name,
            description=data.description,
            plan_type=data.plan_type,
            min_entry_age=data.min_entry_age,
            max_entry_age=data.max_entry_age,
            duration_months=data.duration_months,
            is_active=True,
        )

        db.add(new_plan)
        db.flush()

        # 2. Create pricing rules
        for rule in data.pricing_rules:
            pricing_rule = PlanPricingRule(
                plan_id=new_plan.id,
                min_age=rule.min_age,
                max_age=rule.max_age,
                coverage_amount=rule.coverage_amount,
                duration_months=rule.duration_months,
                premium_frequency=rule.premium_frequency,
                premium_amount=rule.premium_amount,
                is_active=rule.is_active,
            )
            db.add(pricing_rule)

        # 3. Create benefits
        for benefit in data.benefits:
            plan_benefit = PlanBenefit(
                plan_id=new_plan.id,
                benefit_name=benefit.benefit_name,
                description=benefit.description,
                is_included=benefit.is_included,
            )
            db.add(plan_benefit)

        # 4. Create conditions
        for condition in data.conditions:
            plan_condition = PlanCondition(
                plan_id=new_plan.id,
                condition_type=condition.condition_type,
                condition_value=condition.condition_value,
                description=condition.description,
            )
            db.add(plan_condition)

        db.commit()
        db.refresh(new_plan)

        return {
            "message": "Health insurance plan created successfully.",
            "plan": {
                "id": str(new_plan.id),
                "name": new_plan.name,
                "description": new_plan.description,
                "plan_type": new_plan.plan_type,
                "min_entry_age": new_plan.min_entry_age,
                "max_entry_age": new_plan.max_entry_age,
                "duration_months": new_plan.duration_months,
                "is_active": new_plan.is_active,
            },
        }

    except Exception:
        db.rollback()
        raise


# Admin: Get ALL created plans
@router.get("/")
def get_plans(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    plans = (
        db.query(Plan)
        .options(
            joinedload(Plan.pricing_rules),
            joinedload(Plan.benefits),
            joinedload(Plan.conditions),
        )
        .all()
    )

    return plans

# Customer: Get available plans
@router.get("/available/plans")
def get_available_plans(db: Session = Depends(get_db)):
    plans = (
        db.query(Plan)
        .options(
            joinedload(Plan.pricing_rules),
            joinedload(Plan.benefits),
            joinedload(Plan.conditions),
        )
        .filter(Plan.is_active == True)
        .all()
    )

    return plans


# Admin: Activate or deactivate a plan
@router.patch("/{plan_id}/status")
def update_plan_status(
    plan_id: UUID,
    is_active: bool = Body(..., embed=True),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found."
        )

    plan.is_active = is_active

    try:
        db.commit()
        db.refresh(plan)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update plan status.",
        )

    return {
        "message": f"Plan {'activated' if is_active else 'deactivated'} successfully.",
        "plan": plan,
    }

# Route for the specific plan 
# Admin: Get a specific plan with all its details
@router.get("/{plan_id}")
def get_plan_by_id(
    plan_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    plan = (
        db.query(Plan)
        .options(
            joinedload(Plan.pricing_rules),
            joinedload(Plan.benefits),
            joinedload(Plan.conditions)
        )
        .filter(Plan.id == plan_id)
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance plan not found."
        )

    return plan

# Admin: Update complete insurance plan
@router.put("/{plan_id}")
def update_plan(
    plan_id: UUID,
    data: PlanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    plan = db.query(Plan).filter(
        Plan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance plan not found."
        )

    existing_name = db.query(Plan).filter(
        Plan.name == data.name,
        Plan.id != plan_id
    ).first()

    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another plan with this name already exists."
        )

    try:
        # 1. Update main plan information
        plan.name = data.name
        plan.description = data.description
        plan.plan_type = data.plan_type
        plan.min_entry_age = data.min_entry_age
        plan.max_entry_age = data.max_entry_age
        plan.duration_months = data.duration_months

        # 2. Update pricing rules
        existing_rules = {
            rule.id: rule for rule in plan.pricing_rules
        }

        updated_rules = []
        seen_rule_ids = set()

        for item in data.pricing_rules:
            if item.id:
                rule = existing_rules.get(item.id)

                if not rule or item.id in seen_rule_ids:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid or duplicate pricing rule ID."
                    )

                seen_rule_ids.add(item.id)

            else:
                rule = PlanPricingRule()
                db.add(rule)

            rule.min_age = item.min_age
            rule.max_age = item.max_age
            rule.coverage_amount = item.coverage_amount
            rule.duration_months = item.duration_months
            rule.premium_frequency = item.premium_frequency
            rule.premium_amount = item.premium_amount
            rule.is_active = item.is_active

            updated_rules.append(rule)

        plan.pricing_rules = updated_rules

        # 3. Update benefits
        existing_benefits = {
            benefit.id: benefit for benefit in plan.benefits
        }

        updated_benefits = []
        seen_benefit_ids = set()

        for item in data.benefits:
            if item.id:
                benefit = existing_benefits.get(item.id)

                if not benefit or item.id in seen_benefit_ids:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid or duplicate benefit ID."
                    )

                seen_benefit_ids.add(item.id)

            else:
                benefit = PlanBenefit()
                db.add(benefit)

            benefit.benefit_name = item.benefit_name
            benefit.description = item.description
            benefit.is_included = item.is_included

            updated_benefits.append(benefit)

        plan.benefits = updated_benefits

        # 4. Update conditions
        existing_conditions = {
            condition.id: condition for condition in plan.conditions
        }

        updated_conditions = []
        seen_condition_ids = set()

        for item in data.conditions:
            if item.id:
                condition = existing_conditions.get(item.id)

                if not condition or item.id in seen_condition_ids:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid or duplicate condition ID."
                    )

                seen_condition_ids.add(item.id)

            else:
                condition = PlanCondition()
                db.add(condition)

            condition.condition_type = item.condition_type
            condition.condition_value = item.condition_value
            condition.description = item.description

            updated_conditions.append(condition)

        plan.conditions = updated_conditions

        db.commit()
        db.refresh(plan)

        return {
            "message": "Insurance plan updated successfully.",
            "plan": {
                "id": str(plan.id),
                "name": plan.name,
                "description": plan.description,
                "plan_type": plan.plan_type,
                "min_entry_age": plan.min_entry_age,
                "max_entry_age": plan.max_entry_age,
                "duration_months": plan.duration_months,
                "is_active": plan.is_active
            }
        }

    except Exception:
        db.rollback()
        raise