"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.security import create_access_token, verify_password
from app.core.users import get_user
from app.schemas.auth import CurrentUser, TokenResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ============================================================
# Login
# ============================================================


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    user = get_user(form.username)
    if not user or not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user["username"], role=user["role"].value)
    return TokenResponse(access_token=token)


# ============================================================
# Current-user dependency (reused by protected endpoints)
# ============================================================


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    from jwt import PyJWTError

    from app.core.security import decode_access_token

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")  # type: ignore[assignment]
        role: str = payload.get("role")  # type: ignore[assignment]
        if username is None or role is None:
            raise credentials_error
    except PyJWTError:
        raise credentials_error
    return CurrentUser(username=username, role=role)


def require_roles(*allowed: str):
    """Dependency factory: reject users whose role is not in `allowed`."""

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role.value not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker
