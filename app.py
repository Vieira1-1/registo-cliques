from flask import Flask, render_template, request, jsonify, Response
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# DB numa pasta própria (melhor para deploy)
os.makedirs(app.instance_path, exist_ok=True)
DB_NAME = os.path.join(app.instance_path, "clicks.db")

ACTIVITY_NAMES = {
    "1": "Estudo",
    "2": "Xadrez",
    "3": "Leitura",
    "4": "Computadores"
}

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
            date TEXT NOT NULL,   -- YYYY-MM-DD
            time TEXT NOT NULL    -- HH:MM
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    """Dashboard simples."""
    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()

    # últimos 20 registos
    cur.execute("SELECT id, button, seq, date, time FROM clicks ORDER BY id DESC LIMIT 20")
    recent = cur.fetchall()

    # total de hoje
    cur.execute("SELECT COUNT(*) AS total FROM clicks WHERE date = ?", (today,))
    total_today = cur.fetchone()["total"]

    # totais de hoje por botão
    cur.execute("""
        SELECT button, COUNT(*) AS total
        FROM clicks
        WHERE date = ?
        GROUP BY button
        ORDER BY button ASC
    """, (today,))
    per_button_rows = cur.fetchall()

    conn.close()

    per_activity = []
    for r in per_button_rows:
        b = r["button"]
        per_activity.append({
            "button": b,
            "activity": ACTIVITY_NAMES.get(b, f"Botão {b}"),
            "total": r["total"]
        })

    # prepara recent com nomes
    recent_prepared = []
    for r in recent:
        b = r["button"]
        recent_prepared.append({
            "id": r["id"],
            "activity": ACTIVITY_NAMES.get(b, f"Botão {b}"),
            "button": b,
            "seq": r["seq"],
            "date": r["date"],
            "time": r["time"]
        })

    return render_template(
        "admin.html",
        today=today,
        total_today=total_today,
        per_activity=per_activity,
        recent=recent_prepared
    )

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

    # sequencial diário independente por botão
    cur.execute(
        "SELECT MAX(seq) AS max_seq FROM clicks WHERE date = ? AND button = ?",
        (today, button)
    )
    row = cur.fetchone()
    last_seq = row["max_seq"] if row and row["max_seq"] is not None else 0
    seq = last_seq + 1

    cur.execute(
        "INSERT INTO clicks (button, seq, date, time) VALUES (?, ?, ?, ?)",
        (button, seq, today, time_hm)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "button": button,
        "activity": ACTIVITY_NAMES.get(button, f"Botão {button}"),
        "seq": seq,
        "date": today,
        "time": time_hm
    })

@app.route("/api/export.csv")
def export_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, button, seq, date, time FROM clicks ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()

    # CSV organizado para Excel PT (separador ;)
    lines = ["id;atividade;botao;clique;data;hora"]
    for r in rows:
        button = r["button"]
        activity = ACTIVITY_NAMES.get(button, f"Botão {button}")
        lines.append(f'{r["id"]};{activity};{button};{r["seq"]};{r["date"]};{r["time"]}')

    csv_data = "\n".join(lines)

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=registos_biblioteca.csv"}
    )

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
