from fastapi import APIRouter, Depends

from app.config import settings
from app.core.constants import RoleEnum
from app.dependencies import require_roles
from app.routers.sla import SLA_TARGET_MINUTES
from app.schemas.settings_schema import SettingsRead, SettingsUpdate
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])

# In-memory override store for demo purposes (would be a DB-backed table in production).
_sla_overrides: dict[str, int] = {}


@router.get("", response_model=SettingsRead)
def get_settings(current_user: User = Depends(require_roles(RoleEnum.admin))):
    merged = {k.value: v for k, v in SLA_TARGET_MINUTES.items()}
    merged.update(_sla_overrides)
    return SettingsRead(
        project_name=settings.PROJECT_NAME,
        cors_origins=settings.cors_origins_list,
        sla_default_minutes=merged,
        seed_on_startup=settings.SEED_ON_STARTUP,
    )


@router.patch("", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate, current_user: User = Depends(require_roles(RoleEnum.admin))):
    if payload.sla_default_minutes:
        _sla_overrides.update(payload.sla_default_minutes)
    merged = {k.value: v for k, v in SLA_TARGET_MINUTES.items()}
    merged.update(_sla_overrides)
    return SettingsRead(
        project_name=settings.PROJECT_NAME,
        cors_origins=settings.cors_origins_list,
        sla_default_minutes=merged,
        seed_on_startup=settings.SEED_ON_STARTUP,
    )
