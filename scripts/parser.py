from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import psycopg2
from psycopg2 import sql
from datetime import datetime
import time

# Настройки для работы с браузером
options = Options()
options.add_argument("--headless")  # Запуск в headless-режиме
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--window-size=1920,1080")

# Установка ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# URL страницы с результатами КХЛ
url = 'https://www.flashscorekz.com/hockey/russia/khl/results/'
driver.get(url)
driver.implicitly_wait(10)

# Закрываем баннер cookie, если он есть
try:
    cookie_banner = driver.find_element("css selector", "#onetrust-accept-btn-handler")
    cookie_banner.click()
    print("Cookie баннер закрыт.")
    time.sleep(2)  # Небольшая задержка для обработки закрытия баннера
except NoSuchElementException:
    print("Cookie баннер не найден, продолжаем.")

# Нажимаем кнопку "Показать больше матчей" до тех пор, пока она доступна
while True:
    try:
        load_more_button = driver.find_element("css selector", "a.event__more")
        load_more_button.click()
        time.sleep(2)  # Ожидание после клика
    except NoSuchElementException:
        print("Все матчи загружены.")
        break
    except ElementClickInterceptedException:
        print("Элемент не кликабелен, попытка снова.")
        time.sleep(2)

# Подключение к PostgreSQL
try:
    conn = psycopg2.connect(
        dbname='KHL',
        user='khl_user',
        password='khl_password',
        host='db',
        port='5432'
    )
    cursor = conn.cursor()

    # Парсинг данных о матчах
    matches = driver.find_elements("css selector", "div.event__match")

    for match in matches:
        # Дата и время матча
        match_time = match.find_element("css selector", "div.event__time").text.strip()

        # Название команд
        try:
            home_team = match.find_element("css selector", "div.event__participant--home").text.strip()
            away_team = match.find_element("css selector", "div.event__participant--away").text.strip()
        except Exception as e:
            print(f"Ошибка при получении команд: {e}")
            continue

        # Счета
        scores = match.find_elements("css selector", "div.event__score")
        if len(scores) >= 2:
            try:
                home_score = int(scores[0].text.strip())
                away_score = int(scores[1].text.strip())
            except ValueError:
                print("Ошибка при преобразовании счета.")
                continue
        else:
            print("Счет не доступен.")
            continue

        # Определяем победителя
        winner = home_team if home_score > away_score else away_team

        # Форматируем дату и время
        match_datetime_str = match_time.replace("После", "").replace("OT", "").replace("бул.", "").strip()
        
        # Преобразуем строку даты и времени в datetime объект
        try:
            match_datetime = datetime.strptime(match_datetime_str, "%d.%m. %H:%M")
            match_datetime = match_datetime.replace(year=datetime.now().year)  # Установка текущего года
        except ValueError as ve:
            print(f"Ошибка преобразования даты и времени: {ve}")
            continue

        # Проверка на существование записи
        check_query = sql.SQL("""
            SELECT 1 FROM games 
            WHERE date_time = %s 
            AND home_team_id = (SELECT id FROM teams WHERE name = %s) 
            AND away_team_id = (SELECT id FROM teams WHERE name = %s) 
            AND home_score = %s 
            AND away_score = %s
        """)

        cursor.execute(check_query, (match_datetime, home_team, away_team, home_score, away_score))
        exists = cursor.fetchone()

        # Вставка данных в таблицу games, если запись не существует
        if not exists:
            insert_query = sql.SQL("""
                INSERT INTO games (date_time, home_team_id, away_team_id, home_score, away_score, winner_id)
                VALUES (
                    %s,
                    (SELECT id FROM teams WHERE name = %s),
                    (SELECT id FROM teams WHERE name = %s),
                    %s,
                    %s,
                    (SELECT id FROM teams WHERE name = %s)
                )
            """)

            try:
                cursor.execute(insert_query, (match_datetime, home_team, away_team, home_score, away_score, winner))
            except Exception as e:
                print(f"Ошибка при вставке данных: {e}")

    # Подтверждение транзакции
    conn.commit()
except Exception as e:
    print(f"Ошибка подключения к БД: {e}")
finally:
    # Закрытие соединения и браузера
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    driver.quit()
