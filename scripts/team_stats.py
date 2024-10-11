import requests
from bs4 import BeautifulSoup
import psycopg2

# Установите соединение с вашей базой данных PostgreSQL
def connect_db():
    conn = psycopg2.connect(
        dbname='your_dbname',
        user='your_username',
        password='your_password',
        host='your_host',
        port='your_port'
    )
    return conn

def fetch_team_stats():
    url = "https://www.khl.ru/stat/teams/1288/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Ошибка при запросе страницы")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    teams_table = soup.find('div', id='stat_teams_table')

    if not teams_table:
        print("Таблица не найдена!")
        return

    rows = teams_table.find_all('tr')[1:]  # Пропускаем заголовок
    for row in rows:
        columns = row.find_all('td')
        if len(columns) > 0:
            team_name = columns[0].get_text(strip=True)
            games_played = columns[2].get_text(strip=True)
            wins = columns[3].get_text(strip=True)
            overtime_wins = columns[4].get_text(strip=True)
            shootout_wins = columns[5].get_text(strip=True)
            # Добавьте другие статистики по мере необходимости

            # Сохраните данные в базу данных
            save_to_db(team_name, games_played, wins, overtime_wins, shootout_wins)

def save_to_db(team_name, games_played, wins, overtime_wins, shootout_wins):
    conn = connect_db()
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO team_stats (team_name, games_played, wins, overtime_wins, shootout_wins)
    VALUES (%s, %s, %s, %s, %s);
    """
    cursor.execute(insert_query, (team_name, games_played, wins, overtime_wins, shootout_wins))
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    fetch_team_stats()
