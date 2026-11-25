from uuid import UUID as PyUUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.policy import Policy
from app.models.user import User
from app.core.dependency import get_current_user, get_current_admin
from app.models.policy_cancellation import PolicyCancellationRequest
from app.schemas.policy_cancellation import (
    PolicyCancellationCreate,
    PolicyCancellationResponse,
    PolicyCancellationReview
)

router = APIRouter(prefix="/policies", tags=["Policies"])


def format_policy(policy):
    return {
        "id": str(policy.id),
        "policy_number": policy.policy_number,
        "application_id": str(policy.application_id),
        "customer_id": str(policy.customer_id),
        "plan_id": str(policy.plan_id),
        "plan_name": policy.plan.name,
        "premium_amount": str(policy.premium_amount),
        "coverage_amount": str(policy.coverage_amount),
        "start_date": policy.start_date.isoformat(),
        "end_date": policy.end_date.isoformat(),
        "status": policy.status,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
    }


# function for the policy cancellation request...
def format_cancellation_request(request):
    return {
        "id": str(request.id),
        "policy_id": str(request.policy_id),
        "policy_number": request.policy.policy_number if request.policy else None,
        "customer_id": str(request.customer_id),
        "customer_name": request.customer.full_name if request.customer else None,
        "customer_email": request.customer.email if request.customer else None,
        "reason": request.reason,
        "additional_comments": request.additional_comments,
        "status": request.status,
        "admin_remarks": request.admin_remarks,
        "requested_at": (
            request.requested_at.isoformat() if request.requested_at else None
        ),
        "reviewed_at": (
            request.reviewed_at.isoformat() if request.reviewed_at else None
        ),
    }


# Customer: View own policies
@router.get("/my")
def get_my_policies(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    customer = current_user.customer

    if not customer or customer.is_deleted:
        raise HTTPException(status_code=404, detail="Customer not found.")

    policies = db.query(Policy).filter(Policy.customer_id == customer.id).all()

    return [format_policy(policy) for policy in policies]


# Admin: View all policies
@router.get("/")
def get_all_policies(
    db: Session = Depends(get_db), admin: User = Depends(get_current_admin)
):
    policies = db.query(Policy).order_by(Policy.created_at.desc()).all()

    return [
        {
            **format_policy(policy),
            "customer_name": policy.customer.full_name if policy.customer else None,
            "customer_email": policy.customer.email if policy.customer else None,
        }
        for policy in policies
    ]

# Admin: View all policy cancellation requests
@router.get("/cancellation-requests")
def get_all_cancellation_requests(
    status: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    query = db.query(PolicyCancellationRequest)

    if status:
        if status not in ["pending", "approved", "rejected"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid cancellation request status.",
            )

        query = query.filter(
            PolicyCancellationRequest.status == status
        )

    total = query.count()

    requests = (
        query
        .order_by(PolicyCancellationRequest.requested_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            format_cancellation_request(request)
            for request in requests
        ],
    }

# Customer/Admin: View individual policy
@router.get("/{policy_id}")
def get_policy(
    policy_id: PyUUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")

    if current_user.role == "customer":
        customer = current_user.customer

        if not customer or customer.id != policy.customer_id:
            raise HTTPException(status_code=403, detail="Access denied.")

    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

    return format_policy(policy)


# Policy cancellation Request...
@router.post("/{policy_id}/cancellation_request")
def create_cancellation_request(
    policy_id: PyUUID,
    request_data: PolicyCancellationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only customers can submit cancellation requests
    if current_user.role != "customer":
        raise HTTPException(
            status_code=403, detail="Only customer can submit cancellation requests."
        )
    customer = current_user.customer

    if not customer or customer.is_deleted:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # Check whether policy exists
    policy = db.query(Policy).filter(Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")

    # verify policy ownership
    if policy.customer_id != customer.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized for this policy cancellation.",
        )
    # only active policies can be submitted for cancellation..
    if policy.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Only active policies can be submitted for cancellation.",
        )

    # Check for an existing pending cancellation request
    existing_request = (
        db.query(PolicyCancellationRequest)
        .filter(
            PolicyCancellationRequest.policy_id == policy_id,
            PolicyCancellationRequest.status == "pending",
        )
        .first()
    )

    if existing_request:
        raise HTTPException(
            status_code=400,
            detail="A cancellation request is already pending for this policy.",
        )

    # Create cancellation request
    cancellation_request = PolicyCancellationRequest(
        policy_id=policy.id,
        customer_id=customer.id,
        reason=request_data.reason,
        additional_comments=request_data.additional_comments,
        status="pending",
    )

    db.add(cancellation_request)
    db.commit()
    db.refresh(cancellation_request)

    return format_cancellation_request(cancellation_request)

# Admin: Approve or reject a policy cancellation request
@router.patch("/cancellation-requests/{request_id}/review")
def review_cancellation_request(
    request_id: PyUUID,
    review_data: PolicyCancellationReview,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    cancellation_request = (
        db.query(PolicyCancellationRequest)
        .filter(PolicyCancellationRequest.id == request_id)
        .first()
    )

    if not cancellation_request:
        raise HTTPException(
            status_code=404,
            detail="Cancellation request not found.",
        )

    if cancellation_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="This cancellation request has already been reviewed.",
        )

    policy = (
        db.query(Policy)
        .filter(Policy.id == cancellation_request.policy_id)
        .first()
    )

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Associated policy not found.",
        )

    if review_data.status == "approved":
        if policy.status != "active":
            raise HTTPException(
                status_code=400,
                detail="Only active policies can be cancelled.",
            )

        policy.status = "cancelled"

    cancellation_request.status = review_data.status
    cancellation_request.admin_remarks = review_data.admin_remarks
    cancellation_request.reviewed_at = datetime.now(timezone.utc)
    cancellation_request.reviewed_by = admin.id

    try:
        db.commit()
        db.refresh(cancellation_request)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to review cancellation request.",
        )

    return format_cancellation_request(cancellation_request)