from flask import Flask, render_template, request, jsonify
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
            seq INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
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

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time_hm = now.strftime("%H:%M")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT MAX(seq) FROM clicks WHERE date = ?", (today,))
    last = cur.fetchone()[0]
    seq = (last or 0) + 1

    cur.execute(
        "INSERT INTO clicks (button, seq, date, time) VALUES (?, ?, ?, ?)",
        (button, seq, today, time_hm)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "button": button,
        "seq": seq,
        "date": today,
        "time": time_hm
    })

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
