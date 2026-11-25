from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.database.connection import get_db
from app.core.dependency import get_current_admin
from app.models.user import User
from app.models.customer import Customer
from app.models.insurance_application import InsuranceApplication
from app.models.policy import Policy
from app.schemas.customer import CustomerUpdate

from app.models.plan import Plan
from app.models.plan_pricing_rule import PlanPricingRule
from app.models.plan_benefit import PlanBenefit
from app.models.plan_condition import PlanCondition

from app.schemas.plan import PlanCreate

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db), admin: User = Depends(get_current_admin)
):
    total_users = db.query(func.count(User.id)).scalar() or 0

    total_customers = db.query(func.count(Customer.id)).scalar() or 0

    total_admins = (
        db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0
    )

    total_applications = db.query(func.count(InsuranceApplication.id)).scalar() or 0
    total_policies = db.query(func.count(Policy.id)).scalar() or 0

    return {
        "message": "Admin dashboard statistics",
        "total_users": total_users,
        "total_customers": total_customers,
        "total_admins": total_admins,
        "total_applications": total_applications,
        "total_policies": total_policies,
    }


# Only fetch the customer whose value is deleted is False
@router.get("/customers")
def get_all_customers(
    db: Session = Depends(get_db), admin: User = Depends(get_current_admin)
):
    customers = db.query(Customer).filter(Customer.is_deleted == False).all()

    return customers


# Delete the customers
@router.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.is_deleted == False)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found."
        )

    user = db.query(User).filter(User.id == customer.user_id).first()

    customer.is_deleted = True

    if user:
        user.is_deleted = True

    db.commit()

    return {"message": "Customer deleted successfully."}


# Individual customer details view


@router.get("/customers/{customer_id}")
def get_customer_by_id(
    customer_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.is_deleted == False)
        .first()
    )

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    return customer


# For Update the customer API
@router.patch("/customers/{customer_id}")
def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.is_deleted == False)
        .first()
    )

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    update_data = data.model_dump(exclude_unset=True)

    if "email" in update_data:
        new_email = str(update_data["email"]).strip().lower()

        existing_user = (
            db.query(User)
            .filter(User.email == new_email, User.id != customer.user_id)
            .first()
        )

        if existing_user:
            raise HTTPException(status_code=409, detail="Email is already registered.")

        customer.email = new_email

        user = db.query(User).filter(User.id == customer.user_id).first()

        if user:
            user.email = new_email

        update_data.pop("email")

    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    return {"message": "Customer updated successfully.", "customer": customer}


# Create a new insurance plan
@router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        # Create the main plan
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

        # Create pricing rules
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

        # Create plan benefits
        for benefit in data.benefits:
            plan_benefit = PlanBenefit(
                plan_id=new_plan.id,
                benefit_name=benefit.benefit_name,
                description=benefit.description,
                is_included=benefit.is_included,
            )

            db.add(plan_benefit)

        # Create plan conditions
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
            "message": "Insurance plan created successfully.",
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create insurance plan.",
        )
