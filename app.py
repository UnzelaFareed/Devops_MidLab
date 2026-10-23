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
            cur.execute("ALTER TABLE notes ADD COLUMN IF NOT EXISTS done BOOLEAN DEFAULT FALSE")
            cur.execute("ALTER TABLE notes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()")
            conn.commit(); conn.close(); return
        except Exception:
            time.sleep(2)

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Study Planner</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: 'Segoe UI', Arial, sans-serif; background: #f5f7fb; color: #1f2937; }
  header { background: #fff; border-bottom: 1px solid #e5e7eb; padding: 16px 32px;
           display: flex; align-items: center; gap: 12px; }
  .logo { width: 34px; height: 34px; border-radius: 10px; color: #fff; font-weight: bold;
          background: linear-gradient(135deg, #3b82f6, #8b5cf6);
          display: flex; align-items: center; justify-content: center; }
  header span { font-weight: 700; color: #3b82f6; font-size: 20px; }
  main { max-width: 720px; margin: 40px auto; padding: 0 16px; }
  h1 { font-size: 34px; margin: 0 0 6px; }
  .sub { color: #9ca3af; margin: 0 0 22px; }
  .stats { display: flex; gap: 22px; margin-bottom: 22px; font-size: 14px; color: #6b7280; }
  .stats b { color: #111827; margin-left: 4px; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .add { display: flex; gap: 12px; margin-bottom: 18px; }
  .add input { flex: 1; padding: 13px 16px; border: 1px solid #e5e7eb; border-radius: 12px;
               font-size: 15px; outline: none; background: #fff; }
  .add input:focus { border-color: #3b82f6; }
  .add button { padding: 0 24px; border: 0; border-radius: 12px; color: #fff; font-weight: 600;
                font-size: 15px; cursor: pointer;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
  .tabs { display: flex; gap: 8px; margin-bottom: 18px; }
  .tabs a { padding: 6px 16px; border: 1px solid #e5e7eb; border-radius: 20px; background: #fff;
            color: #6b7280; text-decoration: none; font-size: 14px; }
  .tabs a.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
  ul { list-style: none; padding: 0; margin: 0; }
  li { display: flex; align-items: center; gap: 14px; background: #fff; border: 1px solid #e5e7eb;
       border-left: 5px solid #9ca3af; border-radius: 14px; padding: 16px 18px; margin-bottom: 12px; }
  li.done { border-left-color: #22c55e; }
  li form { margin: 0; }
  .check { width: 24px; height: 24px; border-radius: 7px; border: 2px solid #d1d5db; background: #fff;
           color: #fff; cursor: pointer; font-size: 14px; line-height: 1; padding: 0; }
  li.done .check { background: #22c55e; border-color: #22c55e; }
  .body { flex: 1; }
  .txt { font-weight: 600; }
  li.done .txt { text-decoration: line-through; color: #9ca3af; }
  .meta { font-size: 12px; color: #9ca3af; margin-top: 4px; }
  .badge { margin-left: 8px; padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 11px;
           background: #f3f4f6; color: #6b7280; }
  li.done .badge { background: #dcfce7; color: #16a34a; }
  .del { border: 0; background: none; color: #9ca3af; font-size: 18px; cursor: pointer; }
  .del:hover { color: #ef4444; }
  .empty { text-align: center; color: #9ca3af; padding: 30px; }
  footer { text-align: center; color: #9ca3af; font-size: 13px; padding: 28px;
           border-top: 1px solid #e5e7eb; margin-top: 40px; background: #fff; }
</style>
</head>
<body>
<header><div class="logo">&#10003;</div><span>Study Planner</span></header>
<main>
  <h1 id="title">Daily Task Manager</h1>
  <p class="sub">Stay organized. Keep it simple.</p>

  <div class="stats">
    <div><span class="dot" style="background:#3b82f6"></span>Total <b>{{ total }}</b></div>
    <div><span class="dot" style="background:#22c55e"></span>Completed <b>{{ completed }}</b></div>
    <div><span class="dot" style="background:#9ca3af"></span>Pending <b>{{ pending }}</b></div>
  </div>

  <form class="add" method="post" action="/add">
    <input name="text" id="note-input" placeholder="What needs to be done?" required>
    <button id="add-btn">+ Add Task</button>
  </form>

  <div class="tabs">
    <a href="/?filter=all" class="{{ 'active' if flt=='all' }}">All</a>
    <a href="/?filter=pending" class="{{ 'active' if flt=='pending' }}">Pending</a>
    <a href="/?filter=completed" class="{{ 'active' if flt=='completed' }}">Completed</a>
  </div>

  <ul id="notes">
    {% for t in tasks %}
    <li class="{{ 'done' if t.done }}">
      <form method="post" action="/toggle/{{ t.id }}"><button class="check" title="Toggle">{{ '&#10003;'|safe if t.done }}</button></form>
      <div class="body">
        <div class="txt">{{ t.text }}</div>
        <div class="meta">{{ t.time }}<span class="badge">{{ 'COMPLETED' if t.done else 'PENDING' }}</span></div>
      </div>
      <form method="post" action="/delete/{{ t.id }}"><button class="del" title="Delete">&#128465;</button></form>
    </li>
    {% endfor %}
  </ul>
  {% if not tasks %}<div class="empty">No tasks here yet.</div>{% endif %}
</main>
<footer>Built with Flask, Postgres and Docker &middot; <span id="host">Served by: {{ host }}</span></footer>
</body>
</html>
"""

@app.route("/")
def index():
    flt = request.args.get("filter", "all")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, text, COALESCE(done, FALSE), created_at FROM notes ORDER BY id DESC")
    rows = cur.fetchall(); conn.close()
    all_tasks = [{"id": r[0], "text": r[1], "done": r[2],
                  "time": r[3].strftime("%d %b, %I:%M %p") if r[3] else ""} for r in rows]
    total = len(all_tasks)
    completed = sum(1 for t in all_tasks if t["done"])
    if flt == "pending":
        tasks = [t for t in all_tasks if not t["done"]]
    elif flt == "completed":
        tasks = [t for t in all_tasks if t["done"]]
    else:
        flt, tasks = "all", all_tasks
    return render_template_string(PAGE, tasks=tasks, total=total, completed=completed,
                                  pending=total - completed, flt=flt, host=socket.gethostname())

@app.route("/add", methods=["POST"])
def add():
    text = request.form["text"].strip()
    if text:
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO notes (text, done) VALUES (%s, FALSE)", (text,))
        conn.commit(); conn.close()
    return redirect("/")

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle(task_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE notes SET done = NOT COALESCE(done, FALSE) WHERE id = %s", (task_id,))
    conn.commit(); conn.close()
    return redirect(request.referrer or "/")

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = %s", (task_id,))
    conn.commit(); conn.close()
    return redirect(request.referrer or "/")

@app.route("/health")
def health():
    return "OK", 200

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)