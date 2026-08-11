from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import AuditAction, RoleEnum
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamRead, TeamUpdate
from app.services.audit_service import write_audit_log

router = APIRouter(prefix="/teams", tags=["teams"])


def _to_read(team: Team) -> TeamRead:
    read = TeamRead.model_validate(team)
    read.member_count = len(team.members)
    return read


@router.get("", response_model=list[TeamRead])
def list_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    teams = db.query(Team).order_by(Team.name).all()
    return [_to_read(t) for t in teams]


@router.post("", response_model=TeamRead, status_code=201)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
):
    team = Team(**payload.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    write_audit_log(db, AuditAction.create, "team", team.id, user_id=current_user.id)
    return _to_read(team)


@router.patch("/{team_id}", response_model=TeamRead)
def update_team(
    team_id: str,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
):
    team = db.get(Team, team_id)
    if not team:
        raise NotFoundError("Team not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    write_audit_log(db, AuditAction.update, "team", team.id, user_id=current_user.id)
    return _to_read(team)
