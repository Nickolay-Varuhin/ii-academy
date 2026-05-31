"""Роутер аутентификации."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database import get_db
from models import User, Role, RoleName
from schemas import UserRegister, UserLogin, TokenResponse, UserOut
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Аутентификация"])


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(User).options(selectinload(User.role)).where(User.email == data.email)
    )
    user = r.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт деактивирован")

    # Обновляем last_login (триггер в БД создаст запись в system_logs)
    user.last_login = datetime.utcnow()
    await db.commit()

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        role=user.role.name.value,
        user_id=user.id,
        full_name=f"{user.first_name} {user.last_name}",
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email уже занят")
    role_r = await db.execute(select(Role).where(Role.name == RoleName.EMPLOYEE))
    role = role_r.scalar_one_or_none()
    if not role:
        raise HTTPException(500, "Роль не найдена")
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role_id=role.id,
        department=data.department,
        position=data.position,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        role="employee",
        user_id=user.id,
        full_name=f"{user.first_name} {user.last_name}",
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut(
        id=user.id, email=user.email,
        first_name=user.first_name, last_name=user.last_name,
        role=user.role.name.value,
        department=user.department, position=user.position,
        is_active=user.is_active,
    )
