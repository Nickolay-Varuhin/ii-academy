"""ORM-модели (19 таблиц с учётом заданий от HR) — SQLAlchemy 2.0, PostgreSQL.

ВАЖНО: все Enum-колонки используют name= совпадающий с названиями типов
в init_db_postgres.sql.
"""
import enum
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, Boolean, Text,
                        DateTime, ForeignKey, Enum, UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base


# ─── ENUM-типы (должны совпадать с SQL!) ────────────────────

class RoleName(str, enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    EMPLOYEE = "employee"


class DialogStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SenderType(str, enum.Enum):
    USER = "user"
    AI = "ai"


class MasteryStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"


class ContentType(str, enum.Enum):
    VIDEO = "video"
    ARTICLE = "article"
    PRACTICE = "practice"


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ANSWER = "open_answer"


class AssignmentStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


def _values(x):
    return [e.value for e in x]


# ─── Аутентификация ─────────────────────────────────────────
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(Enum(RoleName, name="role_enum", values_callable=_values,
                        create_type=False), unique=True, nullable=False)
    permissions = Column(JSONB, default=list)
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    department = Column(String(100))
    position = Column(String(100))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))
    role = relationship("Role", back_populates="users")
    skill_levels = relationship("UserSkillLevel", back_populates="user")
    dialog_sessions = relationship("DialogSession", back_populates="user")


class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    notification_enabled = Column(Boolean, default=True)
    language = Column(String(10), default="ru")
    theme = Column(String(20), default="light")


# ─── База знаний ────────────────────────────────────────────
class SkillCategory(Base):
    __tablename__ = "skill_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    parent_id = Column(Integer, ForeignKey("skill_categories.id"))
    skills = relationship("Skill", back_populates="category")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("skill_categories.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    level = Column(Integer, default=1)
    irt_discrimination = Column(Float, default=1.0)
    irt_difficulty = Column(Float, default=0.0)
    irt_guessing = Column(Float, default=0.25)
    weight = Column(Float, default=1.0)
    category = relationship("SkillCategory", back_populates="skills")
    scenarios = relationship("Scenario", back_populates="skill")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    level_required = Column(Integer, default=1)
    content_type = Column(Enum(ContentType, name="content_type_enum",
                                values_callable=_values, create_type=False),
                           default=ContentType.ARTICLE)
    content_url = Column(String(500))
    duration_minutes = Column(Integer, default=15)
    order_index = Column(Integer, default=0)


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    text = Column(Text, nullable=False)
    type = Column(Enum(QuestionType, name="question_type_enum",
                        values_callable=_values, create_type=False),
                  default=QuestionType.SINGLE_CHOICE)
    difficulty = Column(Integer, default=1)
    irt_difficulty = Column(Float, default=0.0)
    irt_discrimination = Column(Float, default=1.0)
    time_limit_sec = Column(Integer, default=60)
    options = relationship("AnswerOption", back_populates="question")


class AnswerOption(Base):
    __tablename__ = "answer_options"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    score_weight = Column(Float, default=1.0)
    feedback = Column(Text)
    question = relationship("Question", back_populates="options")


# ─── Прогресс ───────────────────────────────────────────────
class UserSkillLevel(Base):
    __tablename__ = "user_skill_level"
    __table_args__ = (UniqueConstraint("user_id", "skill_id"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    current_level = Column(Float, default=0.0)
    level_confidence = Column(Float, default=0.5)
    last_assessed = Column(DateTime(timezone=True))
    attempts_count = Column(Integer, default=0)
    mastery_status = Column(Enum(MasteryStatus, name="mastery_enum",
                                  values_callable=_values, create_type=False),
                            default=MasteryStatus.NOT_STARTED)
    user = relationship("User", back_populates="skill_levels")


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(300), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    completed_at = Column(DateTime(timezone=True))
    items = relationship("PathItem", back_populates="path")


class PathItem(Base):
    __tablename__ = "path_items"
    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    order_position = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    score = Column(Float)
    path = relationship("LearningPath", back_populates="items")


# ─── AI-симулятор ───────────────────────────────────────────
class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    difficulty = Column(Integer, default=1)
    initial_prompt = Column(Text, nullable=False)
    success_criteria = Column(JSONB, default=dict)
    max_turns = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    skill = relationship("Skill", back_populates="scenarios")
    sessions = relationship("DialogSession", back_populates="scenario")


class DialogSession(Base):
    __tablename__ = "dialog_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True))
    status = Column(Enum(DialogStatus, name="dialog_status_enum",
                          values_callable=_values, create_type=False),
                    default=DialogStatus.ACTIVE)
    ai_model_used = Column(String(100), default="mock_llm_v1")
    user = relationship("User", back_populates="dialog_sessions")
    scenario = relationship("Scenario", back_populates="sessions")
    messages = relationship("DialogMessage", back_populates="session",
                             order_by="DialogMessage.created_at",
                             cascade="all, delete-orphan")
    feedback = relationship("DialogFeedback", back_populates="session", uselist=False)


class DialogMessage(Base):
    __tablename__ = "dialog_messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("dialog_sessions.id", ondelete="CASCADE"))
    sender_type = Column(Enum(SenderType, name="sender_type_enum",
                               values_callable=_values, create_type=False),
                         nullable=False)
    message_text = Column(Text, nullable=False)
    sentiment_score = Column(Float)
    intent_category = Column(String(100))
    ai_response_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    session = relationship("DialogSession", back_populates="messages")


class DialogFeedback(Base):
    __tablename__ = "dialog_feedback"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("dialog_sessions.id"), unique=True)
    overall_score = Column(Float)
    skill_scores = Column(JSONB, default=dict)
    ai_feedback_text = Column(Text)
    recommendations = Column(Text)
    user_rating = Column(Integer)
    session = relationship("DialogSession", back_populates="feedback")


# ─── Аналитика ──────────────────────────────────────────────
class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    assessment_type = Column(String(50), default="adaptive")
    adaptive_used = Column(Boolean, default=True)


class UserResponse(Base):
    __tablename__ = "user_responses"
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_options = Column(JSONB, default=list)
    is_correct = Column(Boolean)
    score_obtained = Column(Float)
    response_time_ms = Column(Integer)
    irt_theta_before = Column(Float)
    irt_theta_after = Column(Float)


class HRReport(Base):
    __tablename__ = "hr_reports"
    id = Column(Integer, primary_key=True)
    hr_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(String(50))
    parameters = Column(JSONB, default=dict)
    data_snapshot = Column(JSONB, default=dict)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True)
    event_type = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ─── Задания от HR сотрудникам (НОВОЕ в v3) ─────────────────
class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    due_date = Column(DateTime(timezone=True))
    priority = Column(String(20), default="normal")
    status = Column(Enum(AssignmentStatus, name="assignment_status_enum",
                          values_callable=_values, create_type=False),
                    default=AssignmentStatus.ASSIGNED)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    completion_note = Column(Text)

    assigner = relationship("User", foreign_keys=[assigned_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    scenario = relationship("Scenario", foreign_keys=[scenario_id])
    course = relationship("Course", foreign_keys=[course_id])
