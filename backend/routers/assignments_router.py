"""Роутер заданий от HR сотрудникам.

GET /api/assignments           — список заданий (для employee: свои; для hr/admin: все)
POST /api/assignments          — создать задание (hr/admin)
GET /api/assignments/{id}      — одно задание
PATCH /api/assignments/{id}    — изменить статус/заметку (employee — свои; hr — любые)
DELETE /api/assignments/{id}   — удалить (hr/admin, только свои созданные)

GET /api/assignments/employees — список сотрудников (для выпадающего списка в форме HR)
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database import get_db
from models import (User, RoleName, Assignment, AssignmentStatus,
                    Scenario, Course, Role)
from schemas import (AssignmentCreate, AssignmentUpdate, AssignmentOut,
                     EmployeePickOut)
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/assignments", tags=["Задания"])


def _to_out(a: Assignment) -> AssignmentOut:
    """Преобразует ORM-объект в схему ответа."""
    return AssignmentOut(
        id=a.id,
        assigned_by=a.assigned_by,
        assigner_name=(f"{a.assigner.first_name} {a.assigner.last_name}"
                        if a.assigner else ""),
        assigned_to=a.assigned_to,
        assignee_name=(f"{a.assignee.first_name} {a.assignee.last_name}"
                        if a.assignee else ""),
        title=a.title,
        description=a.description,
        scenario_id=a.scenario_id,
        scenario_title=a.scenario.title if a.scenario else None,
        course_id=a.course_id,
        course_title=a.course.title if a.course else None,
        due_date=a.due_date,
        priority=a.priority or "normal",
        status=(a.status.value if hasattr(a.status, "value") else a.status),
        created_at=a.created_at,
        completed_at=a.completed_at,
        completion_note=a.completion_note,
    )


@router.get("/employees", response_model=list[EmployeePickOut])
async def list_employees(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(RoleName.HR, RoleName.ADMIN)),
):
    """Список активных сотрудников для выбора в форме задания."""
    r = await db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name == RoleName.EMPLOYEE, User.is_active == True)
        .order_by(User.last_name, User.first_name)
    )
    users = r.scalars().all()
    return [
        EmployeePickOut(
            id=u.id,
            full_name=f"{u.first_name} {u.last_name}",
            department=u.department,
        )
        for u in users
    ]


@router.get("", response_model=list[AssignmentOut])
async def list_assignments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Для employee: свои задания (где assigned_to = user.id).
    Для hr/admin: задания, которые они выдали (assigned_by = user.id) +
                  все задания в целом (чтобы HR видел прогресс).
    """
    query = (
        select(Assignment)
        .options(
            selectinload(Assignment.assigner),
            selectinload(Assignment.assignee),
            selectinload(Assignment.scenario),
            selectinload(Assignment.course),
        )
        .order_by(Assignment.created_at.desc())
    )

    role_name = user.role.name
    if role_name == RoleName.EMPLOYEE:
        query = query.where(Assignment.assigned_to == user.id)
    # hr/admin видят все — без доп.фильтра

    r = await db.execute(query)
    return [_to_out(a) for a in r.scalars().all()]


@router.post("", response_model=AssignmentOut, status_code=201)
async def create_assignment(
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(RoleName.HR, RoleName.ADMIN)),
):
    """Создать задание для сотрудника. Доступно только HR/admin."""
    # Проверяем, что получатель существует и это сотрудник
    recipient = await db.get(User, data.assigned_to)
    if not recipient:
        raise HTTPException(404, "Сотрудник не найден")

    a = Assignment(
        assigned_by=user.id,
        assigned_to=data.assigned_to,
        title=data.title,
        description=data.description,
        scenario_id=data.scenario_id,
        course_id=data.course_id,
        due_date=data.due_date,
        priority=data.priority,
        status=AssignmentStatus.ASSIGNED,
    )
    db.add(a)
    await db.commit()

    # Перечитываем с зависимостями чтобы вернуть полный объект
    r = await db.execute(
        select(Assignment)
        .options(
            selectinload(Assignment.assigner),
            selectinload(Assignment.assignee),
            selectinload(Assignment.scenario),
            selectinload(Assignment.course),
        )
        .where(Assignment.id == a.id)
    )
    return _to_out(r.scalar_one())


@router.get("/{assignment_id}", response_model=AssignmentOut)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(Assignment)
        .options(
            selectinload(Assignment.assigner),
            selectinload(Assignment.assignee),
            selectinload(Assignment.scenario),
            selectinload(Assignment.course),
        )
        .where(Assignment.id == assignment_id)
    )
    a = r.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Задание не найдено")

    # Проверка доступа: либо это твоё задание, либо ты hr/admin
    role_name = user.role.name
    if role_name == RoleName.EMPLOYEE and a.assigned_to != user.id:
        raise HTTPException(403, "Нет доступа к этому заданию")

    return _to_out(a)


@router.patch("/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Employee: может менять статус своего задания и оставлять заметку.
    HR/admin: могут менять любое задание.
    """
    r = await db.execute(
        select(Assignment)
        .options(
            selectinload(Assignment.assigner),
            selectinload(Assignment.assignee),
            selectinload(Assignment.scenario),
            selectinload(Assignment.course),
        )
        .where(Assignment.id == assignment_id)
    )
    a = r.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Задание не найдено")

    role_name = user.role.name
    if role_name == RoleName.EMPLOYEE and a.assigned_to != user.id:
        raise HTTPException(403, "Нельзя менять чужое задание")

    if data.status is not None:
        try:
            new_status = AssignmentStatus(data.status)
        except ValueError:
            raise HTTPException(400, f"Недопустимый статус: {data.status}")
        a.status = new_status
        if new_status == AssignmentStatus.COMPLETED and not a.completed_at:
            a.completed_at = datetime.utcnow()
        elif new_status != AssignmentStatus.COMPLETED:
            a.completed_at = None

    if data.completion_note is not None:
        a.completion_note = data.completion_note

    await db.commit()
    await db.refresh(a)
    return _to_out(a)


@router.delete("/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(RoleName.HR, RoleName.ADMIN)),
):
    """HR/admin может удалить задание. HR — только те, что создал сам;
    admin — любые."""
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(404, "Задание не найдено")

    if user.role.name == RoleName.HR and a.assigned_by != user.id:
        raise HTTPException(403, "HR может удалять только свои задания")

    await db.delete(a)
    await db.commit()
    return None
