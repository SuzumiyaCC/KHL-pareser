import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Настройки для работы с браузером
options = Options()
options.add_argument("--headless")  # Запуск в headless-режиме
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--window-size=1920,1080")

# Установка ChromeDriver с помощью webdriver-manager
service = Service(ChromeDriverManager().install())

# Запуск браузера через Service
driver = webdriver.Chrome(service=service, options=options)

# URL страницы с таблицей команд КХЛ
url = 'https://www.flashscorekz.com/hockey/russia/khl/#/4MyUlev0/table/overall'
driver.get(url)

# Ждем загрузку данных
driver.implicitly_wait(10)

# Парсинг данных о командах
teams = driver.find_elements("css selector", "div.tableCellParticipant")

# Подключение к базе данных PostgreSQL
# Измените хост на имя сервиса Docker
conn = psycopg2.connect(
    dbname='KHL',
    user='khl_user',
    password='khl_password',
    host='db',  # Используйте имя сервиса Docker
    port='5432'
)

cur = conn.cursor()

# Вставка команд в таблицу
for team in teams:
    team_name = team.find_element("css selector", "a.tableCellParticipant__name").text

    # Выполнение SQL-запроса для вставки команды
    cur.execute("INSERT INTO teams (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (team_name,))
    print(f"Команда: {team_name} добавлена в базу данных.")

# Сохранение изменений и закрытие подключения
conn.commit()
cur.close()
conn.close()

# Закрытие браузера
driver.quit()
