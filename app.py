from flask import Flask, render_template, request, jsonify
import psycopg2

app = Flask(__name__)

def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname='KHL',
            user='user',
            password='password',
            host='db',
            port='5432'
        )
        return conn
    except Exception as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None

@app.route('/')
def index():
    conn = connect_to_db()
    if not conn:
        return "Ошибка подключения к базе данных", 500

    cursor = conn.cursor()

    # Получаем все матчи
    cursor.execute("SELECT * FROM games ORDER BY date_time DESC")
    matches = cursor.fetchall()

    # Получаем список всех команд
    cursor.execute("SELECT DISTINCT home_team FROM games UNION SELECT DISTINCT away_team FROM games")
    teams = [row[0] for row in cursor.fetchall()]

    conn.close()

    return render_template('index.html', matches=matches, teams=teams)

@app.route('/compare')
def compare_teams():
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')

    if not team1 or not team2:
        return jsonify({"error": "Выберите обе команды!"}), 400

    conn = connect_to_db()
    if not conn:
        return jsonify({"error": "Ошибка подключения к базе данных"}), 500

    cursor = conn.cursor()

    # Получаем последние 5 матчей первой команды
    cursor.execute("""
        SELECT date_time, home_team, away_team, home_score, away_score, match_type 
        FROM games 
        WHERE (home_team = %s OR away_team = %s) 
        ORDER BY date_time DESC 
        LIMIT 5
    """, (team1, team1))
    team1_matches = cursor.fetchall()

    # Получаем последние 5 матчей второй команды
    cursor.execute("""
        SELECT date_time, home_team, away_team, home_score, away_score, match_type 
        FROM games 
        WHERE (home_team = %s OR away_team = %s) 
        ORDER BY date_time DESC 
        LIMIT 5
    """, (team2, team2))
    team2_matches = cursor.fetchall()

    conn.close()

    # Форматируем данные для JSON
    def format_matches(matches):
        return [{
            "date": match[0].strftime('%Y-%m-%d %H:%M'),
            "opponent": match[2] if match[1] == team1 else match[1],
            "score": f"{match[3]} : {match[4]}",
            "match_type": match[5]
        } for match in matches]

    return jsonify({
        "team1_matches": format_matches(team1_matches),
        "team2_matches": format_matches(team2_matches)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)