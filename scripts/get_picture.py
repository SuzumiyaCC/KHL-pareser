from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests

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

# Функция для скачивания изображений
def download_image(url, team_name, folder="static/images"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Создаем имя файла на основе названия команды
            filename = f"{team_name}.png"
            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"Изображение для команды {team_name} сохранено в {filepath}")
        else:
            print(f"Не удалось скачать изображение для команды {team_name}. Статус код: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при скачивании изображения для команды {team_name}: {e}")

# Основной код
def main():
    # URL страницы с таблицей команд
    url = 'https://www.flashscorekz.com/hockey/russia/khl/#/4MyUlev0/table/overall'

    # Открываем страницу
    driver.get(url)

    # Ждем загрузки страницы
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
        
        # Ожидаем появления всех изображений
        images = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'img.participant__image')))
        print(f"Найдено изображений: {len(images)}")
        
        # Проходим по каждому изображению и сохраняем его
        for image in images:
            try:
                # Получаем URL изображения и название команды
                image_url = image.get_attribute('src')
                team_name = image.get_attribute('alt').strip()
                
                # Скачиваем и сохраняем изображение
                download_image(image_url, team_name)
            except Exception as e:
                print(f"Ошибка при обработке изображения: {e}")
    except Exception as e:
        print(f"Ошибка при парсинге изображений: {e}")
    finally:
        # Закрываем браузер
        driver.quit()

# Запуск основного кода
if __name__ == "__main__":
    main()