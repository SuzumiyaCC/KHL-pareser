import requests
from bs4 import BeautifulSoup
import psycopg2

# Словарь для приведения названий команд к единому виду
TEAM_MAPPING = {
    "ХК Сочи (Сочи)": "Сочи",
    "Авангард (Омск)": "Авангард",
    "Витязь (Московская область)": "Витязь",
    "Динамо М (Москва)": "Динамо Москва",
    "Динамо Мн (Минск)": "Динамо Минск",
    "ЦСКА (Москва)": "ЦСКА",
    "Трактор (Челябинск)": "Трактор",
    "Амур (Хабаровск)": "Амур",
    "Сибирь (Новосибирская область)": "Сибирь",
    "Северсталь (Череповец)": "Северсталь",
    "Куньлунь Ред Стар (Пекин)": "Куньлунь РС",
    "Ак Барс (Казань)": "Ак Барс",
    "Спартак (Москва)": "Спартак Москва",
    "Салават Юлаев (Уфа)": "Салават Юлаев",
    "Металлург (Магнитогорск)": "Металлург Магнитогорск",
    "Локомотив (Ярославль)": "Локомотив",
    "Барыс (Астана)": "Барыс",
    "Адмирал (Владивосток)": "Адмирал",
    "СКА (Санкт-Петербург)": "СКА",
    "Нефтехимик (Нижнекамск)": "Нефтехимик",
    "Автомобилист (Екатеринбург)": "Автомобилист",
    "Торпедо (Нижний Новгород)": "Торпедо",
    "Лада (Тольятти)": "Лада",
}

def normalize_team_name(team_name):
    """
    Приводит название команды к единому виду.
    Если игрок менял команды, оставляет только первую.
    """
    # Если в строке более одного закрывающего символа ")", это две команды
    if team_name.count(")") > 1:
        # Разделяем строку по закрывающей скобке и берем первую часть
        first_team = team_name.split(")")[0] + ")"
        # Приводим к единому виду
        return TEAM_MAPPING.get(first_team, first_team)
    else:
        # Если команда одна, просто возвращаем её
        return TEAM_MAPPING.get(team_name, team_name)

def parse_all_pages(base_url, total_pages):
    players_data = []

    for page in range(1, total_pages + 1):
        print(f"Парсим страницу {page} из {total_pages}...")

        # Формируем URL для текущей страницы
        url = f"{base_url}?season=1288&pager_selector=&PAGEN_1={page}"
        
        # Отправляем GET-запрос
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        })
        
        # Проверяем статус ответа
        if response.status_code != 200:
            print(f"Ошибка: не удалось загрузить страницу {page}. Код ответа: {response.status_code}")
            continue

        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем таблицу игроков
        rows = soup.find_all('tr')
        for row in rows:
            name_element = row.find('p', class_='players-table__txt players-table__txt_name roboto-condensed roboto-bold roboto-xx color-dark')
            if not name_element:
                continue

            name = name_element.text.strip()

            team_element = row.find('p', class_='players-table__txt players-table__txt_club players-table__txt_club-desk color-dark')
            team = team_element.text.strip() if team_element else 'Не найдено'

            # Нормализуем название команды
            team = normalize_team_name(team)

            cells = row.find_all('td')
            if len(cells) >= 5:
                # Чистим данные
                position = cells[2].text.strip().replace('Амплуа', '').strip().lower() if cells[2] else 'Не найдено'
                age = cells[4].text.strip().replace('Возраст', '').strip() if cells[4] else 'Не найдено'
            else:
                position, age = 'Не найдено', 'Не найдено'

            player_data = {
                'name': name,
                'team': team,
                'position': position,
                'age': age
            }
            players_data.append(player_data)

    return players_data


def save_to_postgres(players_data):
    # Установка соединения с базой данных
    conn = psycopg2.connect(
        dbname='KHL',
        user='khl_user',
        password='khl_password',
        host='db',  # Используйте имя сервиса Docker
        port='5432'
    )

    # Создание курсора
    cursor = conn.cursor()

    # SQL-запрос для вставки данных
    insert_query = """
    INSERT INTO Players (name, team, position, age)
    VALUES (%(name)s, %(team)s, %(position)s, %(age)s);
    """

    # Вставка данных для каждого игрока
    for player in players_data:
        try:
            cursor.execute(insert_query, player)
        except Exception as e:
            print(f"Ошибка при вставке данных игрока {player['name']}: {e}")

    # Фиксация изменений в базе данных
    conn.commit()

    # Закрытие курсора и соединения
    cursor.close()
    conn.close()

    print("Данные успешно сохранены в PostgreSQL.")


# URL страницы
base_url = 'https://www.khl.ru/players/season/1288/'

# Общее количество страниц
total_pages = 29

# Парсинг данных
players_data = parse_all_pages(base_url, total_pages)

# Сохранение данных в PostgreSQL
if players_data:
    save_to_postgres(players_data)
else:
    print("Данные игроков не найдены.")