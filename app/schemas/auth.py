# schemas/auth.py
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserIn(BaseModel):
    """User info response"""

    id: UUID
    email: EmailStr


class UserSign(BaseModel):
    """User sign up/sign in request"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str
    token_type: str = "bearer"


class SignUpResponse(BaseModel):
    """Sign up response"""

    message: str


class SignInResponse(BaseModel):
    """Sign in response"""

    message: str
    data: TokenResponse
