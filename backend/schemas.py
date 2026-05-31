"""Pydantic-схемы для валидации API."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ─── Аутентификация ───────────────────────────────────────────
class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    department: Optional[str] = None
    position: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str


class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# ─── Диалоги ─────────────────────────────────────────────────
class ScenarioOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    difficulty: int
    skill_id: int
    max_turns: int
    is_active: bool
    # История попыток текущего пользователя
    completed: bool = False
    attempts_count: int = 0
    best_score: Optional[float] = None

    class Config:
        from_attributes = True


class StartDialogRequest(BaseModel):
    scenario_id: int


class SendMessageRequest(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=5000)


class DialogMessageOut(BaseModel):
    id: int
    sender_type: str
    message_text: str
    sentiment_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DialogSessionOut(BaseModel):
    id: int
    scenario_id: int
    scenario_title: str = ""
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: list[DialogMessageOut] = []

    class Config:
        from_attributes = True


class DialogFeedbackOut(BaseModel):
    overall_score: float
    skill_scores: dict
    ai_feedback_text: str
    recommendations: str

    class Config:
        from_attributes = True


# ─── Навыки и дашборд ────────────────────────────────────────
class SkillLevelOut(BaseModel):
    skill_id: int
    skill_name: str
    category: str
    current_level: float
    mastery_status: str
    attempts_count: int
    target_level: float = 85.0

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    overall_rating: float
    completed_modules: int
    streak_days: int
    practice_hours: float
    skill_match_percent: float
    recommended_courses: list[dict]
    upcoming_tasks: list[dict]


# ─── HR-аналитика ────────────────────────────────────────────
class DepartmentAnalytics(BaseModel):
    department: str
    employee_count: int
    completion_rate: float
    engagement_score: float
    avg_dialog_score: Optional[float] = None


class TopPerformerOut(BaseModel):
    name: str
    department: Optional[str] = None
    score: float
    skill: str


class MonthlyTrend(BaseModel):
    month: str
    value: float


class HRSummary(BaseModel):
    active_users: int
    active_users_change_pct: float
    course_completion_pct: float
    course_completion_change_pct: float
    engagement_hours_per_week: float
    engagement_change_pct: float
    critical_gaps: int


# ─── Админка ─────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    role: str = Field(..., pattern="^(admin|hr|employee)$")
    department: Optional[str] = None
    position: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(admin|hr|employee)$")
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemLogOut(BaseModel):
    id: int
    event_type: str
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    details: dict
    created_at: datetime

    class Config:
        from_attributes = True


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_dialogs: int
    total_sessions_today: int
    users_by_role: dict
    recent_logs: list[SystemLogOut]


# ─── Задания от HR сотрудникам (v3) ──────────────────────────
class AssignmentCreate(BaseModel):
    """Создание задания: HR выбирает сотрудника и описывает что сделать."""
    assigned_to: int = Field(..., description="ID сотрудника, которому выдаётся задание")
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    scenario_id: Optional[int] = None
    course_id: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: Literal["low", "normal", "high"] = "normal"


class AssignmentUpdate(BaseModel):
    """Сотрудник может обновить статус / оставить заметку."""
    status: Optional[Literal["assigned", "in_progress", "completed", "overdue"]] = None
    completion_note: Optional[str] = None


class AssignmentOut(BaseModel):
    id: int
    assigned_by: int
    assigner_name: str = ""
    assigned_to: int
    assignee_name: str = ""
    title: str
    description: Optional[str] = None
    scenario_id: Optional[int] = None
    scenario_title: Optional[str] = None
    course_id: Optional[int] = None
    course_title: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    completion_note: Optional[str] = None


class EmployeePickOut(BaseModel):
    """Вариант выбора сотрудника для формы создания задания."""
    id: int
    full_name: str
    department: Optional[str] = None
