"""Common FastAPI dependencies: current user resolution and role-based access control."""
from typing import Iterable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.constants import RoleEnum
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.database import get_db
from app.models.user import User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise UnauthorizedError("Not authenticated")
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


def require_roles(*roles: Iterable[RoleEnum]):
    """Dependency factory: require_roles(RoleEnum.admin, RoleEnum.team_lead)"""
    allowed = set(roles)

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise ForbiddenError(
                f"This action requires one of the following roles: {', '.join(r.value for r in allowed)}"
            )
        return current_user

    return _checker
