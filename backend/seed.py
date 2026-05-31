"""
Генерирует:
- 3 админа (для демо), 3 HR, ~50 сотрудников по 5 отделам
- 6 категорий навыков, 8 навыков
- Исторические сессии диалогов за последние 6 месяцев (для трендов)
- Уровни навыков для каждого сотрудника
- НОВОЕ в v3: примеры заданий от HR для демо-сотрудников
"""
import random
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import (Role, User, SkillCategory, Skill, Scenario, Course,
                    UserSkillLevel, DialogSession, DialogMessage, DialogFeedback,
                    Assignment, AssignmentStatus,
                    RoleName, MasteryStatus, DialogStatus, SenderType,
                    ContentType)
from auth import hash_password


DEPARTMENTS = ["Продажи", "Разработка", "Маркетинг", "Поддержка", "HR"]
POSITIONS = {
    "Продажи":    ["Менеджер по продажам", "Старший менеджер", "Руководитель отдела"],
    "Разработка": ["Junior-разработчик", "Разработчик", "Senior-разработчик", "Тимлид"],
    "Маркетинг":  ["Специалист", "Маркетолог", "Руководитель направления"],
    "Поддержка":  ["Специалист поддержки", "Старший специалист"],
    "HR":         ["HR-специалист", "Рекрутер"],
}

FIRST_NAMES_M = ["Николай", "Иван", "Пётр", "Алексей", "Дмитрий", "Сергей", "Андрей", "Михаил", "Олег", "Константин"]
FIRST_NAMES_F = ["Анна", "Мария", "Елена", "Ольга", "Татьяна", "Ирина", "Наталья", "Юлия", "Екатерина", "Светлана"]
LAST_NAMES = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Новиков", "Фёдоров", "Морозов",
              "Волков", "Соколов", "Лебедев", "Козлов", "Николаев", "Орлов", "Макаров", "Андреев", "Ковалёв", "Ильин"]


async def seed_database(db: AsyncSession):
    """Заполняет БД, если она пустая."""
    result = await db.execute(select(Role))
    if result.first():
        return  # уже засеяно

    # ─── Роли ────────────────────────────────────────────
    roles = [
        Role(name=RoleName.ADMIN,    permissions=["all"]),
        Role(name=RoleName.HR,       permissions=["view_analytics", "manage_content"]),
        Role(name=RoleName.EMPLOYEE, permissions=["view_own", "dialog"]),
    ]
    db.add_all(roles)
    await db.flush()
    rm = {r.name: r.id for r in roles}

    # ─── Демо-аккаунты (фиксированные для логина) ────────
    demo_users = [
        User(email="admin@company.ru", password_hash=hash_password("admin123"),
             first_name="Администратор", last_name="Системы",
             role_id=rm[RoleName.ADMIN], department="IT", position="Сисадмин"),
        User(email="hr@company.ru", password_hash=hash_password("hr123456"),
             first_name="Мария", last_name="Иванова",
             role_id=rm[RoleName.HR], department="HR", position="HR-специалист"),
        User(email="employee@company.ru", password_hash=hash_password("emp123456"),
             first_name="Николай", last_name="Варухин",
             role_id=rm[RoleName.EMPLOYEE], department="Разработка", position="Разработчик"),
        User(email="employee2@company.ru", password_hash=hash_password("emp123456"),
             first_name="Анна", last_name="Смирнова",
             role_id=rm[RoleName.EMPLOYEE], department="Продажи", position="Менеджер по продажам"),
    ]
    db.add_all(demo_users)
    await db.flush()

    # ─── Генерируемые сотрудники ─────────────────────────
    generated_users = []
    for dep in DEPARTMENTS:
        count = {"Продажи": 14, "Разработка": 18, "Маркетинг": 8, "Поддержка": 10, "HR": 4}[dep]
        for i in range(count):
            is_male = random.random() > 0.5
            first = random.choice(FIRST_NAMES_M if is_male else FIRST_NAMES_F)
            last = random.choice(LAST_NAMES) + ("" if is_male else "а")
            email = f"{dep.lower()}.{i}@company.ru"
            generated_users.append(User(
                email=email,
                password_hash=hash_password("password123"),
                first_name=first, last_name=last,
                role_id=rm[RoleName.EMPLOYEE],
                department=dep,
                position=random.choice(POSITIONS[dep]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                last_login=datetime.utcnow() - timedelta(days=random.randint(0, 7))
                if random.random() > 0.2 else None,
            ))
    db.add_all(generated_users)
    await db.flush()

    # ─── Категории навыков ───────────────────────────────
    cats = [
        SkillCategory(name="Коммуникация", description="Навыки общения"),
        SkillCategory(name="Эмоциональный интеллект", description="Управление эмоциями"),
        SkillCategory(name="Лидерство", description="Управление командой"),
    ]
    db.add_all(cats)
    await db.flush()
    cm = {c.name: c.id for c in cats}

    # ─── Навыки ──────────────────────────────────────────
    skill_defs = [
        ("Коммуникация",      "Коммуникация",                1.2,  0.0),
        ("Эмпатия",           "Эмоциональный интеллект",     1.0, -0.2),
        ("Лидерство",         "Лидерство",                   1.5,  0.5),
        ("Командная работа",  "Коммуникация",                1.1,  0.1),
        ("Решение проблем",   "Лидерство",                   1.4,  0.8),
        ("Адаптивность",      "Эмоциональный интеллект",     1.3,  0.3),
    ]
    skills = [
        Skill(category_id=cm[cat], name=name, irt_discrimination=d, irt_difficulty=b)
        for name, cat, d, b in skill_defs
    ]
    db.add_all(skills)
    await db.flush()
    sm = {s.name: s.id for s in skills}

    # ─── Уровни навыков для всех сотрудников ─────────────
    all_employees = [u for u in demo_users if u.role_id == rm[RoleName.EMPLOYEE]] + generated_users

    def random_level():
        r = random.gauss(65, 15)
        return max(20, min(98, r))

    for emp in all_employees:
        emp_skills = random.sample(list(sm.keys()), k=random.randint(4, 6))
        for skill_name in emp_skills:
            lvl = round(random_level(), 1)
            status = (MasteryStatus.MASTERED if lvl >= 85
                      else MasteryStatus.IN_PROGRESS if lvl >= 40
                      else MasteryStatus.NOT_STARTED)
            db.add(UserSkillLevel(
                user_id=emp.id,
                skill_id=sm[skill_name],
                current_level=lvl,
                mastery_status=status,
                attempts_count=random.randint(1, 10),
                last_assessed=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
            ))

    # Для демо-сотрудника Николая — явные "красивые" уровни
    nikolay = demo_users[2]
    await db.execute(
        UserSkillLevel.__table__.delete().where(UserSkillLevel.user_id == nikolay.id)
    )
    nikolay_levels = [
        ("Коммуникация",     72.0, MasteryStatus.IN_PROGRESS, 5),
        ("Эмпатия",          75.0, MasteryStatus.IN_PROGRESS, 4),
        ("Лидерство",        60.0, MasteryStatus.IN_PROGRESS, 3),
        ("Командная работа", 88.0, MasteryStatus.MASTERED, 6),
        ("Решение проблем",  92.0, MasteryStatus.MASTERED, 7),
        ("Адаптивность",     65.0, MasteryStatus.IN_PROGRESS, 2),
    ]
    for name, lvl, status, cnt in nikolay_levels:
        db.add(UserSkillLevel(
            user_id=nikolay.id, skill_id=sm[name],
            current_level=lvl, mastery_status=status, attempts_count=cnt,
            last_assessed=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
        ))

    # ─── Сценарии ────────────────────────────────────────
    scenarios = [
        Scenario(skill_id=sm["Коммуникация"], title="Конструктивная критика",
                 description="Ваша задача — дать обратную связь коллеге, которая стабильно нарушает дедлайны спринта.",
                 difficulty=3, initial_prompt="Вы — тимлид. Анна нарушает дедлайны, вызывая задержки у других отделов.",
                 success_criteria={"min_turns": 3}, max_turns=8),
        Scenario(skill_id=sm["Лидерство"], title="Сложные переговоры с клиентом",
                 description="Клиент недоволен сроками и угрожает расторгнуть контракт.",
                 difficulty=3, initial_prompt="Крупный клиент звонит — разочарован задержкой на 2 недели.",
                 success_criteria={"min_turns": 3}, max_turns=8),
        Scenario(skill_id=sm["Эмпатия"], title="Сглаживание конфликта",
                 description="Два сотрудника не могут договориться о подходе к проекту. Вы — медиатор.",
                 difficulty=2, initial_prompt="К вам пришли двое сотрудников с разными мнениями.",
                 success_criteria={"min_turns": 2}, max_turns=10),
        Scenario(skill_id=sm["Решение проблем"], title="Презентация идеи руководству",
                 description="Убедите директора выделить бюджет на автоматизацию.",
                 difficulty=2, initial_prompt="У вас 5 минут чтобы убедить скептически настроенного директора.",
                 success_criteria={"min_turns": 3}, max_turns=8),
        Scenario(skill_id=sm["Адаптивность"], title="Стрессовое совещание",
                 description="Коллега публично критикует ваш отчёт при руководстве.",
                 difficulty=3, initial_prompt="На совещании коллега указал на ошибки в вашем квартальном отчёте.",
                 success_criteria={"min_turns": 3}, max_turns=8),
    ]
    db.add_all(scenarios)
    await db.flush()

    # ─── Курсы (больше и с описаниями) ───────────────────
    courses_data = [
        ("Основы активного слушания",
         "Учимся слышать собеседника, задавать уточняющие вопросы и корректно "
         "перефразировать позицию оппонента.",
         sm["Коммуникация"], 20, ContentType.ARTICLE, 1),
        ("Эмоциональный интеллект лидера",
         "Разбираем, как распознавать эмоции в команде и управлять собственной "
         "реакцией в сложных рабочих ситуациях.",
         sm["Эмпатия"], 45, ContentType.VIDEO, 2),
        ("Практика: Сложные переговоры",
         "Пошаговый разбор переговорных техник: позиционный торг, принципиальные "
         "переговоры по Гарвардской методике.",
         sm["Лидерство"], 30, ContentType.PRACTICE, 3),
        ("Конфликтология для руководителей",
         "Классификация конфликтов, методы разрешения и техники, которые работают "
         "в реальных командах.",
         sm["Решение проблем"], 40, ContentType.ARTICLE, 4),
        ("Командное взаимодействие: как работать в команде",
         "Как выстраивать эффективное взаимодействие с коллегами, делиться "
         "ответственностью и координировать работу.",
         sm["Командная работа"], 25, ContentType.VIDEO, 5),
        ("Адаптивность в условиях изменений",
         "Практические техники для быстрой адаптации к новым условиям и "
         "управлению изменениями в команде.",
         sm["Адаптивность"], 35, ContentType.PRACTICE, 6),
    ]
    courses = [
        Course(title=t, description=d, skill_id=s, duration_minutes=dur,
               content_type=ct, order_index=oi)
        for t, d, s, dur, ct, oi in courses_data
    ]
    db.add_all(courses)
    await db.flush()

    # ─── Задания от HR (пример для Николая и Анны) ───────
    # HR Мария выдаёт задания демо-сотрудникам
    maria = demo_users[1]
    anna = demo_users[3]

    sample_assignments = [
        Assignment(
            assigned_by=maria.id,
            assigned_to=nikolay.id,
            title="Пройти сценарий «Сглаживание конфликта»",
            description="Проработать техники медиации. До конца недели обязательно — "
                        "материал для обсуждения на встрече с командой.",
            scenario_id=scenarios[2].id,  # Сглаживание конфликта
            due_date=datetime.utcnow() + timedelta(days=3),
            priority="high",
            status=AssignmentStatus.ASSIGNED,
            created_at=datetime.utcnow() - timedelta(days=1),
        ),
        Assignment(
            assigned_by=maria.id,
            assigned_to=nikolay.id,
            title="Изучить курс по активному слушанию",
            description="Базовый навык для работы в команде. Рассчитан на 20 минут.",
            course_id=courses[0].id,
            due_date=datetime.utcnow() + timedelta(days=7),
            priority="normal",
            status=AssignmentStatus.IN_PROGRESS,
            created_at=datetime.utcnow() - timedelta(days=2),
        ),
        Assignment(
            assigned_by=maria.id,
            assigned_to=nikolay.id,
            title="Подготовиться к выступлению на квартальной встрече",
            description="Пройти сценарий «Презентация идеи руководству» для тренировки.",
            scenario_id=scenarios[3].id,
            due_date=datetime.utcnow() + timedelta(days=14),
            priority="normal",
            status=AssignmentStatus.ASSIGNED,
            created_at=datetime.utcnow() - timedelta(hours=6),
        ),
        Assignment(
            assigned_by=maria.id,
            assigned_to=anna.id,
            title="Тренинг: работа с недовольным клиентом",
            description="Пройти сценарий «Сложные переговоры с клиентом» и отработать "
                        "техники деэскалации.",
            scenario_id=scenarios[1].id,
            due_date=datetime.utcnow() + timedelta(days=5),
            priority="high",
            status=AssignmentStatus.ASSIGNED,
            created_at=datetime.utcnow() - timedelta(hours=12),
        ),
    ]
    db.add_all(sample_assignments)

    # ─── Исторические диалоги (для трендов 6 месяцев) ───
    sample_size = min(len(all_employees), 30)
    sample_users = random.sample(all_employees, sample_size)
    for emp in sample_users:
        for _ in range(random.randint(2, 8)):
            days_ago = random.randint(1, 180)
            started = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
            scenario = random.choice(scenarios)

            base = 55 + (180 - days_ago) * 0.1
            score = round(max(30, min(98, random.gauss(base, 12))), 1)

            session = DialogSession(
                user_id=emp.id, scenario_id=scenario.id,
                started_at=started,
                ended_at=started + timedelta(minutes=random.randint(5, 25)),
                status=DialogStatus.COMPLETED,
            )
            db.add(session)
            await db.flush()

            for i in range(random.randint(2, 5)):
                db.add(DialogMessage(
                    session_id=session.id,
                    sender_type=SenderType.AI if i % 2 == 0 else SenderType.USER,
                    message_text=f"Сообщение #{i}",
                    created_at=started + timedelta(minutes=i),
                ))

            db.add(DialogFeedback(
                session_id=session.id,
                overall_score=score,
                skill_scores={"Эмпатия": round(score * 0.9, 1),
                                "Аргументация": round(score * 0.85, 1)},
                ai_feedback_text="Автоматически сгенерированный отзыв.",
                recommendations="Рекомендуемые курсы подобраны.",
            ))

    await db.commit()
    print("БД заполнена тестовыми данными")
    print(f"   Всего пользователей: {len(demo_users) + len(generated_users)}")
    print(f"   Навыков: {len(skills)}")
    print(f"   Сценариев: {len(scenarios)}")
    print(f"   Курсов: {len(courses)}")
    print(f"   Заданий от HR: {len(sample_assignments)}")
    print("\n   ДЕМО-АККАУНТЫ:")
    print("   admin@company.ru    / admin123")
    print("   hr@company.ru       / hr123456")
    print("   employee@company.ru / emp123456")
