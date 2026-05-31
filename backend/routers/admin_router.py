"""Роутер админки. Только для роли ADMIN.
CRUD-операции над пользователями + просмотр системных логов + сводка."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database import get_db
from models import User, Role, SystemLog, DialogSession, RoleName
from schemas import (UserCreate, UserUpdate, AdminUserOut, SystemLogOut,
                      AdminStats)
from auth import hash_password, require_role

router = APIRouter(prefix="/api/admin", tags=["Администрирование"])


def _user_to_out(u: User) -> AdminUserOut:
    return AdminUserOut(
        id=u.id, email=u.email,
        first_name=u.first_name, last_name=u.last_name,
        role=u.role.name.value,
        department=u.department, position=u.position,
        is_active=u.is_active,
        created_at=u.created_at,
        last_login=u.last_login,
    )


# ─── Сводка админки ────────────────────────────────────────

@router.get("/stats", response_model=AdminStats)
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.ADMIN)),
):
    total_r = await db.execute(select(func.count(User.id)))
    active_r = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    dialogs_r = await db.execute(select(func.count(DialogSession.id)))

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_r = await db.execute(
        select(func.count(DialogSession.id)).where(DialogSession.started_at >= today_start)
    )

    # Пользователей по ролям
    by_role_r = await db.execute(
        select(Role.name, func.count(User.id))
        .join(User, User.role_id == Role.id)
        .group_by(Role.name)
    )
    by_role = {row[0].value if hasattr(row[0], "value") else row[0]: row[1]
               for row in by_role_r.all()}

    # Последние 20 логов
    logs_r = await db.execute(
        select(SystemLog, User.email)
        .join(User, SystemLog.user_id == User.id, isouter=True)
        .order_by(desc(SystemLog.created_at))
        .limit(20)
    )
    logs = [
        SystemLogOut(
            id=log.id, event_type=log.event_type,
            user_id=log.user_id, user_email=email,
            details=log.details or {},
            created_at=log.created_at,
        )
        for log, email in logs_r.all()
    ]

    return AdminStats(
        total_users=total_r.scalar() or 0,
        active_users=active_r.scalar() or 0,
        total_dialogs=dialogs_r.scalar() or 0,
        total_sessions_today=today_r.scalar() or 0,
        users_by_role=by_role,
        recent_logs=logs,
    )


# ─── CRUD пользователей ────────────────────────────────────

@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.ADMIN)),
):
    r = await db.execute(
        select(User).options(selectinload(User.role)).order_by(User.id)
    )
    return [_user_to_out(u) for u in r.scalars().all()]


@router.post("/users", response_model=AdminUserOut, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.ADMIN)),
):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email уже занят")
    role_r = await db.execute(select(Role).where(Role.name == RoleName(data.role)))
    role = role_r.scalar_one_or_none()
    if not role:
        raise HTTPException(400, "Неизвестная роль")

    u = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name, last_name=data.last_name,
        role_id=role.id,
        department=data.department, position=data.position,
    )
    db.add(u)
    await db.commit()
    # Перечитываем с ролью
    r = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == u.id)
    )
    return _user_to_out(r.scalar_one())


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.ADMIN)),
):
    r = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "Пользователь не найден")

    if data.first_name is not None: u.first_name = data.first_name
    if data.last_name is not None:  u.last_name = data.last_name
    if data.department is not None: u.department = data.department
    if data.position is not None:   u.position = data.position
    if data.is_active is not None:  u.is_active = data.is_active
    if data.role is not None:
        role_r = await db.execute(select(Role).where(Role.name == RoleName(data.role)))
        role = role_r.scalar_one_or_none()
        if not role:
            raise HTTPException(400, "Неизвестная роль")
        u.role_id = role.id

    await db.commit()
    r = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == u.id)
    )
    return _user_to_out(r.scalar_one())


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(RoleName.ADMIN)),
):
    if user_id == admin.id:
        raise HTTPException(400, "Нельзя удалить самого себя")
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "Пользователь не найден")
    # Soft-delete: деактивируем, а не удаляем (из-за FK)
    u.is_active = False
    await db.commit()


# ─── Системные логи ────────────────────────────────────────

@router.get("/logs", response_model=list[SystemLogOut])
async def list_logs(
    limit: int = 100,
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.ADMIN)),
):
    q = (select(SystemLog, User.email)
         .join(User, SystemLog.user_id == User.id, isouter=True)
         .order_by(desc(SystemLog.created_at))
         .limit(min(limit, 500)))
    if event_type:
        q = q.where(SystemLog.event_type == event_type)
    r = await db.execute(q)
    return [
        SystemLogOut(
            id=log.id, event_type=log.event_type,
            user_id=log.user_id, user_email=email,
            details=log.details or {},
            created_at=log.created_at,
        )
        for log, email in r.all()
    ]
