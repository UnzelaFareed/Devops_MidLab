import os, socket, time
import psycopg2
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "notesdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )

def init_db():
    for _ in range(20):
        try:
            conn = get_conn(); cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, text TEXT)")
            conn.commit(); conn.close(); return
        except Exception:
            time.sleep(2)

PAGE = """
<h1 id="title">Unzela Fareed - DevOps Notes App</h1>
<p id="host">Served by: {{ host }}</p>
<form method="post" action="/add">
  <input name="text" id="note-input" required>
  <button id="add-btn">Add</button>
</form>
<ul id="notes">{% for n in notes %}<li>{{ n[1] }}</li>{% endfor %}</ul>
"""

@app.route("/")
def index():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM notes ORDER BY id")
    notes = cur.fetchall(); conn.close()
    return render_template_string(PAGE, notes=notes, host=socket.gethostname())

@app.route("/add", methods=["POST"])
def add():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO notes (text) VALUES (%s)", (request.form["text"],))
    conn.commit(); conn.close()
    return redirect("/")

@app.route("/health")
def health():
    return "OK", 200

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)