import hmac

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.microsoft_auth import (
    get_microsoft_login_url,
    get_microsoft_user_token,
    get_microsoft_user_profile,
    generate_oauth_state,
    verify_oauth_state,
)
from app.models.super_admin import SuperAdmin

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

    if (
        not user
        or user.is_deleted
        or not user.is_active
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(user_id=user.id, role=user.role)
    return LoginResponse(access_token=access_token)


# For the current logged in user...
@router.get("/me")
def get_my_account(current_user: User = Depends(get_current_user)):
    customer_info = None
    if current_user.customer and not current_user.customer.is_deleted:
        customer_info = {
            "id": str(current_user.customer.id),
            "full_name": current_user.customer.full_name,
            "email": current_user.customer.email,
            "phone": current_user.customer.phone,
            "created_at": (
                current_user.customer.created_at.isoformat()
                if current_user.customer.created_at
                else None
            ),
        }
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "customer": customer_info,
    }

# Microsoft Login Endpoint...
@router.get("/microsoft/login")
def microsoft_login(response: Response):

    state = generate_oauth_state()
    login_url = get_microsoft_login_url(state)

    response = RedirectResponse(url=login_url)
    response.set_cookie(
        key="microsoft_oauth_state",
        value=state,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=600,
    )
    return {"authorization_url": login_url}


# Update profile for logged in user (customer self-service)
@router.patch("/me")
def update_my_profile(
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.customer or current_user.customer.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found."
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
            "created_at": (
                current_user.customer.created_at.isoformat()
                if current_user.customer.created_at
                else None
            ),
        },
    }


# For the admin role
@router.get("/admin")
def admin_test(admin: User = Depends(get_current_admin)):
    return {
        "message": "Welcome Admin!",
        "id": str(admin.id),
        "email": admin.email,
        "role": admin.role,
    }


# For the admin through microsoft login
@router.get("/microsoft/callback", response_model=LoginResponse)
def microsoft_callback(
    request: Request,
    response: Response,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    # 1. Validate OAuth state
    stored_state = request.cookies.get("microsoft_oauth_state")

    if (
        not state
        or not stored_state
        or not hmac.compare_digest(state, stored_state)
        or not verify_oauth_state(state)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired Microsoft authentication state.",
        )

    # Clear OAuth state cookie after successful validation
    response.delete_cookie(
        key="microsoft_oauth_state",
        httponly=True,
        secure=False,
        samesite="lax",
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Microsoft authentication was unsuccessful.",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is missing.",
        )

    # 2. Exchange authorization code for Microsoft tokens
    try:
        token_result = get_microsoft_user_token(code)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Microsoft authentication failed.",
        )

    access_token = token_result.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to retrieve Microsoft access token.",
        )

    # 3. Retrieve Microsoft profile through Graph API
    try:
        microsoft_profile = get_microsoft_user_profile(access_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to retrieve Microsoft profile.",
        )

    microsoft_user_id = microsoft_profile.get("id")

    microsoft_email = microsoft_profile.get("mail") or microsoft_profile.get(
        "userPrincipalName"
    )

    full_name = microsoft_profile.get("displayName")

    if not microsoft_user_id or not microsoft_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incomplete Microsoft profile information.",
        )

    microsoft_email = microsoft_email.strip().lower()

    # 4. Check whether this Microsoft account already exists
    super_admin = (
        db.query(SuperAdmin)
        .filter(SuperAdmin.microsoft_user_id == microsoft_user_id)
        .first()
    )

    if super_admin:
        # Check whether the Super Admin account is active
        if not super_admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This Super Admin account is inactive.",
            )
        if super_admin.email.strip().lower() != microsoft_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Microsoft account information does not match.",
            )
    else:
        # 5. Bootstrap the first Super Admin
        existing_super_admin = db.query(SuperAdmin).first()

        authorized_email = settings.MICROSOFT_ADMIN_EMAIL.strip().lower()

        if existing_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This Microsoft account is not registered as a Super Admin.",
            )

        if microsoft_email != authorized_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This Microsoft account is not authorized as a Super Admin.",
            )

        super_admin = SuperAdmin(
            full_name=full_name or microsoft_email,
            email=microsoft_email,
            microsoft_user_id=microsoft_user_id,
            role="super_admin",
            is_active=True,
        )

        db.add(super_admin)

        try:
            db.commit()
            db.refresh(super_admin)

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Super Admin account already exists.",
            )

        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create Super Admin account.",
            )

    # 6. Generate JWT using database ID and database role
    access_token = create_access_token(
        user_id=str(super_admin.id),
        role=super_admin.role,
    )

    return LoginResponse(access_token=access_token)
