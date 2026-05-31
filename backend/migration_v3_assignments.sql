-- ============================================================================
-- МИГРАЦИЯ v3: добавление таблицы заданий от HR сотрудникам
-- ============================================================================
-- Выполнить на существующей БД soft_skills:
--   psql -U postgres -d soft_skills -f migration_v3_assignments.sql
-- ----------------------------------------------------------------------------

-- ENUM для статуса задания
DO $$ BEGIN
    CREATE TYPE assignment_status_enum AS ENUM ('assigned', 'in_progress', 'completed', 'overdue');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Таблица заданий (HR → Сотрудник)
CREATE TABLE IF NOT EXISTS assignments (
    id            SERIAL PRIMARY KEY,
    -- Кто назначил (HR или admin)
    assigned_by   INTEGER NOT NULL REFERENCES users(id),
    -- Кому назначено (employee)
    assigned_to   INTEGER NOT NULL REFERENCES users(id),
    -- Данные задания
    title         VARCHAR(300) NOT NULL,
    description   TEXT,
    -- Опциональная связь с сценарием симулятора или курсом
    scenario_id   INTEGER REFERENCES scenarios(id),
    course_id     INTEGER REFERENCES courses(id),
    -- Сроки
    due_date      TIMESTAMPTZ,
    priority      VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high')),
    -- Статус
    status        assignment_status_enum DEFAULT 'assigned',
    -- Метаданные
    created_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at  TIMESTAMPTZ,
    completion_note TEXT  -- заметка сотрудника при завершении
);

CREATE INDEX IF NOT EXISTS idx_assignments_to     ON assignments(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_assignments_by     ON assignments(assigned_by);
CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments(status);
