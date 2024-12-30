import requests
from bs4 import BeautifulSoup

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

            cells = row.find_all('td')
            if len(cells) >= 5:
                # Чистим данные
                position = cells[2].text.strip().replace('Амплуа', '').strip().lower() if cells[2] else 'Не найдено'
                age = cells[4].text.strip().replace('Возраст', '').strip() if cells[4] else 'Не найдено'
            else:
                position, age = 'Не найдено', 'Не найдено'

            player_data = {
                'Имя': name,
                'Команда': team,
                'Позиция': position,
                'Лет': age
            }
            players_data.append(player_data)

    return players_data


# URL страницы
base_url = 'https://www.khl.ru/players/season/1288/'

# Общее количество страниц
total_pages = 29

# Парсинг данных
players_data = parse_all_pages(base_url, total_pages)

# Вывод данных
if players_data:
    for player in players_data:
        for key, value in player.items():
            print(f"{key}: {value}")
        print("-" * 40)
else:
    print("Данные игроков не найдены.")
