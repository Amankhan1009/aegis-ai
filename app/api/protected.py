"""Protected demo endpoints to prove authn/authz works (Milestone 5).

The real AI endpoint replaces /me/ai in Milestone 6 — this is only here to
verify roles before we build the orchestrator.
"""

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user, require_roles
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["protected"])


@router.get("/me")
def read_me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {"username": user.username, "role": user.role.value}


@router.get("/admin-only")
def admin_only(user: CurrentUser = Depends(require_roles("ADMIN"))) -> dict:
    return {"message": "admin access granted", "user": user.username}
