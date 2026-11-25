from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.connection import get_db
from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.core.dependency import get_current_admin

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    customer = Customer(
        full_name=customer_data.full_name,
        email=customer_data.email,
        phone=customer_data.phone,
    )
    db.add(customer)

    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this email already exists."
        )
    return customer


@router.get("/", response_model=list[CustomerResponse])
def get_customer(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    customers = db.query(Customer).filter(Customer.is_deleted == False).order_by(Customer.created_at.desc()).all()

    return customers
