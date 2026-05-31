"""Роутер HR-аналитики. Доступ только для HR и ADMIN."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, RoleName
from auth import require_role
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/hr", tags=["HR-Аналитика"])


@router.get("/analytics/departments")
async def department_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.HR, RoleName.ADMIN)),
):
    return await AnalyticsService(db).department_analytics()


@router.get("/analytics/top-performers")
async def top_performers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.HR, RoleName.ADMIN)),
):
    return await AnalyticsService(db).top_performers()


@router.get("/analytics/summary")
async def summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.HR, RoleName.ADMIN)),
):
    return await AnalyticsService(db).hr_summary()


@router.get("/analytics/trend")
async def monthly_trend(
    months: int = 6,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.HR, RoleName.ADMIN)),
):
    return await AnalyticsService(db).monthly_trend(months)
