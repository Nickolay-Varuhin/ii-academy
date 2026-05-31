"""
Модульные тесты для платформы «ИИ-Академия».

Запуск:
    pip install pytest httpx
    cd backend
    pytest tests/test_platform.py -v

Покрытие (17 тестов):
  Блок 1 — Хеширование паролей      (тесты 01-03)
  Блок 2 — JWT-токены                (тесты 04-05)
  Блок 3 — Модель UserReportData     (тесты 06-10)
  Блок 4 — Генерация PDF / DOCX      (тесты 11-13)
  Блок 5 — Pydantic-схемы            (тест  14)
  Блок 6 — API-эндпоинты (TestClient)(тесты 15-17)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock


# ────────────────────────────────────────────────────────────────────────
# Вспомогательная фабрика тестовых данных
# ────────────────────────────────────────────────────────────────────────

def _make_report_data(**overrides):
    from services.report_service import UserReportData
    defaults = dict(
        user_id=1,
        last_name="Иванов",
        first_name="Иван",
        patronymic="Иванович",
        email="ivan@example.com",
        department="Разработка",
        position="Инженер",
        role="employee",
        created_at=datetime(2024, 9, 1),
        assignments_total=10,
        assignments_completed=7,
        assignments_in_progress=2,
        assignments_overdue=1,
        dialogs_total=15,
        dialogs_completed=13,
        avg_dialog_score=8.45,
        skill_levels=[
            {
                "skill_name": "Python",
                "category": "Программирование",
                "mastery_status": "mastered",
                "current_level": 92,
                "attempts_count": 5,
            }
        ],
        generated_at=datetime(2026, 5, 17, 12, 0),
        generated_by="Петрова А.С.",
    )
    defaults.update(overrides)
    return UserReportData(**defaults)


# ════════════════════════════════════════════════════════════════════════
# БЛОК 1 — Хеширование паролей
# ════════════════════════════════════════════════════════════════════════

class TestPasswordHashing:

    def test_01_hash_differs_from_plain(self):
        """Хеш пароля не совпадает с оригинальным паролем."""
        from auth import hash_password
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert len(hashed) > 20

    def test_02_verify_correct_password(self):
        """verify_password возвращает True для верного пароля."""
        from auth import hash_password, verify_password
        hashed = hash_password("qwerty456")
        assert verify_password("qwerty456", hashed) is True

    def test_03_verify_wrong_password(self):
        """verify_password возвращает False для неверного пароля."""
        from auth import hash_password, verify_password
        hashed = hash_password("correct_pass")
        assert verify_password("wrong_pass", hashed) is False


# ════════════════════════════════════════════════════════════════════════
# БЛОК 2 — JWT-токены
# ════════════════════════════════════════════════════════════════════════

class TestJWT:

    def test_04_token_contains_user_id(self):
        """Токен декодируется и содержит корректный sub (user_id)."""
        from auth import create_access_token
        from config import SECRET_KEY, ALGORITHM
        from jose import jwt
        token = create_access_token({"sub": 42})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "42"

    def test_05_token_has_expiry_field(self):
        """Токен содержит поле exp (время истечения)."""
        from auth import create_access_token
        from config import SECRET_KEY, ALGORITHM
        from jose import jwt
        token = create_access_token({"sub": 1})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload


# ════════════════════════════════════════════════════════════════════════
# БЛОК 3 — Модель UserReportData
# ════════════════════════════════════════════════════════════════════════

class TestUserReportData:

    def test_06_full_name_with_patronymic(self):
        """full_name собирается из фамилии, имени и отчества."""
        d = _make_report_data()
        assert d.full_name == "Иванов Иван Иванович"

    def test_07_full_name_without_patronymic(self):
        """full_name без отчества содержит только фамилию и имя."""
        d = _make_report_data(patronymic=None)
        assert d.full_name == "Иванов Иван"

    def test_08_short_name_format(self):
        """short_name возвращает формат «Фамилия И.О.»"""
        d = _make_report_data()
        assert d.short_name == "Иванов И. И."

    def test_09_completion_rate_calculation(self):
        """completion_rate корректно вычисляет процент выполнения."""
        d = _make_report_data(assignments_total=10, assignments_completed=7)
        assert d.completion_rate == 70.0

    def test_10_completion_rate_zero_division(self):
        """completion_rate не падает при assignments_total=0."""
        d = _make_report_data(assignments_total=0, assignments_completed=0)
        assert d.completion_rate == 0.0


# ════════════════════════════════════════════════════════════════════════
# БЛОК 4 — Генерация PDF и DOCX
# ════════════════════════════════════════════════════════════════════════

class TestReportGeneration:

    def test_11_generate_pdf_returns_bytes(self):
        """generate_pdf возвращает bytes с корректным PDF-заголовком."""
        from services.report_service import generate_pdf
        pdf = generate_pdf(_make_report_data())
        assert isinstance(pdf, bytes)
        assert len(pdf) > 500
        assert pdf[:4] == b"%PDF"

    def test_12_generate_docx_returns_valid_zip(self):
        """generate_docx возвращает DOCX (ZIP-архив начинается с PK)."""
        from services.report_service import generate_docx
        docx = generate_docx(_make_report_data())
        assert isinstance(docx, bytes)
        assert len(docx) > 500
        assert docx[:2] == b"PK"

    def test_13_generate_pdf_without_skills(self):
        """PDF генерируется без ошибок при пустом списке навыков."""
        from services.report_service import generate_pdf
        pdf = generate_pdf(_make_report_data(skill_levels=[]))
        assert pdf[:4] == b"%PDF"


# ════════════════════════════════════════════════════════════════════════
# БЛОК 5 — Pydantic-схемы
# ════════════════════════════════════════════════════════════════════════

class TestSchemas:

    def test_14_register_rejects_short_password(self):
        """UserRegister бросает ValidationError при пароле короче 6 символов."""
        from schemas import UserRegister
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserRegister(
                email="valid@test.ru",
                password="abc",
                first_name="Иван",
                last_name="Иванов",
            )


# ════════════════════════════════════════════════════════════════════════
# БЛОК 6 — API-эндпоинты (FastAPI TestClient + мок БД)
# ════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def api_client():
    """
    Фикстура: FastAPI TestClient с замокированной БД.
    Подставляет пользователя-сотрудника с валидным паролем.
    """
    from fastapi.testclient import TestClient
    from main import app
    from database import get_db
    from auth import hash_password
    from models import User, RoleName

    # RoleName.EMPLOYEE уже содержит .value == "employee"
    mock_role = MagicMock()
    mock_role.name = RoleName.EMPLOYEE

    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = "emp@test.ru"
    mock_user.password_hash = hash_password("pass1234")
    mock_user.is_active = True
    mock_user.first_name = "Тест"
    mock_user.last_name = "Юзер"
    mock_user.role = mock_role
    mock_user.last_login = None

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    async def override_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestAuthEndpoints:

    def test_15_login_success_returns_token(self, api_client):
        """POST /api/auth/login с верными данными возвращает 200 и access_token."""
        resp = api_client.post(
            "/api/auth/login",
            json={"email": "emp@test.ru", "password": "pass1234"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "employee"

    def test_16_login_wrong_password_returns_401(self, api_client):
        """POST /api/auth/login с неверным паролем возвращает 401."""
        resp = api_client.post(
            "/api/auth/login",
            json={"email": "emp@test.ru", "password": "WRONG_PASSWORD"},
        )
        assert resp.status_code == 401

    def test_17_reports_endpoint_requires_auth(self, api_client):
        """GET /api/reports/employees без токена возвращает 401."""
        resp = api_client.get("/api/reports/employees")
        assert resp.status_code == 401