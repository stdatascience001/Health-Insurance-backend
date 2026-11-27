from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers import admin
from app.database.connection import Base, engine
from app.models import Customer, User, InsuranceApplication
from app.routers.customers import router as customer_router
from app.routers.policies import router as policy_router
from app.routers import plans
from app.routers.insurance_application import router as application_router
from app.models.policy import Policy
from app.routers import contact_inquiries
from app.routers import super_admin
from app.models.policy_cancellation import PolicyCancellationRequest

app = FastAPI(
    title="Health Care Insurance API",
    description="Backend APIs for individual health insurance",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

app.include_router(customer_router)
app.include_router(auth_router)
app.include_router(super_admin.router)
app.include_router(admin.router)
app.include_router(plans.router)
app.include_router(application_router)
app.include_router(policy_router)
app.include_router(contact_inquiries.router)

@app.get("/")
def root():
    return {"message": "Health Insurance API is running."}


@app.get("/health")
def health_check():
    return {"status": "Healthy"}
