import uuid
from app.models.super_admin import SuperAdmin

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from app.database.connection import get_db
from app.models.user import User

security = HTTPBearer()

# This code will perform 3 opertations....
# 1. Extracts the JWT token from the request's Authorization header.
# 2. Validates the token, including its signature and expiration.
# 3. Finds the corresponding user in the database.


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None or user.is_deleted or not user.is_active:
        raise credentials_exception

    return user


# for the admininstartor
def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have the permission to access this route.",
        )
    return current_user

# Super Admin authentication
def get_current_super_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate Super Admin credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        super_admin_id = payload.get("sub")
        role = payload.get("role")

        if super_admin_id is None or role != "super_admin":
            raise credentials_exception

        super_admin_id = uuid.UUID(super_admin_id)

    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    super_admin = (
        db.query(SuperAdmin)
        .filter(SuperAdmin.id == super_admin_id)
        .first()
    )

    if super_admin is None or not super_admin.is_active:
        raise credentials_exception

    return super_admin