from flask import Flask, render_template, request, jsonify, Response
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# DB numa pasta própria (melhor para deploy)
os.makedirs(app.instance_path, exist_ok=True)
DB_NAME = os.path.join(app.instance_path, "clicks.db")

# Nomes das atividades (para export Excel e/ou UI)
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

    # devolve também o nome (podes usar no front-end se quiseres)
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
    # colunas com nomes "humanos"
    lines = ["id;atividade;botao;clique;data;hora"]

    for r in rows:
        button = r["button"]
        activity = ACTIVITY_NAMES.get(button, f"Botão {button}")

        # id;atividade;botao;clique;data;hora
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
