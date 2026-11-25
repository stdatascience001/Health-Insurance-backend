from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.connection import get_db
from app.models.user import User
from app.models.customer import Customer
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.schemas.customer import CustomerUpdate
from app.core.security import hash_password
from app.schemas.auth import LoginRequest, LoginResponse
from app.core.security import verify_password, create_access_token
from app.core.dependency import get_current_user, get_current_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])

# 1. Register Endpoint-----------------


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    email = str(data.email).strip().lower()

    # Check whether the email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    exisiting_customer = db.query(Customer).filter(Customer.email == email).first()

    if exisiting_customer or existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered."
        )
    # Hash the password before saving it
    hashed_password = hash_password(data.password)

    try:
        # Create the new user account if the user doesn't exists
        new_user = User(email=email, password_hash=hashed_password, role="customer")
        db.add(new_user)

        # Save the user temporarily to generate its ID
        db.flush()

        # Create the customer profile and link it to the user...
        new_customer = Customer(
            user_id=new_user.id, full_name=data.full_name, email=email, phone=data.phone
        )
        db.add(new_customer)

        # Save both records togeather
        db.commit()
        db.refresh(new_customer)

        return RegisterResponse(
            message="Registeration Successfull.", customer_id=str(new_customer.id)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered."
        )
    except Exception:
        db.rollback()
        raise


# 2. Login Endpoint --------------------
@router.post("/login", response_model=LoginResponse)
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    email = str(data.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if (not user or user.is_deleted or not user.is_active or not verify_password(data.password, user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(user_id=user.id, role=user.role)
    return LoginResponse(access_token=access_token)

# For the current logged in user...
@router.get('/me')
def get_my_account(
    current_user: User = Depends(get_current_user)
):
    customer_info = None
    if current_user.customer and not current_user.customer.is_deleted:
        customer_info = {
            "id": str(current_user.customer.id),
            "full_name": current_user.customer.full_name,
            "email": current_user.customer.email,
            "phone": current_user.customer.phone,
            "created_at": current_user.customer.created_at.isoformat() if current_user.customer.created_at else None,
        }
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "customer": customer_info
    }


# Update profile for logged in user (customer self-service)
@router.patch('/me')
def update_my_profile(
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.customer or current_user.customer.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found."
        )

    if data.full_name is not None and data.full_name.strip():
        current_user.customer.full_name = data.full_name.strip()
    if data.phone is not None:
        clean_phone = data.phone.strip()
        current_user.customer.phone = clean_phone if clean_phone else None

    db.commit()
    db.refresh(current_user.customer)

    return {
        "message": "Profile updated successfully.",
        "customer": {
            "id": str(current_user.customer.id),
            "full_name": current_user.customer.full_name,
            "email": current_user.customer.email,
            "phone": current_user.customer.phone,
            "created_at": current_user.customer.created_at.isoformat() if current_user.customer.created_at else None,
        }
    }

# For the admin role 
@router.get("/admin")
def admin_test( admin: User = Depends(get_current_admin)):
    return {
        "message": "Welcome Admin!",
        "id": str(admin.id),
        "email": admin.email,
        "role": admin.role
    }
