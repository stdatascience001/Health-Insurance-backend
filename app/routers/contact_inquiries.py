from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.contact_inquiries import ContactInquiry
from app.schemas.contact_inquiries import ( ContactInquiryCreate,ContactInquiryResponse,)

router = APIRouter(prefix="/contact", tags=["Contact"])

@router.post("/",response_model=ContactInquiryResponse,status_code=status.HTTP_201_CREATED)
def create_contact_inquiry(
    inquiry_data: ContactInquiryCreate,
    db: Session = Depends(get_db)
):
    inquiry = ContactInquiry(
        full_name=inquiry_data.full_name,
        email=inquiry_data.email,
        phone=inquiry_data.phone,
        subject=inquiry_data.subject,
        message=inquiry_data.message,
    )

    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    return inquiry