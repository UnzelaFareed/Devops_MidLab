import os, socket, time
from datetime import date
import psycopg2
from flask import Flask, request, redirect, render_template_string, jsonify

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
            cur.execute("ALTER TABLE notes ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'Medium'")
            cur.execute("ALTER TABLE notes ADD COLUMN IF NOT EXISTS due_date DATE")
            conn.commit(); conn.close(); return
        except Exception:
            time.sleep(2)

def fetch_tasks():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, text, COALESCE(done, FALSE), created_at, "
                "COALESCE(priority, 'Medium'), due_date FROM notes ORDER BY id DESC")
    rows = cur.fetchall(); conn.close()
    today = date.today()
    return [{
        "id": r[0], "text": r[1], "done": r[2],
        "time": r[3].strftime("%d %b, %I:%M %p") if r[3] else "",
        "priority": r[4],
        "due": r[5].strftime("%d %b %Y") if r[5] else "",
        "overdue": bool(r[5] and r[5] < today and not r[2]),
    } for r in rows]

STYLE = """
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: 'Segoe UI', Arial, sans-serif; background: #f5f7fb; color: #1f2937; }
  main { max-width: 760px; margin: 36px auto; padding: 0 16px; }
  h1 { font-size: 34px; margin: 0 0 6px; }
  .sub { color: #9ca3af; margin: 0 0 20px; }
  .stats { display: flex; gap: 22px; margin-bottom: 20px; font-size: 14px; color: #6b7280; }
  .stats b { color: #111827; margin-left: 4px; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .add { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
  .add input[type=text], .search input { flex: 1; min-width: 180px; padding: 12px 14px; border: 1px solid #e5e7eb;
        border-radius: 12px; font-size: 15px; outline: none; background: #fff; }
  .add select, .add input[type=date] { padding: 12px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; }
  .add button { padding: 0 22px; min-height: 44px; border: 0; border-radius: 12px; color: #fff; font-weight: 600;
        font-size: 15px; cursor: pointer; background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
  .search { display: flex; gap: 8px; margin-bottom: 14px; }
  .search button { padding: 0 16px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; cursor: pointer; }
  .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
  .tabs a { padding: 6px 16px; border: 1px solid #e5e7eb; border-radius: 20px; background: #fff;
            color: #6b7280; text-decoration: none; font-size: 14px; }
  .tabs a.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
  ul { list-style: none; padding: 0; margin: 0; }
  li { display: flex; align-items: center; gap: 14px; background: #fff; border: 1px solid #e5e7eb;
       border-left: 5px solid #9ca3af; border-radius: 14px; padding: 14px 18px; margin-bottom: 12px; }
  li.done { border-left-color: #22c55e; }
  li form { margin: 0; }
  .check { width: 24px; height: 24px; border-radius: 7px; border: 2px solid #d1d5db; background: #fff;
           color: #fff; cursor: pointer; font-size: 14px; padding: 0; }
  li.done .check { background: #22c55e; border-color: #22c55e; }
  .body { flex: 1; }
  .txt { font-weight: 600; }
  li.done .txt { text-decoration: line-through; color: #9ca3af; }
  .meta { font-size: 12px; color: #9ca3af; margin-top: 5px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  .badge, .prio, .due { padding: 2px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; background: #f3f4f6; color: #6b7280; }
  li.done .badge { background: #dcfce7; color: #16a34a; }
  .prio.high { background: #fee2e2; color: #dc2626; }
  .prio.medium { background: #fef3c7; color: #d97706; }
  .prio.low { background: #dbeafe; color: #2563eb; }
  .due.over { background: #fee2e2; color: #dc2626; }
  .del, .edit { border: 0; background: none; color: #9ca3af; font-size: 18px; cursor: pointer; text-decoration: none; }
  .del:hover { color: #ef4444; } .edit:hover { color: #3b82f6; }
  .empty { text-align: center; color: #9ca3af; padding: 26px; }
  footer { text-align: center; color: #9ca3af; font-size: 13px; padding: 24px; border-top: 1px solid #e5e7eb;
           margin-top: 36px; background: #fff; }
</style>
"""

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Daily Task Manager</title>""" + STYLE + """
</head><body><main>
  <h1 id="title">Daily Task Manager</h1>
  <p class="sub">Stay organized. Keep it simple.</p>
  <div class="stats">
    <div><span class="dot" style="background:#3b82f6"></span>Total <b>{{ total }}</b></div>
    <div><span class="dot" style="background:#22c55e"></span>Completed <b>{{ completed }}</b></div>
    <div><span class="dot" style="background:#9ca3af"></span>Pending <b>{{ pending }}</b></div>
  </div>

  <form class="add" method="post" action="/add">
    <input type="text" name="text" id="note-input" placeholder="What needs to be done?" required>
    <select name="priority"><option>High</option><option selected>Medium</option><option>Low</option></select>
    <input type="date" name="due_date">
    <button id="add-btn">+ Add Task</button>
  </form>

  <form class="search" method="get" action="/">
    <input type="text" name="q" value="{{ q }}" placeholder="Search tasks...">
    <input type="hidden" name="filter" value="{{ flt }}">
    <button>Search</button>
  </form>

  <div class="tabs">
    <a href="/?filter=all&q={{ q }}" class="{{ 'active' if flt=='all' }}">All</a>
    <a href="/?filter=pending&q={{ q }}" class="{{ 'active' if flt=='pending' }}">Pending</a>
    <a href="/?filter=completed&q={{ q }}" class="{{ 'active' if flt=='completed' }}">Completed</a>
  </div>

  <ul id="notes">
    {% for t in tasks %}
    <li class="{{ 'done' if t.done }}">
      <form method="post" action="/toggle/{{ t.id }}"><button class="check" title="Toggle">{{ '&#10003;'|safe if t.done }}</button></form>
      <div class="body">
        <div class="txt">{{ t.text }}</div>
        <div class="meta">{{ t.time }}
          <span class="badge">{{ 'COMPLETED' if t.done else 'PENDING' }}</span>
          <span class="prio {{ t.priority|lower }}">{{ t.priority }}</span>
          {% if t.due %}<span class="due {{ 'over' if t.overdue }}">Due {{ t.due }}</span>{% endif %}
        </div>
      </div>
      <a class="edit" href="/edit/{{ t.id }}" title="Edit">&#9998;</a>
      <form method="post" action="/delete/{{ t.id }}"><button class="del" title="Delete">&#128465;</button></form>
    </li>
    {% endfor %}
  </ul>
  {% if not tasks %}<div class="empty">No tasks here yet.</div>{% endif %}
</main>
<footer>Flask + PostgreSQL + Docker &middot; <span id="host">Served by: {{ host }}</span></footer>
</body></html>"""

EDIT_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Edit Task</title>""" + STYLE + """
</head><body><main>
  <h1>Edit Task</h1>
  <form class="add" method="post" action="/edit/{{ t.id }}">
    <input type="text" name="text" value="{{ t.text }}" required>
    <select name="priority">
      {% for p in ['High','Medium','Low'] %}<option {{ 'selected' if p==t.priority }}>{{ p }}</option>{% endfor %}
    </select>
    <input type="date" name="due_date" value="{{ t.due_iso }}">
    <button>Save</button>
  </form>
  <a href="/">&larr; Back</a>
</main></body></html>"""

@app.route("/")
def index():
    flt = request.args.get("filter", "all")
    q = request.args.get("q", "").strip()
    all_tasks = fetch_tasks()
    total = len(all_tasks)
    completed = sum(1 for t in all_tasks if t["done"])
    tasks = all_tasks
    if flt == "pending":
        tasks = [t for t in tasks if not t["done"]]
    elif flt == "completed":
        tasks = [t for t in tasks if t["done"]]
    else:
        flt = "all"
    if q:
        tasks = [t for t in tasks if q.lower() in t["text"].lower()]
    return render_template_string(PAGE, tasks=tasks, total=total, completed=completed,
                                  pending=total - completed, flt=flt, q=q, host=socket.gethostname())

@app.route("/add", methods=["POST"])
def add():
    text = request.form["text"].strip()
    priority = request.form.get("priority", "Medium")
    if priority not in ("High", "Medium", "Low"):
        priority = "Medium"
    due = request.form.get("due_date") or None
    if text:
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO notes (text, done, priority, due_date) VALUES (%s, FALSE, %s, %s)",
                    (text, priority, due))
        conn.commit(); conn.close()
    return redirect("/")

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    conn = get_conn(); cur = conn.cursor()
    if request.method == "POST":
        priority = request.form.get("priority", "Medium")
        if priority not in ("High", "Medium", "Low"):
            priority = "Medium"
        cur.execute("UPDATE notes SET text=%s, priority=%s, due_date=%s WHERE id=%s",
                    (request.form["text"].strip(), priority, request.form.get("due_date") or None, task_id))
        conn.commit(); conn.close()
        return redirect("/")
    cur.execute("SELECT id, text, COALESCE(priority,'Medium'), due_date FROM notes WHERE id=%s", (task_id,))
    r = cur.fetchone(); conn.close()
    if not r:
        return redirect("/")
    t = {"id": r[0], "text": r[1], "priority": r[2], "due_iso": r[3].isoformat() if r[3] else ""}
    return render_template_string(EDIT_PAGE, t=t)

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

@app.route("/api/tasks")
def api_tasks():
    return jsonify(fetch_tasks())

@app.route("/health")
def health():
    return "OK", 200

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)