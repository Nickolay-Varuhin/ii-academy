"""Роутер отчётов о достижениях.
Доступен только для ролей ADMIN и HR.
"""
from datetime import datetime
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from auth import get_current_user
from models import (
    User, RoleName,
    Assignment, AssignmentStatus,
    DialogSession, DialogStatus,
    UserSkillLevel, Skill, SkillCategory,
)
from services.report_service import UserReportData, generate_pdf, generate_docx


class EmployeePickOut(BaseModel):
    id: int
    full_name: str
    department: Optional[str] = None


router = APIRouter(prefix="/api/reports", tags=["Отчёты"])


def _require_report_access():
    async def dep(
        db: AsyncSession = Depends(get_db),
        current: User = Depends(get_current_user),
    ) -> User:
        await db.refresh(current, ["role"])
        if current.role.name not in (RoleName.ADMIN, RoleName.HR):
            raise HTTPException(status_code=403, detail="Доступ запрещён")
        return current
    return dep


@router.get("/employees", response_model=list[EmployeePickOut])
async def list_report_employees(
    search: str = Query("", description="Поиск по имени, email или отделу"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_require_report_access()),
):
    q = (
        select(User)
        .options(selectinload(User.role))
        .where(User.is_active == True)
        .order_by(User.last_name, User.first_name)
    )
    result = await db.execute(q)
    users = result.scalars().all()

    out = []
    for u in users:
        full = f"{u.last_name} {u.first_name}"
        if getattr(u, "patronymic", None):
            full += f" {u.patronymic}"
        if search:
            s = search.lower()
            if (s not in full.lower()
                    and s not in (u.email or "").lower()
                    and s not in (u.department or "").lower()):
                continue
        out.append(EmployeePickOut(id=u.id, full_name=full, department=u.department))
    return out


@router.get("/download/{user_id}")
async def download_report(
    user_id: int,
    format: str = Query("pdf", description="Формат: pdf или docx"),
    db: AsyncSession = Depends(get_db),
    current: User = Depends(_require_report_access()),
):
    fmt = format.lower()
    if fmt not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Формат должен быть pdf или docx")

    user_q = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = user_q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    assign_q = await db.execute(
        select(Assignment).where(Assignment.assigned_to == user_id)
    )
    assignments = assign_q.scalars().all()
    a_total       = len(assignments)
    a_completed   = sum(1 for a in assignments if a.status == AssignmentStatus.COMPLETED)
    a_in_progress = sum(1 for a in assignments if a.status == AssignmentStatus.IN_PROGRESS)
    a_overdue     = sum(1 for a in assignments if a.status == AssignmentStatus.OVERDUE)

    dialog_q = await db.execute(
        select(DialogSession)
        .options(selectinload(DialogSession.feedback))
        .where(DialogSession.user_id == user_id)
    )
    dialogs = dialog_q.scalars().all()
    d_total     = len(dialogs)
    d_completed = sum(1 for d in dialogs if d.status == DialogStatus.COMPLETED)
    scores = [
        d.feedback.overall_score
        for d in dialogs
        if d.feedback and d.feedback.overall_score is not None
    ]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    skills_q = await db.execute(
        select(UserSkillLevel, Skill, SkillCategory)
        .join(Skill, UserSkillLevel.skill_id == Skill.id)
        .join(SkillCategory, Skill.category_id == SkillCategory.id)
        .where(UserSkillLevel.user_id == user_id)
        .order_by(UserSkillLevel.current_level.desc())
    )
    skill_rows = skills_q.all()
    skill_levels = [
        {
            "skill_name":     s.name,
            "category":       cat.name,
            "mastery_status": (usl.mastery_status.value
                               if hasattr(usl.mastery_status, "value")
                               else str(usl.mastery_status)),
            "current_level":  usl.current_level * 100,
            "attempts_count": usl.attempts_count,
        }
        for usl, s, cat in skill_rows
    ]

    await db.refresh(current, ["role"])
    report_data = UserReportData(
        user_id=user.id,
        last_name=user.last_name,
        first_name=user.first_name,
        patronymic=getattr(user, "patronymic", None),
        email=user.email,
        department=user.department,
        position=user.position,
        role=(user.role.name.value
              if hasattr(user.role.name, "value")
              else str(user.role.name)),
        created_at=user.created_at or datetime.utcnow(),
        assignments_total=a_total,
        assignments_completed=a_completed,
        assignments_in_progress=a_in_progress,
        assignments_overdue=a_overdue,
        dialogs_total=d_total,
        dialogs_completed=d_completed,
        avg_dialog_score=avg_score,
        skill_levels=skill_levels,
        generated_at=datetime.utcnow(),
        generated_by=f"{current.first_name} {current.last_name}",
    )

    date_str      = datetime.utcnow().strftime("%Y%m%d")
    ascii_name    = f"report_user{user_id}_{date_str}"
    cyrillic_name = (
        f"report_{user.last_name}_{user.first_name}_{date_str}"
        .replace(" ", "_")
    )

    if fmt == "pdf":
        file_bytes = generate_pdf(report_data)
        media_type = "application/pdf"
        ascii_file = f"{ascii_name}.pdf"
        utf8_file  = f"{cyrillic_name}.pdf"
    else:
        file_bytes = generate_docx(report_data)
        media_type = (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )
        ascii_file = f"{ascii_name}.docx"
        utf8_file  = f"{cyrillic_name}.docx"

    disposition = (
        f'attachment; filename="{ascii_file}"; '
        f"filename*=UTF-8''{quote(utf8_file)}"
    )

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": disposition},
    )
