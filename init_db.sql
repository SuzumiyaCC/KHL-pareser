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
CREATE TABLE team_stats (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    games_played INT NOT NULL,
    wins INT NOT NULL,
    losses INT NOT NULL,
    points INT NOT NULL,
    goal_difference INT NOT NULL,
    shots INT NOT NULL,
    shot_percentage DECIMAL(5, 2) NOT NULL,
    penalties INT NOT NULL,
    power_play_goals INT NOT NULL,
    power_play_percentage DECIMAL(5, 2) NOT NULL,
    penalty_minutes INT NOT NULL,
    men INT NOT NULL,
    penalty_killing_percentage DECIMAL(5, 2) NOT NULL,
    goals_made INT NOT NULL
);

-- Предоставляем права на таблицу пользователю khl_user
GRANT ALL PRIVILEGES ON TABLE team_stats TO khl_user;
-- Предоставляем права на последовательность
GRANT ALL PRIVILEGES ON SEQUENCE team_stats_id_seq TO khl_user;