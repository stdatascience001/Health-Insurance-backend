from pydantic import BaseModel, EmailStr, Field, model_validator
from uuid import UUID
class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)

    #This is a Python Decorator... when validating this model, also execute the validation logic defined in this function
    @model_validator(mode='after')  
    def check_password_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self

class RegisterResponse(BaseModel):
    message: str
    customer_id: UUID


#Login schema 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"