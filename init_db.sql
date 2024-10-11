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
    team_name VARCHAR(100),
    games_played INT,
    wins_in_regular INT,
    wins_in_overtime INT,
    wins_in_shootout INT,
    losses_in_shootout INT,
    losses_in_overtime INT,
    losses_regular INT,
    points INT,
    games_without_goals INT,
    games_without_conceding INT,
    goals_scored INT,
    goals_conceded INT,
    penalty_time INT,
    opponent_penalty_time INT,
    puck_recoveries INT,
    pass_interceptions INT,
    puck_losses INT,
    equal_strength_time VARCHAR(10),
    avg_equal_strength_time VARCHAR(10),
    empty_net_time VARCHAR(10),
    avg_empty_net_time VARCHAR(10),
    date_updated DATE
);

-- Предоставляем права на таблицу пользователю khl_user
GRANT ALL PRIVILEGES ON TABLE team_stats TO khl_user;
-- Предоставляем права на последовательность
GRANT ALL PRIVILEGES ON SEQUENCE team_stats_id_seq TO khl_user;