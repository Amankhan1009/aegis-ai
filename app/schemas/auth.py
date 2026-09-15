"""Auth request/response schemas."""

from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    USER = "USER"


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUser(BaseModel):
    """The authenticated principal, attached to request.state by the dependency."""

    username: str
    role: Role