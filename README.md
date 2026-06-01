#  ИИ-Академия — Платформа развития Soft-Skills с AI-тьютором

## Оглавление

- [О проекте](#-о-проекте)
- [Стек технологий](#-стек-технологий)
- [Архитектура](#-архитектура)
- [Структура проекта](#-структура-проекта)
- [Установка и запуск](#-установка-и-запуск)
- [Тестовые аккаунты](#-тестовые-аккаунты)
- [API-эндпоинты](#-api-эндпоинты)
- [База данных](#-база-данных)
- [Скриншоты](#-скриншоты)
- [Дальнейшее развитие](#-дальнейшее-развитие)
- [Лицензия](#-лицензия)

---

##  О проекте

**ИИ-Академия** решает проблему отсутствия персонализированных инструментов для обучения soft-skills в корпоративной среде. Существующие LMS (Skillfolio, iSpring, Coursera) не используют AI для адаптации обучения под уровень конкретного сотрудника.

### Ключевые возможности

- **AI-Симулятор диалогов** — интерактивные сценарии деловых коммуникаций (переговоры, конфликты, обратная связь) с AI-тьютором
- **Адаптивное тестирование (IRT)** — автоматический подбор вопросов по Item Response Theory для точной оценки уровня навыков
- **Карта навыков** — визуализация прогресса на радар-диаграмме с 6 осями
- **HR-аналитика** — графики эффективности по отделам, таблица лучших результатов
- **RBAC** — ролевая модель доступа: сотрудник, HR-специалист, администратор
- **AI-Наставник** — персональные рекомендации по развитию

---

## Стек технологий

### Backend

| Технология | Назначение |
|---|---|
| **Python 3.11+** | Язык серверной части |
| **FastAPI** | Асинхронный REST API фреймворк |
| **Uvicorn** | ASGI-сервер |
| **SQLAlchemy 2.0** | ORM с поддержкой async (aiosqlite) |
| **SQLite** | Файловая БД для демо (PostgreSQL для прод) |
| **python-jose** | JWT-токены аутентификации |
| **bcrypt** | Хеширование паролей |
| **Pydantic** | Валидация данных |

### Frontend

| Технология | Назначение |
|---|---|
| **Angular 19** | SPA-фреймворк (standalone-компоненты) |
| **TypeScript** | Типизированный JavaScript |
| **RxJS** | Реактивные потоки данных |
| **Chart.js** | Визуализация (radar-chart, bar-chart) |
| **Zone.js** | Change detection |

### Паттерны проектирования

- **Repository** — DialogService абстрагирует доступ к данным
- **Factory Method** — AI-адаптер с возможностью замены провайдера (Mock → YandexGPT / OpenAI)
- **Observer** — автоматический пересчёт уровня навыка при завершении диалога

---

##  Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    Веб-клиент                           │
│  Angular 19 SPA (TypeScript, Chart.js, RxJS)            │
│  Компоненты: Dashboard, SkillMap, Simulator,            │
│              Analytics, Mentor, Login                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / REST API (JSON)
┌──────────────────────▼──────────────────────────────────┐
│                 Основной бэкенд                         │
│  FastAPI + Uvicorn (:8000)                              │
│  ┌────────────┐ ┌──────────┐ ┌────────────────────┐    │
│  │ Auth (JWT) │ │ Routers  │ │ Services           │    │
│  │ + RBAC     │ │ auth     │ │ dialog_service.py  │    │
│  └────────────┘ │ dialog   │ │ ai_mock.py         │    │
│                 │ skills   │ │ (Factory Method)   │    │
│                 └──────────┘ └────────────────────┘    │
└──────────────────────┬──────────────────────────────────┘
                       │ SQLAlchemy async
┌──────────────────────▼──────────────────────────────────┐
│                   База данных                           │
│  SQLite (soft_skills.db) / PostgreSQL                   │
│  18 таблиц · 4 триггера · 11 индексов · 3 views        │
└─────────────────────────────────────────────────────────┘
```

---

##  Структура проекта

```
project/
├── backend/
│   ├── main.py                 # Точка входа FastAPI, CORS, lifespan
│   ├── database.py             # Подключение SQLAlchemy async
│   ├── models.py               # 18 ORM-моделей
│   ├── schemas.py              # Pydantic-схемы валидации
│   ├── auth.py                 # JWT-аутентификация + RBAC
│   ├── seed.py                 # Seed-данные (4 пользователя, 6 навыков, 5 сценариев)
│   ├── init_db.sql             # DDL: таблицы, триггеры, индексы, views
│   ├── requirements.txt        # Python-зависимости
│   ├── routers/
│   │   ├── auth_router.py      # POST /login, /register, GET /me
│   │   ├── dialog_router.py    # Симулятор: scenarios, start, message, complete
│   │   └── skills_router.py    # Карта навыков, дашборд, HR-аналитика
│   └── services/
│       ├── ai_mock.py          # Mock AI-тьютор (Factory Method)
│       └── dialog_service.py   # Бизнес-логика диалогов
│
├── frontend/
│   ├── angular.json            # Конфигурация Angular CLI
│   ├── package.json            # npm-зависимости
│   ├── proxy.conf.json         # Прокси /api → localhost:8000
│   ├── tsconfig.json           # TypeScript конфигурация
│   └── src/
│       ├── main.ts             # Bootstrap (zone.js, provideHttpClient)
│       ├── index.html          # Корневой HTML
│       ├── styles.css           # Глобальные стили
│       └── app/
│           ├── app.component.ts
│           ├── app.routes.ts    # Маршруты с lazy loading
│           ├── guards/
│           │   └── auth.guard.ts
│           ├── services/
│           │   ├── auth.service.ts   # BehaviorSubject, login/logout
│           │   ├── api.service.ts    # HttpClient + JWT headers
│           │   └── auth.interceptor.ts
│           ├── components/
│           │   └── layout/
│           │       └── layout.component.ts  # Sidebar + Header
│           └── pages/
│               ├── login/          # Форма входа
│               ├── dashboard/      # Обзорная панель
│               ├── skill-map/      # Карта навыков (radar-chart)
│               ├── simulator/      # AI-Симулятор диалогов
│               ├── analytics/      # HR-аналитика
│               └── mentor/         # AI-Наставник
│
└── README.md
```

---

##  Установка и запуск

### Предварительные требования

- **Python** 3.10+ ([скачать](https://python.org/downloads/))
- **Node.js** 18+ ([скачать](https://nodejs.org/))
- **Git** ([скачать](https://git-scm.com/))

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/ai-academy.git
cd ai-academy/project
```

### 2. Запуск бэкенда

```bash
cd backend

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера (БД создастся автоматически)
uvicorn main:app --reload --port 8000
```

После запуска:
- API доступен на `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- БД инициализируется автоматически (seed-данные загружаются при первом старте)

### 3. Запуск фронтенда

Откройте **новый терминал**:

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev-сервера
npm start
```

После запуска:
- Приложение доступно на `http://localhost:3000`
- Прокси автоматически перенаправляет `/api/*` на `localhost:8000`

### 4. Открытие в браузере

Перейдите на `http://localhost:3000` и авторизуйтесь.

---

##  Тестовые аккаунты

| Роль | Email | Пароль |
|---|---|---|
| **Сотрудник** | `employee@company.ru` | `emp123456` |
| **HR-специалист** | `hr@company.ru` | `hr123456` |
| **Администратор** | `admin@company.ru` | `admin123` |
| Сотрудник 2 | `user2@company.ru` | `user123456` |

---

## API-эндпоинты

### Аутентификация

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/auth/login` | Авторизация (email + password → JWT) |
| `POST` | `/api/auth/register` | Регистрация нового пользователя |
| `GET` | `/api/auth/me` | Текущий пользователь (по JWT) |

### AI-Симулятор

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/dialog/scenarios` | Список доступных сценариев |
| `POST` | `/api/dialog/start` | Начать новую диалоговую сессию |
| `POST` | `/api/dialog/{id}/message` | Отправить реплику в диалог |
| `POST` | `/api/dialog/{id}/complete` | Завершить диалог и получить оценку |
| `GET` | `/api/dialog/sessions` | Список сессий пользователя |
| `GET` | `/api/dialog/{id}` | Детали конкретной сессии |

### Навыки и дашборд

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/skills/map` | Карта навыков (radar-chart data) |
| `GET` | `/api/dashboard` | Данные обзорной панели |

### HR-аналитика (только hr/admin)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/analytics/departments` | Статистика по отделам |
| `GET` | `/api/analytics/top-performers` | Лучшие результаты |

### Системные

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/` | Информация об API |
| `GET` | `/api/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## База данных

### Схема (18 таблиц)

**Основные сущности:**
- `users` — пользователи (email, пароль, ФИО, отдел, должность)
- `roles` — роли (admin, hr, employee) с JSON-правами
- `skills` — навыки с IRT-параметрами (discrimination, difficulty, guessing)
- `skill_categories` — категории навыков (иерархия)
- `scenarios` — сценарии диалогов (промпт, критерии, max_turns)

**Диалоги:**
- `dialog_sessions` — сессии (user_id, scenario_id, status, timestamps)
- `dialog_messages` — сообщения (sender_type, text, sentiment_score)
- `dialog_feedback` — обратная связь (overall_score, skill_scores, рекомендации)

**Прогресс:**
- `user_skill_level` — уровень θ по каждому навыку
- `assessments` — тестирования
- `user_responses` — ответы на вопросы (is_correct, θ_before, θ_after)

**Контент:**
- `courses`, `questions`, `answer_options`, `learning_paths`, `path_items`

**Система:**
- `system_logs` — журнал аудита
- `user_settings` — пользовательские настройки

### Дополнительные объекты

- **4 триггера** — автообновление статистики
- **11 индексов** — оптимизация запросов
- **3 views** — агрегированные отчёты

---
