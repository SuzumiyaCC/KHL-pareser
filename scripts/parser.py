from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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

# Подключение к PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname='KHL',
            user='khl_user',
            password='khl_password',
            host='db',
            port='5432'
        )
        return conn
    except Exception as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None

# Вставка данных в таблицу games
def insert_match_data(conn, match_datetime, home_team, away_team, home_score, away_score, match_type):
    try:
        cursor = conn.cursor()

        # Проверка на существование записи
        check_query = sql.SQL("""
            SELECT 1 FROM games 
            WHERE date_time = %s 
            AND home_team = %s 
            AND away_team = %s 
            AND home_score = %s 
            AND away_score = %s
        """)

        cursor.execute(check_query, (match_datetime, home_team, away_team, home_score, away_score))
        exists = cursor.fetchone()

        # Вставка данных в таблицу games, если запись не существует
        if not exists:
            insert_query = sql.SQL("""
                INSERT INTO games (date_time, home_team, away_team, home_score, away_score, match_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """)

            try:
                cursor.execute(insert_query, (match_datetime, home_team, away_team, home_score, away_score, match_type))
                print(f"Добавлен матч: {home_team} {home_score} : {away_score} {away_team} ({match_type})")
            except Exception as e:
                print(f"Ошибка при вставке данных: {e}")
        else:
            print(f"Матч уже существует: {home_team} {home_score} : {away_score} {away_team}")

        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")

# Функция для очистки строки с временем
def clean_time_string(time_str):
    # Удаляем лишние символы (например, "После бул.")
    return time_str.split("После")[0].strip()

# Функция для преобразования строки в datetime
def parse_match_time(time_str):
    try:
        # Очищаем строку с временем
        clean_time = clean_time_string(time_str)
        # Преобразуем в datetime
        return datetime.strptime(clean_time, '%d.%m. %H:%M').replace(year=datetime.now().year)
    except ValueError as e:
        print(f"Ошибка при преобразовании времени '{time_str}': {e}")
        return None

# Функция для прокрутки страницы вниз
def scroll_page():
    # Получаем текущую высоту страницы
    previous_height = driver.execute_script("return document.body.scrollHeight")
    # Прокручиваем страницу вниз
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)  # Ожидание загрузки данных
    # Получаем новую высоту страницы
    new_height = driver.execute_script("return document.body.scrollHeight")
    # Возвращаем True, если высота изменилась (загрузились новые данные)
    return new_height != previous_height

# Функция для нажатия кнопки "Показать больше матчей"
def load_more_matches():
    try:
        # Ожидание появления кнопки
        load_more_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="live-table"]/div[1]/div/div/a'))
        )
        # Нажатие на кнопку
        load_more_button.click()
        print("Нажата кнопка 'Показать больше матчей'.")
        return True
    except Exception as e:
        print("Кнопка 'Показать больше матчей' не найдена или больше не доступна.")
        return False

# Основной код
def main():
    # Подключение к базе данных
    conn = connect_to_db()
    if not conn:
        return

    # Открытие страницы
    driver.get('https://www.flashscorekz.com/hockey/russia/khl/results/')

    # Ожидание загрузки страницы
    time.sleep(5)

    # Закрытие всплывающих баннеров
    try:
        close_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="legalAgeContainer"]/div/div/section/div/div/button[3]'))
        )
        close_button.click()
        print("Первый всплывающий баннер закрыт.")
    except Exception as e:
        print("Первый всплывающий баннер не найден или не удалось закрыть:", e)

    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
        )
        cookie_button.click()
        print("Второй всплывающий баннер закрыт.")
    except Exception as e:
        print("Второй всплывающий баннер не найден или не удалось закрыть:", e)

    # Загрузка всех матчей
    while True:
        if not load_more_matches():
            break
        if not scroll_page():
            break

    # Ожидание появления данных о матчах
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'event__match'))
        )
        print("Данные о матчах загружены.")
    except Exception as e:
        print("Данные о матчах не загрузились:", e)

    # Поиск всех матчей
    matches = driver.find_elements(By.CLASS_NAME, 'event__match')

    # Перебор и вставка данных о каждом матче
    for match in matches:
        try:
            # Время ивента
            event_time = match.find_element(By.CLASS_NAME, 'event__time').text
            
            # Преобразование времени в формат datetime
            match_datetime = parse_match_time(event_time)
            if not match_datetime:
                continue  # Пропустить матч, если время не удалось преобразовать
            
            # Названия команд
            home_team = match.find_element(By.CLASS_NAME, 'event__participant--home').text
            away_team = match.find_element(By.CLASS_NAME, 'event__participant--away').text
            
            # Счет для каждой команды
            home_score = match.find_element(By.CLASS_NAME, 'event__score--home').text
            away_score = match.find_element(By.CLASS_NAME, 'event__score--away').text
            
            # Проверка на OT или буллиты
            match_type = "Основное время"  # По умолчанию
            try:
                # Поиск отметки OT или буллитов
                ot_bul = match.find_element(By.CLASS_NAME, 'event__stage').text
                if "OT" in ot_bul:
                    match_type = "Овертайм"
                elif "бул." in ot_bul or "буллиты" in ot_bul:
                    match_type = "Буллиты"
            except:
                pass

            # Вставка данных в базу данных
            insert_match_data(conn, match_datetime, home_team, away_team, int(home_score), int(away_score), match_type)

        except Exception as e:
            print(f"Ошибка при извлечении данных матча: {e}")

    # Закрытие соединения с базой данных
    conn.close()

    # Закрытие драйвера
    driver.quit()

# Запуск основного кода
if __name__ == "__main__":
    main()