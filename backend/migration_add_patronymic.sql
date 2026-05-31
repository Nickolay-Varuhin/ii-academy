-- Миграция: добавить поле patronymic (отчество) в таблицу users
-- Выполнить один раз после обновления кода

ALTER TABLE users ADD COLUMN IF NOT EXISTS patronymic VARCHAR(100) DEFAULT NULL;

-- Пример заполнения тестовых данных (опционально)
-- UPDATE users SET patronymic = 'Иванович' WHERE id = 1;
