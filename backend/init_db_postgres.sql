-- ==========================================================================
-- Платформа «ИИ-Академия» — SQL-скрипт создания БД (PostgreSQL 14+)
-- Таблиц: 18 | Связей: 20+ | Нормальная форма: 3НФ
--
-- Выполнение:
--   1. Создайте БД:   CREATE DATABASE soft_skills;
--   2. Подключитесь:  \c soft_skills
--   3. Запустите:     \i init_db_postgres.sql
--
-- Или одной командой из терминала:
--   psql -U postgres -c "CREATE DATABASE soft_skills;"
--   psql -U postgres -d soft_skills -f init_db_postgres.sql
-- ==========================================================================

-- Удаляем типы и таблицы если существуют (для чистого пересоздания)
DROP TABLE IF EXISTS assignments, system_logs, hr_reports, user_responses, assessments,
    dialog_feedback, dialog_messages, dialog_sessions, scenarios,
    path_items, learning_paths, user_skill_level, answer_options, questions,
    courses, skills, skill_categories, user_settings, users, roles CASCADE;

DROP TYPE IF EXISTS assignment_status_enum, role_enum, mastery_enum, dialog_status_enum,
    sender_type_enum, content_type_enum, question_type_enum CASCADE;

-- ─── ENUM-типы (удобнее, чем CHECK) ────────────────────────────────────────

CREATE TYPE role_enum           AS ENUM ('admin', 'hr', 'employee');
CREATE TYPE mastery_enum        AS ENUM ('not_started', 'in_progress', 'mastered');
CREATE TYPE dialog_status_enum  AS ENUM ('active', 'completed', 'abandoned');
CREATE TYPE sender_type_enum    AS ENUM ('user', 'ai');
CREATE TYPE content_type_enum   AS ENUM ('video', 'article', 'practice');
CREATE TYPE question_type_enum  AS ENUM ('single_choice', 'multiple_choice', 'open_answer');
CREATE TYPE assignment_status_enum AS ENUM ('assigned', 'in_progress', 'completed', 'overdue');

-- ─── 1. АУТЕНТИФИКАЦИЯ И РОЛЕВАЯ МОДЕЛЬ ───────────────────────────────────

CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    name        role_enum NOT NULL UNIQUE,
    permissions JSONB     DEFAULT '[]'::jsonb
);

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    role_id       INTEGER      NOT NULL REFERENCES roles(id),
    department    VARCHAR(100),
    position      VARCHAR(100),
    avatar_url    VARCHAR(500),
    is_active     BOOLEAN      DEFAULT TRUE,
    created_at    TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMPTZ
);

CREATE TABLE user_settings (
    id                   SERIAL PRIMARY KEY,
    user_id              INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    language             VARCHAR(10) DEFAULT 'ru',
    theme                VARCHAR(20) DEFAULT 'light'
);

-- ─── 2. БАЗА ЗНАНИЙ ──────────────────────────────────────────────────────

CREATE TABLE skill_categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    icon        VARCHAR(100),
    parent_id   INTEGER REFERENCES skill_categories(id)
);

CREATE TABLE skills (
    id                 SERIAL PRIMARY KEY,
    category_id        INTEGER NOT NULL REFERENCES skill_categories(id),
    name               VARCHAR(200) NOT NULL,
    description        TEXT,
    level              INTEGER DEFAULT 1,
    irt_discrimination REAL    DEFAULT 1.0,   -- параметр a (IRT)
    irt_difficulty     REAL    DEFAULT 0.0,   -- параметр b (IRT)
    irt_guessing       REAL    DEFAULT 0.25,  -- параметр c (IRT)
    weight             REAL    DEFAULT 1.0
);

CREATE TABLE courses (
    id               SERIAL PRIMARY KEY,
    title            VARCHAR(300) NOT NULL,
    description      TEXT,
    skill_id         INTEGER NOT NULL REFERENCES skills(id),
    level_required   INTEGER DEFAULT 1,
    content_type     content_type_enum DEFAULT 'article',
    content_url      VARCHAR(500),
    duration_minutes INTEGER DEFAULT 15,
    order_index      INTEGER DEFAULT 0
);

CREATE TABLE questions (
    id                 SERIAL PRIMARY KEY,
    skill_id           INTEGER NOT NULL REFERENCES skills(id),
    text               TEXT NOT NULL,
    type               question_type_enum DEFAULT 'single_choice',
    difficulty         INTEGER DEFAULT 1,
    irt_difficulty     REAL    DEFAULT 0.0,
    irt_discrimination REAL    DEFAULT 1.0,
    time_limit_sec     INTEGER DEFAULT 60
);

CREATE TABLE answer_options (
    id           SERIAL PRIMARY KEY,
    question_id  INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    text         TEXT    NOT NULL,
    is_correct   BOOLEAN DEFAULT FALSE,
    score_weight REAL    DEFAULT 1.0,
    feedback     TEXT
);

-- ─── 3. ПОЛЬЗОВАТЕЛЬСКИЙ ПРОГРЕСС ────────────────────────────────────────

CREATE TABLE user_skill_level (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES users(id),
    skill_id         INTEGER NOT NULL REFERENCES skills(id),
    current_level    REAL    DEFAULT 0.0,
    level_confidence REAL    DEFAULT 0.5,
    last_assessed    TIMESTAMPTZ,
    attempts_count   INTEGER DEFAULT 0,
    mastery_status   mastery_enum DEFAULT 'not_started',
    UNIQUE(user_id, skill_id)
);

CREATE TABLE learning_paths (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    name         VARCHAR(300) NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_active    BOOLEAN DEFAULT TRUE,
    completed_at TIMESTAMPTZ
);

CREATE TABLE path_items (
    id             SERIAL PRIMARY KEY,
    path_id        INTEGER NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    course_id      INTEGER NOT NULL REFERENCES courses(id),
    order_position INTEGER DEFAULT 0,
    status         VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending','in_progress','completed')),
    assigned_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at   TIMESTAMPTZ,
    score          REAL
);

-- ─── 4. AI-СИМУЛЯТОР ДИАЛОГОВ ────────────────────────────────────────────

CREATE TABLE scenarios (
    id               SERIAL PRIMARY KEY,
    skill_id         INTEGER NOT NULL REFERENCES skills(id),
    title            VARCHAR(300) NOT NULL,
    description      TEXT,
    difficulty       INTEGER DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 5),
    initial_prompt   TEXT NOT NULL,
    success_criteria JSONB DEFAULT '{}'::jsonb,
    max_turns        INTEGER DEFAULT 10,
    is_active        BOOLEAN DEFAULT TRUE
);

CREATE TABLE dialog_sessions (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    scenario_id   INTEGER NOT NULL REFERENCES scenarios(id),
    started_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ended_at      TIMESTAMPTZ,
    status        dialog_status_enum DEFAULT 'active',
    ai_model_used VARCHAR(100) DEFAULT 'mock_llm_v1'
);

CREATE TABLE dialog_messages (
    id                  SERIAL PRIMARY KEY,
    session_id          INTEGER NOT NULL REFERENCES dialog_sessions(id) ON DELETE CASCADE,
    sender_type         sender_type_enum NOT NULL,
    message_text        TEXT NOT NULL,
    sentiment_score     REAL,
    intent_category     VARCHAR(100),
    ai_response_time_ms INTEGER,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dialog_feedback (
    id               SERIAL PRIMARY KEY,
    session_id       INTEGER NOT NULL UNIQUE REFERENCES dialog_sessions(id),
    overall_score    REAL,
    skill_scores     JSONB DEFAULT '{}'::jsonb,
    ai_feedback_text TEXT,
    recommendations  TEXT,
    user_rating      INTEGER CHECK(user_rating BETWEEN 1 AND 5)
);


-- ─── 4.5. ЗАДАНИЯ ОТ HR ──────────────────────────────────────────────────
-- HR/админ может создавать задания для сотрудников

CREATE TABLE assignments (
    id              SERIAL PRIMARY KEY,
    assigned_by     INTEGER NOT NULL REFERENCES users(id),
    assigned_to     INTEGER NOT NULL REFERENCES users(id),
    title           VARCHAR(300) NOT NULL,
    description     TEXT,
    scenario_id     INTEGER REFERENCES scenarios(id),
    course_id       INTEGER REFERENCES courses(id),
    due_date        TIMESTAMPTZ,
    priority        VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low','normal','high')),
    status          assignment_status_enum DEFAULT 'assigned',
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMPTZ,
    completion_note TEXT
);

-- ─── 5. АНАЛИТИКА И АДМИНИСТРИРОВАНИЕ ────────────────────────────────────

CREATE TABLE assessments (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    started_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMPTZ,
    assessment_type VARCHAR(50) DEFAULT 'adaptive',
    adaptive_used   BOOLEAN     DEFAULT TRUE
);

CREATE TABLE user_responses (
    id               SERIAL PRIMARY KEY,
    assessment_id    INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_id      INTEGER NOT NULL REFERENCES questions(id),
    selected_options JSONB   DEFAULT '[]'::jsonb,
    is_correct       BOOLEAN,
    score_obtained   REAL,
    response_time_ms INTEGER,
    irt_theta_before REAL,
    irt_theta_after  REAL
);

CREATE TABLE hr_reports (
    id            SERIAL PRIMARY KEY,
    hr_user_id    INTEGER NOT NULL REFERENCES users(id),
    report_type   VARCHAR(50),
    parameters    JSONB DEFAULT '{}'::jsonb,
    data_snapshot JSONB DEFAULT '{}'::jsonb,
    generated_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_logs (
    id         SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    user_id    INTEGER REFERENCES users(id),
    details    JSONB   DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ─── 6. ИНДЕКСЫ (для ускорения частых выборок) ──────────────────────────

CREATE INDEX idx_users_email              ON users(email);
CREATE INDEX idx_users_role               ON users(role_id);
CREATE INDEX idx_users_department         ON users(department);
CREATE INDEX idx_skills_category          ON skills(category_id);
CREATE INDEX idx_user_skill_level_user    ON user_skill_level(user_id);
CREATE INDEX idx_user_skill_level_skill   ON user_skill_level(skill_id);
CREATE INDEX idx_dialog_sessions_user     ON dialog_sessions(user_id);
CREATE INDEX idx_dialog_sessions_status   ON dialog_sessions(status);
CREATE INDEX idx_dialog_sessions_started  ON dialog_sessions(started_at DESC);
CREATE INDEX idx_dialog_messages_session  ON dialog_messages(session_id);
CREATE INDEX idx_dialog_messages_created  ON dialog_messages(created_at);
CREATE INDEX idx_assessments_user         ON assessments(user_id);
CREATE INDEX idx_system_logs_user         ON system_logs(user_id);
CREATE INDEX idx_system_logs_type         ON system_logs(event_type);
CREATE INDEX idx_system_logs_created      ON system_logs(created_at DESC);
CREATE INDEX idx_assignments_to           ON assignments(assigned_to, status);
CREATE INDEX idx_assignments_by           ON assignments(assigned_by);
CREATE INDEX idx_assignments_status       ON assignments(status);

-- ─── 7. ТРИГГЕРЫ (PL/pgSQL) ──────────────────────────────────────────────

-- Триггер: лог входа пользователя
CREATE OR REPLACE FUNCTION fn_log_last_login() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.last_login IS DISTINCT FROM OLD.last_login THEN
        INSERT INTO system_logs (event_type, user_id, details)
        VALUES ('user_login', NEW.id, jsonb_build_object('email', NEW.email));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_last_login
AFTER UPDATE OF last_login ON users
FOR EACH ROW EXECUTE FUNCTION fn_log_last_login();

-- Триггер: лог при завершении диалога
CREATE OR REPLACE FUNCTION fn_log_dialog_completed() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        INSERT INTO system_logs (event_type, user_id, details)
        VALUES ('dialog_completed', NEW.user_id,
                jsonb_build_object('session_id', NEW.id, 'scenario_id', NEW.scenario_id));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dialog_completed
AFTER UPDATE OF status ON dialog_sessions
FOR EACH ROW EXECUTE FUNCTION fn_log_dialog_completed();

-- Триггер: автоматическое создание user_settings при регистрации
CREATE OR REPLACE FUNCTION fn_create_user_settings() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_settings (user_id) VALUES (NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_create_user_settings
AFTER INSERT ON users
FOR EACH ROW EXECUTE FUNCTION fn_create_user_settings();

-- Триггер: лог изменения mastery_status
CREATE OR REPLACE FUNCTION fn_log_skill_mastery_change() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.mastery_status IS DISTINCT FROM NEW.mastery_status THEN
        INSERT INTO system_logs (event_type, user_id, details)
        VALUES ('skill_mastery_changed', NEW.user_id,
                jsonb_build_object(
                    'skill_id',  NEW.skill_id,
                    'old_status', OLD.mastery_status,
                    'new_status', NEW.mastery_status,
                    'theta',     NEW.current_level));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_skill_mastery_change
AFTER UPDATE OF mastery_status ON user_skill_level
FOR EACH ROW EXECUTE FUNCTION fn_log_skill_mastery_change();

-- ─── 8. ПРЕДСТАВЛЕНИЯ (VIEWS) ────────────────────────────────────────────

-- Представление: карта навыков пользователя
CREATE OR REPLACE VIEW v_user_skill_map AS
SELECT
    usl.user_id,
    u.first_name || ' ' || u.last_name AS full_name,
    sc.name  AS category_name,
    s.name   AS skill_name,
    s.id     AS skill_id,
    usl.current_level,
    usl.mastery_status,
    usl.attempts_count
FROM user_skill_level usl
JOIN users u             ON usl.user_id = u.id
JOIN skills s            ON usl.skill_id = s.id
JOIN skill_categories sc ON s.category_id = sc.id;

-- Представление: статистика диалогов по пользователям
CREATE OR REPLACE VIEW v_user_dialog_stats AS
SELECT
    ds.user_id,
    u.first_name || ' ' || u.last_name AS full_name,
    u.department,
    COUNT(ds.id)                                                 AS total_dialogs,
    COUNT(*) FILTER (WHERE ds.status = 'completed')              AS completed_dialogs,
    ROUND(AVG(df.overall_score)::numeric, 1)                     AS avg_score
FROM dialog_sessions ds
JOIN users u                 ON ds.user_id = u.id
LEFT JOIN dialog_feedback df ON ds.id = df.session_id
GROUP BY ds.user_id, u.first_name, u.last_name, u.department;

-- Представление: эффективность по отделам (HR)
CREATE OR REPLACE VIEW v_department_analytics AS
SELECT
    u.department,
    COUNT(DISTINCT u.id)                                         AS employee_count,
    COUNT(ds.id)                                                 AS total_dialogs,
    ROUND(AVG(df.overall_score)::numeric, 1)                     AS avg_score,
    COUNT(*) FILTER (WHERE usl.mastery_status = 'mastered')      AS mastered_skills
FROM users u
LEFT JOIN dialog_sessions ds    ON u.id = ds.user_id
LEFT JOIN dialog_feedback df    ON ds.id = df.session_id
LEFT JOIN user_skill_level usl  ON u.id = usl.user_id
WHERE u.is_active = TRUE
GROUP BY u.department;

-- Готово!
COMMENT ON DATABASE soft_skills IS 'ИИ-Академия — платформа развития Soft-Skills. v2.0 (PostgreSQL).';
