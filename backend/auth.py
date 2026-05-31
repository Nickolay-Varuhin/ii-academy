"""JWT-аутентификация + RBAC."""
from datetime import datetime, timedelta
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database import get_db
from models import User, RoleName
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["sub"] = str(to_encode["sub"])
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен не передан")

    token = auth_header[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError) as e:
        raise HTTPException(status_code=401, detail=f"Невалидный токен: {e}")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Нет sub в токене")

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


def require_role(*roles: RoleName):
    """FastAPI-зависимость для проверки ролей.
    Использование: `Depends(require_role(RoleName.HR, RoleName.ADMIN))`
    """
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role.name not in roles:
            raise HTTPException(status_code=403, detail="Доступ запрещён")
        return current_user
    return checker
