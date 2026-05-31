"""Роутер: навыки и обзорная панель сотрудника."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import (User, UserSkillLevel, Skill, SkillCategory,
                    Course, Scenario, Assignment, AssignmentStatus)
from schemas import SkillLevelOut, DashboardStats
from auth import get_current_user
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api", tags=["Навыки и дашборд"])


@router.get("/skills/map", response_model=list[SkillLevelOut])
async def skill_map(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Карта навыков для радар-чарта."""
    r = await db.execute(
        select(UserSkillLevel, Skill.name, SkillCategory.name)
        .join(Skill, UserSkillLevel.skill_id == Skill.id)
        .join(SkillCategory, Skill.category_id == SkillCategory.id)
        .where(UserSkillLevel.user_id == user.id)
        .order_by(Skill.name)
    )
    return [
        SkillLevelOut(
            skill_id=lvl.skill_id,
            skill_name=sn,
            category=cn,
            current_level=lvl.current_level,
            mastery_status=(lvl.mastery_status.value if hasattr(lvl.mastery_status, "value") else lvl.mastery_status),
            attempts_count=lvl.attempts_count,
        )
        for lvl, sn, cn in r.all()
    ]


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Данные для обзорной панели сотрудника.

    Рекомендации курсов формируются ПО СЛАБЫМ НАВЫКАМ сотрудника:
    берём 3 навыка с наименьшим current_level → для каждого ищем курс →
    добавляем в рекомендации (уникально, без дубликатов).

    Если навыков нет или для них нет курсов — берём любые доступные курсы.
    Это гарантирует, что блок «Рекомендовано для вас» никогда не пустой.
    """
    summary = await AnalyticsService(db).employee_dashboard(user.id)

    # ─── Рекомендации курсов (ИСПРАВЛЕННАЯ ЛОГИКА) ──────
    recommended: list[dict] = []
    seen_course_ids: set[int] = set()

    # Шаг 1: пробуем найти курсы по слабым навыкам пользователя
    weak_skills_r = await db.execute(
        select(UserSkillLevel.skill_id, UserSkillLevel.current_level)
        .where(UserSkillLevel.user_id == user.id)
        .order_by(UserSkillLevel.current_level.asc())
        .limit(5)
    )
    weak_pairs = weak_skills_r.all()  # [(skill_id, level), ...]

    for skill_id, level in weak_pairs:
        # Ищем лучший курс для этого навыка (по level_required)
        c_r = await db.execute(
            select(Course)
            .where(Course.skill_id == skill_id, Course.id.notin_(seen_course_ids or [-1]))
            .order_by(Course.level_required.asc(), Course.duration_minutes.asc())
            .limit(1)
        )
        course = c_r.scalar_one_or_none()
        if course:
            seen_course_ids.add(course.id)
            # Процент прогресса = текущий уровень относительно целевого (85)
            progress = min(100, int(level / 85 * 100)) if level else 0
            recommended.append({
                "id": course.id,
                "title": course.title,
                "description": course.description or _generate_course_desc(course.title),
                "tags": [_tag_for_content(course.content_type)],
                "progress": progress,
                "duration": f"{course.duration_minutes} мин.",
                "skill_id": course.skill_id,
            })
            if len(recommended) >= 3:
                break

    # Шаг 2: если курсов по слабым навыкам не хватило — добираем любые
    if len(recommended) < 3:
        fallback_r = await db.execute(
            select(Course)
            .where(Course.id.notin_(seen_course_ids or [-1]))
            .order_by(Course.order_index, Course.duration_minutes)
            .limit(3 - len(recommended))
        )
        for c in fallback_r.scalars().all():
            recommended.append({
                "id": c.id,
                "title": c.title,
                "description": c.description or _generate_course_desc(c.title),
                "tags": [_tag_for_content(c.content_type)],
                "progress": 0,
                "duration": f"{c.duration_minutes} мин.",
                "skill_id": c.skill_id,
            })

    # Если БД совсем пустая — хотя бы 2 заглушки (но это только если нет курсов вообще)
    while len(recommended) < 2:
        recommended.append({
            "id": 0,
            "title": "Новые курсы появятся позже",
            "description": "Мы готовим дополнительные учебные модули.",
            "tags": ["Скоро"],
            "progress": 0,
            "duration": "—",
            "skill_id": 0,
        })

    # ─── Ближайшие задачи — реальные задания от HR ───────
    upcoming = []
    tasks_r = await db.execute(
        select(Assignment, Scenario)
        .outerjoin(Scenario, Assignment.scenario_id == Scenario.id)
        .where(
            Assignment.assigned_to == user.id,
            Assignment.status.in_([AssignmentStatus.ASSIGNED,
                                    AssignmentStatus.IN_PROGRESS])
        )
        .order_by(Assignment.due_date.asc().nullslast(),
                  Assignment.created_at.desc())
        .limit(4)
    )
    for a, sc in tasks_r.all():
        upcoming.append({
            "id": a.id,
            "title": a.title,
            "time": _format_due_date(a.due_date),
            "type": _priority_label(a.priority),
            "priority": a.priority,
        })

    # Если реальных заданий нет — заглушка (чтобы блок не был пустым)
    if not upcoming:
        upcoming = [
            {"id": 0, "title": "Заданий от HR пока нет",
             "time": "—", "type": "ПРАКТИКА", "priority": "normal"},
        ]

    return DashboardStats(
        overall_rating=summary["overall_rating"],
        completed_modules=summary["completed_modules"],
        streak_days=summary["streak_days"],
        practice_hours=summary["practice_hours"],
        skill_match_percent=summary["skill_match_percent"],
        recommended_courses=recommended,
        upcoming_tasks=upcoming,
    )


# ─── Вспомогательные функции ────────────────────────────────

def _tag_for_content(ct) -> str:
    """Человекочитаемая метка типа контента курса."""
    v = ct.value if hasattr(ct, "value") else str(ct)
    return {
        "video":    "ВИДЕО",
        "article":  "СТАТЬЯ",
        "practice": "ПРАКТИКА",
    }.get(v, "КУРС")


def _generate_course_desc(title: str) -> str:
    """Простой генератор описаний по заголовку курса — на случай
    если в БД описания не проставлены."""
    low = title.lower()
    if "слуш" in low:
        return "Учимся слышать собеседника и правильно реагировать на его позицию."
    if "эмоц" in low or "интеллект" in low:
        return "Разбираем, как управлять эмоциями в сложных рабочих ситуациях."
    if "переговор" in low:
        return "Практический разбор сложных переговоров с клиентами и руководством."
    if "конфликт" in low:
        return "Техники разрешения конфликтов в коллективе."
    return "Короткий модуль для прокачки ключевого навыка."


def _format_due_date(due) -> str:
    """Форматирует дату задания в читаемый вид ('Сегодня', 'Завтра', 'Пт, 26.04')."""
    if not due:
        return "Без срока"
    from datetime import datetime
    now = datetime.utcnow()
    due_naive = due.replace(tzinfo=None) if due.tzinfo else due
    delta = (due_naive.date() - now.date()).days
    if delta == 0:
        return f"Сегодня, {due_naive.strftime('%H:%M')}"
    if delta == 1:
        return f"Завтра, {due_naive.strftime('%H:%M')}"
    if delta < 0:
        return f"Просрочено ({due_naive.strftime('%d.%m')})"
    if delta < 7:
        days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        return f"{days_ru[due_naive.weekday()]}, {due_naive.strftime('%H:%M')}"
    return due_naive.strftime("%d.%m.%Y")


def _priority_label(priority: str) -> str:
    return {
        "high":   "СРОЧНО",
        "normal": "ЗАДАНИЕ",
        "low":    "НИЗКИЙ ПРИОРИТЕТ",
    }.get(priority, "ЗАДАНИЕ")
