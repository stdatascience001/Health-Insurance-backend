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
