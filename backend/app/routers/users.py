from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import AuditAction, RoleEnum
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.security import hash_password
from app.services.audit_service import write_audit_log

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin, RoleEnum.team_lead)),
):
    return db.query(User).order_by(User.full_name).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
):
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    write_audit_log(db, AuditAction.update, "user", user.id, user_id=current_user.id)
    return user
