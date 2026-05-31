"""Подключение к БД — PostgreSQL + SQLAlchemy async."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import DATABASE_URL, SQL_ECHO

# Движок. pool_pre_ping=True — проверка соединения перед каждым использованием
# (защита от обрывов, когда БД долго простаивала).
engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency для FastAPI — выдаёт одну сессию на запрос."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Создать таблицы, если их нет.
    Внимание: для продакшена используйте миграции (Alembic),
    а для первого старта — выполните init_db_postgres.sql вручную."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
