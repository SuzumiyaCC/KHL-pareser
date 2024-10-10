-- Создаем пользователя
CREATE USER khl_user WITH PASSWORD 'khl_password';

-- Создаем базу данных, если она еще не существует
CREATE DATABASE KHL WITH OWNER khl_user;

-- Предоставляем все привилегии на базу данных пользователю khl_user
GRANT ALL PRIVILEGES ON DATABASE KHL TO khl_user;

-- Создаем таблицы и другую необходимую структуру
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL -- Добавляем уникальное ограничение на колонку name
);

-- Предоставляем права на таблицу пользователю khl_user
GRANT ALL PRIVILEGES ON TABLE teams TO khl_user;

-- Предоставляем права на последовательность
GRANT ALL PRIVILEGES ON SEQUENCE teams_id_seq TO khl_user;

-- Создание таблицы игр
CREATE TABLE games (
    id SERIAL PRIMARY KEY,            -- Уникальный идентификатор игры
    date_time TIMESTAMP NOT NULL,     -- Дата и время матча
    home_team_id INTEGER NOT NULL,    -- Внешний ключ для команды хозяев
    away_team_id INTEGER NOT NULL,     -- Внешний ключ для команды гостей
    home_score INTEGER NOT NULL,       -- Счет хозяев
    away_score INTEGER NOT NULL,       -- Счет гостей
    winner_id INTEGER NOT NULL,        -- Внешний ключ для победившей команды
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id),
    FOREIGN KEY (winner_id) REFERENCES teams(id)
);

-- Предоставляем права на таблицу пользователю khl_user
GRANT ALL PRIVILEGES ON TABLE games TO khl_user;
-- Предоставляем права на последовательность
GRANT ALL PRIVILEGES ON SEQUENCE games_id_seq TO khl_user;

-- Создание таблицы результатов
CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(id),
    home_team_score INT NOT NULL,
    away_team_score INT NOT NULL
);
