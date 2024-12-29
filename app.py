from flask import Flask, render_template, request, jsonify
import psycopg2
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

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
    cursor.execute("SELECT * FROM games ORDER BY date_time DESC limit 24")
    matches = cursor.fetchall()

    # Получаем список всех команд
    cursor.execute("SELECT DISTINCT home_team FROM games UNION SELECT DISTINCT away_team FROM games")
    teams = [row[0] for row in cursor.fetchall()]

    # Получаем топ команд по очкам
    cursor.execute("""
        SELECT team_name, points
        FROM summary_score
        ORDER BY points DESC
        LIMIT 30
    """)
    top_teams = cursor.fetchall()

    conn.close()

    # Рендерим главную страницу, передавая данные в шаблон
    return render_template('index.html', matches=matches, teams=teams, top_teams=top_teams)

@app.route('/compare-page')
def compare_page():
    conn = connect_to_db()
    if not conn:
        return "Ошибка подключения к базе данных", 500

    cursor = conn.cursor()

    # Получаем список всех команд
    cursor.execute("SELECT DISTINCT home_team FROM games UNION SELECT DISTINCT away_team FROM games")
    teams = [row[0] for row in cursor.fetchall()]

    conn.close()

    # Рендерим страницу сравнения команд
    return render_template('compare.html', teams=teams)

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

    # Получаем последние 10 матчей первой команды
    cursor.execute("""
        SELECT date_time, home_team, away_team, home_score, away_score, match_type 
        FROM games 
        WHERE (home_team = %s OR away_team = %s) 
        ORDER BY date_time DESC 
        LIMIT 10
    """, (team1, team1))
    team1_matches = cursor.fetchall()

    # Получаем последние 10 матчей второй команды
    cursor.execute("""
        SELECT date_time, home_team, away_team, home_score, away_score, match_type 
        FROM games 
        WHERE (home_team = %s OR away_team = %s) 
        ORDER BY date_time DESC 
        LIMIT 10
    """, (team2, team2))
    team2_matches = cursor.fetchall()

    # Получаем последние 5 матчей между выбранными командами
    cursor.execute("""
        SELECT date_time, home_team, away_team, home_score, away_score, match_type 
        FROM games 
        WHERE (home_team = %s AND away_team = %s) OR (home_team = %s AND away_team = %s)
        ORDER BY date_time DESC 
        LIMIT 5
    """, (team1, team2, team2, team1))
    head_to_head_matches = cursor.fetchall()

    # Общая статистика команд
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN (home_team = %s AND home_score > away_score) OR (away_team = %s AND away_score > home_score) THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN (home_team = %s AND home_score < away_score) OR (away_team = %s AND away_score < home_score) THEN 1 ELSE 0 END) AS losses,
            COUNT(*) AS total_matches,
            AVG(home_score) FILTER (WHERE home_team = %s) + AVG(away_score) FILTER (WHERE away_team = %s) AS avg_goals,
            SUM(CASE WHEN (home_team = %s AND home_score > away_score) THEN 1 ELSE 0 END) AS home_wins,
            SUM(CASE WHEN (away_team = %s AND away_score > home_score) THEN 1 ELSE 0 END) AS away_wins
        FROM games
        WHERE (home_team = %s OR away_team = %s)
    """, (team1, team1, team1, team1, team1, team1, team1, team1, team1, team1))
    team1_stats = cursor.fetchone()

    cursor.execute("""
        SELECT 
            SUM(CASE WHEN (home_team = %s AND home_score > away_score) OR (away_team = %s AND away_score > home_score) THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN (home_team = %s AND home_score < away_score) OR (away_team = %s AND away_score < home_score) THEN 1 ELSE 0 END) AS losses,
            COUNT(*) AS total_matches,
            AVG(home_score) FILTER (WHERE home_team = %s) + AVG(away_score) FILTER (WHERE away_team = %s) AS avg_goals,
            SUM(CASE WHEN (home_team = %s AND home_score > away_score) THEN 1 ELSE 0 END) AS home_wins,
            SUM(CASE WHEN (away_team = %s AND away_score > home_score) THEN 1 ELSE 0 END) AS away_wins
        FROM games
        WHERE (home_team = %s OR away_team = %s)
    """, (team2, team2, team2, team2, team2, team2, team2, team2, team2, team2))
    team2_stats = cursor.fetchone()

    # Статистика встреч между командами
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN (home_team = %s AND home_score > away_score) THEN 1 ELSE 0 END) + 
            SUM(CASE WHEN (away_team = %s AND away_score > home_score) THEN 1 ELSE 0 END) AS team1_wins,
            SUM(CASE WHEN (home_team = %s AND home_score > away_score) THEN 1 ELSE 0 END) + 
            SUM(CASE WHEN (away_team = %s AND away_score > home_score) THEN 1 ELSE 0 END) AS team2_wins,
            AVG(home_score + away_score) AS avg_goals
        FROM games
        WHERE (home_team = %s AND away_team = %s) OR (home_team = %s AND away_team = %s)
    """, (team1, team1, team2, team2, team1, team2, team2, team1))
    head_to_head_stats = cursor.fetchone()

    conn.close()

    # Функция для расчета серии побед
    def calculate_win_streak(matches, team):
        streak = 0
        for match in matches:
            home_team = match[1]
            away_team = match[2]
            home_score = match[3]
            away_score = match[4]
            if (home_team == team and home_score > away_score) or (away_team == team and away_score > home_score):
                streak += 1
            else:
                break
        return streak

    # Серия побед для каждой команды
    team1_streak = calculate_win_streak(team1_matches, team1)
    team2_streak = calculate_win_streak(team2_matches, team2)

    # Форматируем данные для JSON
    def format_matches(matches):
        return [{
            "date": match[0].strftime('%Y-%m-%d %H:%M'),
            "home_team": match[1],
            "away_team": match[2],
            "score": f"{match[3]} : {match[4]}",
            "match_type": match[5]
        } for match in matches]

    return jsonify({
        "team1_matches": format_matches(team1_matches),
        "team2_matches": format_matches(team2_matches),
        "head_to_head_matches": format_matches(head_to_head_matches),
        "team1_stats": {
            "wins": team1_stats[0],
            "losses": team1_stats[1],
            "total_matches": team1_stats[2],
            "avg_goals": round(team1_stats[3], 2),
            "home_wins": team1_stats[4],
            "away_wins": team1_stats[5],
            "home_win_percentage": round((team1_stats[4] / team1_stats[2]) * 100, 2) if team1_stats[2] > 0 else 0,
            "away_win_percentage": round((team1_stats[5] / team1_stats[2]) * 100, 2) if team1_stats[2] > 0 else 0,
            "win_streak": team1_streak
        },
        "team2_stats": {
            "wins": team2_stats[0],
            "losses": team2_stats[1],
            "total_matches": team2_stats[2],
            "avg_goals": round(team2_stats[3], 2),
            "home_wins": team2_stats[4],
            "away_wins": team2_stats[5],
            "home_win_percentage": round((team2_stats[4] / team2_stats[2]) * 100, 2) if team2_stats[2] > 0 else 0,
            "away_win_percentage": round((team2_stats[5] / team2_stats[2]) * 100, 2) if team2_stats[2] > 0 else 0,
            "win_streak": team2_streak
        },
        "head_to_head_stats": {
            "team1_wins": head_to_head_stats[0],
            "team2_wins": head_to_head_stats[1],
            "avg_goals": round(head_to_head_stats[2], 2)
        }
    })

@app.route('/team-trends')
def team_trends():
    team = request.args.get('team')

    if not team:
        return jsonify({"error": "Выберите команду"}), 400

    conn = connect_to_db()
    if not conn:
        return jsonify({"error": "Ошибка подключения к базе данных"}), 500

    cursor = conn.cursor()

    # Получаем последние 10 матчей команды
    cursor.execute("""
        SELECT date_time, home_team, away_team, home_score, away_score, match_type 
        FROM games 
        WHERE (home_team = %s OR away_team = %s) 
        ORDER BY date_time DESC 
        LIMIT 10
    """, (team, team))
    matches = cursor.fetchall()

    conn.close()

    # Форматируем данные для JSON
    def format_matches(matches):
        return [{
            "date": match[0].strftime('%Y-%m-%d %H:%M'),
            "home_team": match[1],
            "away_team": match[2],
            "score": f"{match[3]} : {match[4]}",
            "match_type": match[5],
            "result": "Победа" if (match[1] == team and match[3] > match[4]) or (match[2] == team and match[4] > match[3]) else "Поражение"
        } for match in matches]

    return jsonify(format_matches(matches))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)