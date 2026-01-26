from flask import Flask, render_template, request, jsonify, Response
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "clicks.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            button TEXT NOT NULL,
            click_num INTEGER NOT NULL,
            date TEXT NOT NULL,   -- YYYY-MM-DD
            time TEXT NOT NULL    -- HH:MM
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/click", methods=["POST"])
def register_click():
    data = request.get_json(force=True)
    button = data.get("button")

    if button not in ["1", "2", "3", "4"]:
        return jsonify({"error": "Botão inválido"}), 400

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time_hm = now.strftime("%H:%M")

    conn = get_db()
    cur = conn.cursor()

    # ÚLTIMO click_num DO DIA PARA ESTE BOTÃO
    cur.execute(
        "SELECT MAX(click_num) AS max_click FROM clicks WHERE date = ? AND button = ?",
        (today, button)
    )
    row = cur.fetchone()
    last_click = row["max_click"] if row and row["max_click"] is not None else 0
    click_num = last_click + 1

    cur.execute(
        "INSERT INTO clicks (button, click_num, date, time) VALUES (?, ?, ?, ?)",
        (button, click_num, today, time_hm)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "button": button,
        "click_num": click_num,
        "date": today,
        "time": time_hm
    })

@app.route("/api/export.csv")
def export_csv():
    """
    Exporta tudo para CSV (Excel abre direto).
    Colunas: id,button,click_num,date,time
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, button, click_num, date, time FROM clicks ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()

    lines = ["id,button,click_num,date,time"]
    for r in rows:
        lines.append(f'{r["id"]},{r["button"]},{r["click_num"]},{r["date"]},{r["time"]}')
    csv_data = "\n".join(lines)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=clicks.csv"}
    )

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
