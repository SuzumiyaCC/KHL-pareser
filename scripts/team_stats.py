import time
import logging
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Настройки для логирования
logging.basicConfig(level=logging.INFO)

# Настройки для работы с браузером
options = Options()
options.add_argument("--headless")  # Запуск в headless-режиме
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# Установка ChromeDriver с помощью webdriver-manager
service = Service(ChromeDriverManager().install())

# Запуск браузера через Service
driver = webdriver.Chrome(service=service, options=options)

# URL страницы с таблицей команд КХЛ
url = 'https://www.sport-express.ru/hockey/L/khl/2024-2025/statistic/teams/'
driver.get(url)

# Ждем загрузку данных
time.sleep(5)  # Замените на WebDriverWait для более надежного ожидания

# Логирование начала парсинга
logging.info("Парсинг данных о командах...")

# Парсинг данных о командах
try:
    teams_data = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) > 0:
            team_info = {
                "team": cols[1].text.strip(),          # Название команды
                "games_played": cols[2].text.strip(),  # Игры сыграны
                "wins": cols[3].text.strip(),           # Победы
                "losses": cols[4].text.strip(),         # Поражения
                "points": cols[5].text.strip(),         # Очки
                "goal_difference": cols[6].text.strip(),  # Разница голов
                "shots": cols[7].text.strip(),          # Штрафные минуты
                "shot_percentage": cols[8].text.strip(), # Процент бросков
                "penalties": cols[9].text.strip(),      # Штрафы
                "power_play_goals": cols[10].text.strip(), # Голов в большинстве
                "power_play_percentage": cols[11].text.strip(), # Процент в большинстве
                "penalty_minutes": cols[12].text.strip(), # Штрафные минуты
                "men": cols[13].text.strip(),           # Пропущенные игроки
                "penalty_killing_percentage": cols[14].text.strip(), # Процент удалений
                "goals_made": cols[15].text.strip()     # Забитые голы
            }
            teams_data.append(team_info)
            logging.info(f"Добавлена команда: {team_info['team']}")

except Exception as e:
    logging.error(f"Произошла ошибка: {e}")

# Подключение к базе данных PostgreSQL
try:
    conn = psycopg2.connect(
        dbname='KHL',
        user='khl_user',
        password='khl_password',
        host='db',  # Используйте имя сервиса Docker
        port='5432'
    )
    
    cur = conn.cursor()

    # Вставка данных о командах в таблицу
    for team in teams_data:
        cur.execute(
            """
            INSERT INTO teams (
                name, games_played, wins, losses, points,
                goal_difference, shots, shot_percentage, penalties,
                power_play_goals, power_play_percentage, penalty_minutes,
                men, penalty_killing_percentage, goals_made
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING;
            """,
            (
                team['team'], team['games_played'], team['wins'],
                team['losses'], team['points'], team['goal_difference'],
                team['shots'], team['shot_percentage'], team['penalties'],
                team['power_play_goals'], team['power_play_percentage'],
                team['penalty_minutes'], team['men'], team['penalty_killing_percentage'],
                team['goals_made']
            )
        )
        logging.info(f"Команда {team['team']} добавлена в базу данных.")

    # Сохранение изменений и закрытие подключения
    conn.commit()
    cur.close()
    conn.close()

except Exception as db_error:
    logging.error(f"Ошибка базы данных: {db_error}")

# Закрытие браузера
driver.quit()
