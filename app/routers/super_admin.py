from fastapi import APIRouter, Depends

from app.core.dependency import get_current_super_admin
from app.models.super_admin import SuperAdmin

router = APIRouter(
    prefix="/super-admin",
    tags=["Super Admin"],
)


@router.get("/me")
def get_super_admin_profile(
    current_super_admin: SuperAdmin = Depends(get_current_super_admin),
):
    return {
        "id": str(current_super_admin.id),
        "full_name": current_super_admin.full_name,
        "email": current_super_admin.email,
        "role": current_super_admin.role,
    }