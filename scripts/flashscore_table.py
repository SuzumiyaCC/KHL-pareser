from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import psycopg2
from psycopg2 import sql

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

# Вставка или обновление данных в таблице summary_score
def update_summary_score(conn, team_name, points):
    try:
        cursor = conn.cursor()

        # Проверка на существование записи
        check_query = sql.SQL("""
            SELECT 1 FROM summary_score 
            WHERE team_name = %s
        """)

        cursor.execute(check_query, (team_name,))
        exists = cursor.fetchone()

        if exists:
            # Обновление данных, если запись существует
            update_query = sql.SQL("""
                UPDATE summary_score 
                SET points = %s, last_updated = CURRENT_TIMESTAMP 
                WHERE team_name = %s
            """)
            cursor.execute(update_query, (points, team_name))
            print(f"Обновлены данные для команды: {team_name}, Очки: {points}")
        else:
            # Вставка данных, если запись не существует
            insert_query = sql.SQL("""
                INSERT INTO summary_score (team_name, points) 
                VALUES (%s, %s)
            """)
            cursor.execute(insert_query, (team_name, points))
            print(f"Добавлены данные для команды: {team_name}, Очки: {points}")

        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")



# URL страницы
url = 'https://www.flashscorekz.com/hockey/russia/khl/#/4MyUlev0/table/overall'

# Открываем страницу
driver.get(url)

# Ждем загрузки страницы (можно увеличить время, если данные грузятся медленно)
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

# Прокрутка страницы вниз до конца
def scroll_to_bottom():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Прокручиваем страницу вниз
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Ожидание загрузки данных
        # Получаем новую высоту страницы
        new_height = driver.execute_script("return document.body.scrollHeight")
        # Если высота не изменилась, прокрутка завершена
        if new_height == last_height:
            break
        last_height = new_height
    print("Страница прокручена до конца.")

# Прокручиваем страницу до конца
scroll_to_bottom()

# Ждем загрузки таблиц
try:
    # Увеличиваем время ожидания
    wait = WebDriverWait(driver, 20)
    
    # Ожидаем появления всех таблиц
    tables = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'ui-table__body')))
    print(f"Найдено таблиц: {len(tables)}")
    
    # Подключение к базе данных
    conn = connect_to_db()
    if not conn:
        raise Exception("Не удалось подключиться к базе данных.")
    
    # Проходим по каждой таблице
    for table_index, table_body in enumerate(tables):
        print(f"Таблица {table_index + 1}:")
        
        # Извлекаем строки таблицы
        rows = table_body.find_elements(By.CLASS_NAME, 'ui-table__row')
        print(f"Найдено строк: {len(rows)}")
        
        # Проходим по каждой строке и извлекаем данные
        for i, row in enumerate(rows):
            # Название команды
            try:
                team_name = row.find_element(By.CSS_SELECTOR, '.table__cell--participant a').get_attribute('title').strip()
                print(f"Команда {i + 1}: {team_name}")
            except NoSuchElementException:
                print(f"Команда {i + 1}: Название команды не найдено.")
                continue
            
            # Данные (числовые значения)
            try:
                # Ожидаем появления данных в строке
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'span.table__cell--value')))
                values = row.find_elements(By.CSS_SELECTOR, 'span.table__cell--value')
                values_text = [value.text.strip() for value in values]
                # Берем последнее значение (очки)
                last_value = int(values_text[-1]) if values_text else 0
                print(f"Команда: {team_name}, Очки: {last_value}")
                
                # Обновляем данные в базе данных
                update_summary_score(conn, team_name, last_value)
            except NoSuchElementException:
                print(f"Команда: {team_name}, Данные не найдены.")
except Exception as e:
    print(f"Ошибка при парсинге: {e}")
finally:
    # Закрываем соединение с базой данных
    if conn:
        conn.close()
    # Закрываем браузер
    driver.quit()