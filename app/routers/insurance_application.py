import uuid
from uuid import UUID
from datetime import date
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.models.plan import Plan
from app.models.customer import Customer
from app.models.insurance_application import InsuranceApplication
from app.models.policy import Policy

from app.schemas.insurance_application import (
    InsuranceApplicationCreate,
    InsuranceApplicationReview,
)

from app.core.dependency import get_current_user, get_current_admin

router = APIRouter(prefix="/applications", tags=["Insurance Applications"])


# Helper function to format application response.
# The format_application() function is used to convert an Insurance Application database object into a Python dictionary that can be returned as an API response (JSON).
def format_application(application):
    return {
        "id": str(application.id),
        "customer_id": str(application.customer_id),
        "plan_id": str(application.plan_id),
        "plan_name": application.plan.name,
        "premium_amount": str(application.premium_amount),
        "coverage_amount": str(application.coverage_amount),
        "date_of_birth": application.date_of_birth.isoformat(),
        "gender": application.gender,
        "address": application.address,
        "nominee_name": application.nominee_name,
        "nominee_relationship": application.nominee_relationship,
        "nominee_dob": (
            application.nominee_dob.isoformat() if application.nominee_dob else None
        ),
        "nominee_phone": application.nominee_phone,
        "medical_history": application.medical_history,
        "status": application.status,
        "rejection_reason": application.rejection_reason,
        "created_at": (
            application.created_at.isoformat() if application.created_at else None
        ),
    }


# 1. Submit Insurance Application
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_application(
    data: InsuranceApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get logged-in customer's profile
    customer = current_user.customer

    if not customer or customer.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found."
        )

    # Check whether selected plan exists and is active
    plan = (
        db.query(Plan).filter(Plan.id == data.plan_id, Plan.is_active == True).first()
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance plan not found or inactive.",
        )

    # Create application
    application = InsuranceApplication(
        customer_id=customer.id,
        plan_id=plan.id,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        address=data.address,
        nominee_name=data.nominee_name,
        nominee_relationship=data.nominee_relationship,
        nominee_dob=data.nominee_dob,
        nominee_phone=data.nominee_phone,
        medical_history=data.medical_history,
        premium_amount=plan.premium_amount,
        coverage_amount=plan.coverage_amount,
        status="pending",
    )

    try:
        db.add(application)
        db.commit()
        db.refresh(application)

        return {
            "message": "Insurance application submitted successfully.",
            "application": format_application(application),
        }

    except Exception:
        db.rollback()
        raise


# 2. Customer views their own applications
@router.get("/my")
def get_my_applications(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    customer = current_user.customer

    if not customer or customer.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found."
        )

    applications = (
        db.query(InsuranceApplication)
        .filter(InsuranceApplication.customer_id == customer.id)
        .order_by(InsuranceApplication.created_at.desc())
        .all()
    )

    return [format_application(application) for application in applications]


# 3. Admin views all applications
@router.get("/")
def get_all_applications(
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    query = db.query(InsuranceApplication)

    # Get total number of applications
    total = query.count()

    # calculate how records to skip
    offset = (page - 1) * limit

    # Fetch only the records required for the current page
    applications = (
        query.order_by(
            InsuranceApplication.created_at.desc(),
            InsuranceApplication.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        {
            **format_application(application),
            "customer_name": application.customer.full_name,
            "customer_email": application.customer.email,
        }
        for application in applications
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


# 4. View a single application
@router.get("/{application_id}")
def get_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = (
        db.query(InsuranceApplication)
        .filter(InsuranceApplication.id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found."
        )

    # Customers can only view their own applications
    if current_user.role == "customer":
        customer = current_user.customer

        if (
            not customer
            or customer.is_deleted
            or application.customer_id != customer.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access this application.",
            )

    elif current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied."
        )

    return format_application(application)


# for the admin approval and rejection of application....
@router.patch("/{application_id}/review")
def review_application(
    application_id: UUID,
    data: InsuranceApplicationReview,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    application = (
        db.query(InsuranceApplication)
        .filter(InsuranceApplication.id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if application.status != "pending":
        raise HTTPException(
            status_code=400, detail="Only pending applications can be reviewed."
        )

    application.status = data.status

    if data.status == "rejected":
        application.rejection_reason = (
            data.rejection_reason.strip() if data.rejection_reason else None
        )
    else:
        application.rejection_reason = None

        # This is when the status is approved by the admin the policy gets issued to the customer with the below details....

        start_date = date.today()
        policy = Policy(
            policy_number=f"POL-{uuid.uuid4().hex[:10].upper()}",
            application_id=application.id,
            customer_id=application.customer_id,
            plan_id=application.plan_id,
            premium_amount=application.premium_amount,
            coverage_amount=application.coverage_amount,
            start_date=start_date,
            end_date=start_date
            + relativedelta(
                months=application.plan.duration_months
            ),  # Temporary; we'll calculate this later.
        )

        db.add(policy)

    db.commit()
    db.refresh(application)

    return {
        "message": f"Application {data.status} successfully.",
        "application": format_application(application),
    }
