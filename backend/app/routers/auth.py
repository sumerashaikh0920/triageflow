from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import AuditAction
from app.core.exceptions import UnauthorizedError
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import AccessTokenResponse, LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserRead
from app.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.services.audit_service import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedError("This account has been deactivated")

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)
    write_audit_log(db, AuditAction.login, "user", user.id, user_id=user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserRead.model_validate(user))


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise UnauthorizedError("Invalid or expired refresh token")

    user = db.get(User, decoded.get("sub"))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    access_token = create_access_token(user.id, user.role.value)
    return AccessTokenResponse(access_token=access_token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
