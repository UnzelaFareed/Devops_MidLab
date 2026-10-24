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

# ---------------------------------------------------------------- THEME
# Sage Green + Cream + Dusty Rose. Light and dark palettes are CSS variables.
HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<script>
(function () {
  try {
    var t = localStorage.getItem('theme');
    if (!t) { t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; }
    document.documentElement.setAttribute('data-theme', t);
  } catch (e) {}
})();
function toggleTheme() {
  try {
    var r = document.documentElement;
    var n = r.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    r.setAttribute('data-theme', n);
    localStorage.setItem('theme', n);
  } catch (e) {}
}
</script>
<style>
  :root {
    --bg: #F7F9F6; --card: #FFFFFF; --input: #F3F6F2;
    --primary: #6B8F71; --primary-hover: #5C7E62; --on-primary: #FFFFFF; --sage: #A8B8A0;
    --heading: #2D3748; --muted: #718096; --done: #3F6B4F;
    --high-bg: #E8C9C3; --high-fg: #8A4B42;
    --med-bg: #F6E7C8; --med-fg: #8A6A2A;
    --low-bg: #DDE7DC; --low-fg: #3F6B4F;
    --chip: #EEF1EC; --border: #E2E8E0;
    --shadow: 0 1px 2px rgba(45,55,72,.04), 0 6px 18px rgba(45,55,72,.04);
  }
  [data-theme="dark"] {
    --bg: #131815; --card: #1C231F; --input: #252E28;
    --primary: #7DA284; --primary-hover: #8DB394; --on-primary: #10150F; --sage: #5F7A66;
    --heading: #E9EFEA; --muted: #9BA9A0; --done: #8FC49F;
    --high-bg: #4B3633; --high-fg: #EBCFC9;
    --med-bg: #4A4128; --med-fg: #F6E7C8;
    --low-bg: #2B3A2F; --low-fg: #B7D3BD;
    --chip: #252E28; --border: #2E3832; --shadow: none;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--heading);
         font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, Arial, sans-serif; }
  main { max-width: 720px; margin: 40px auto 24px; padding: 0 16px; }
  .top { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
  h1 { font-size: 34px; margin: 0 0 4px; letter-spacing: -0.02em; color: var(--heading); }
  .sub { color: var(--muted); margin: 0 0 18px; }
  .icon-btn { width: 40px; height: 40px; display: inline-flex; align-items: center; justify-content: center;
              border: 1px solid var(--border); border-radius: 12px; background: var(--card); color: var(--primary);
              cursor: pointer; text-decoration: none; padding: 0; box-shadow: var(--shadow); }
  .icon-btn:hover { border-color: var(--sage); }
  .icon-btn svg, .check svg { width: 18px; height: 18px; }
  .sun { display: none; } [data-theme="dark"] .sun { display: block; } [data-theme="dark"] .moon { display: none; }
  .stats { display: flex; gap: 20px; margin-bottom: 18px; font-size: 14px; color: var(--muted); font-weight: 500; }
  .stats b { color: var(--heading); margin-left: 4px; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .panel { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 12px;
           margin-bottom: 14px; box-shadow: var(--shadow); }
  .add { display: flex; gap: 10px; flex-wrap: wrap; }
  .add input[type=text] { flex: 1; min-width: 170px; }
  input[type=text], input[type=date], select { padding: 12px 14px; border: 1px solid var(--border);
        border-radius: 12px; font: inherit; font-size: 14px; background: var(--input); color: var(--heading); outline: none; }
  input:focus, select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(107,143,113,.18); }
  ::placeholder { color: var(--muted); opacity: .8; }
  .btn { display: inline-flex; align-items: center; gap: 6px; padding: 0 20px; min-height: 44px; border: 0;
         border-radius: 12px; background: var(--primary); color: var(--on-primary); font: inherit;
         font-weight: 600; font-size: 14px; cursor: pointer; }
  .btn:hover { background: var(--primary-hover); }
  .btn svg { width: 14px; height: 14px; }
  .btn.ghost { background: var(--card); color: var(--heading); border: 1px solid var(--border); }
  .btn.ghost:hover { border-color: var(--sage); background: var(--card); }
  .search { display: flex; gap: 10px; margin-bottom: 14px; }
  .search-box { position: relative; flex: 1; }
  .search-box svg { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); width: 15px; height: 15px; color: var(--muted); }
  .search-box input { width: 100%; padding-left: 38px; background: var(--card); }
  .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
  .tabs a { padding: 7px 16px; border: 1px solid var(--border); border-radius: 20px; background: var(--card);
            color: var(--muted); text-decoration: none; font-size: 13px; font-weight: 600; }
  .tabs a.active { background: var(--primary); color: var(--on-primary); border-color: var(--primary); }
  ul { list-style: none; padding: 0; margin: 0; }
  li { display: flex; align-items: center; gap: 14px; background: var(--card); border: 1px solid var(--border);
       border-radius: 16px; padding: 14px 16px; margin-bottom: 10px; box-shadow: var(--shadow); }
  li.done { border-left: 3px solid var(--done); }
  li form { margin: 0; }
  .check { width: 24px; height: 24px; border-radius: 8px; border: 2px solid var(--border); background: var(--card);
           color: var(--on-primary); cursor: pointer; padding: 0; display: flex; align-items: center; justify-content: center; }
  .check:hover { border-color: var(--primary); }
  .check svg { width: 14px; height: 14px; }
  li.done .check { background: var(--done); border-color: var(--done); color: #fff; }
  .body { flex: 1; min-width: 0; }
  .txt { font-weight: 600; font-size: 15px; overflow-wrap: anywhere; }
  li.done .txt { text-decoration: line-through; color: var(--primary); }
  .meta { font-size: 12px; color: var(--muted); margin-top: 5px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  .badge, .prio, .due { padding: 2px 10px; border-radius: 8px; font-weight: 600; font-size: 11px;
                        background: var(--chip); color: var(--muted); }
  .badge { letter-spacing: .02em; }
  li.done .badge { background: var(--low-bg); color: var(--done); }
  .prio.high { background: var(--high-bg); color: var(--high-fg); }
  .prio.medium { background: var(--med-bg); color: var(--med-fg); }
  .prio.low { background: var(--low-bg); color: var(--low-fg); }
  .due.over { background: var(--high-bg); color: var(--high-fg); }
  .act { width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; border: 0;
         background: none; color: var(--muted); cursor: pointer; border-radius: 8px; text-decoration: none; padding: 0; }
  .act svg { width: 16px; height: 16px; }
  .act:hover { background: var(--chip); color: var(--heading); }
  .act.del:hover { color: var(--high-fg); background: var(--high-bg); }
  .empty { text-align: center; color: var(--muted); padding: 40px 20px; border: 1px dashed var(--sage);
           border-radius: 16px; background: var(--card); }
  .empty svg { width: 28px; height: 28px; color: var(--sage); margin-bottom: 10px; }
  .empty strong { display: block; color: var(--heading); font-size: 15px; margin-bottom: 4px; }
  .empty span { font-size: 12px; }
  .back { display: inline-block; margin-top: 8px; color: var(--primary); text-decoration: none; font-weight: 600; font-size: 14px; }
  footer { text-align: center; color: var(--muted); font-size: 12px; padding: 20px 16px 36px; }
  :focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
  @media (max-width: 520px) { h1 { font-size: 28px; } .stats { gap: 14px; } }
</style>
"""

ICONS = {
    "moon": '<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    "sun": '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
}

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Daily Task Manager</title>""" + HEAD + """
</head><body><main>
  <div class="top">
    <div>
      <h1 id="title">Daily Task Manager</h1>
      <p class="sub">Stay organized. Keep it simple.</p>
    </div>
    <button type="button" class="icon-btn" id="theme-toggle" onclick="toggleTheme()" aria-label="Toggle dark mode">""" + ICONS["moon"] + ICONS["sun"] + """</button>
  </div>

  <div class="stats">
    <div><span class="dot" style="background:var(--primary)"></span>Total <b>{{ total }}</b></div>
    <div><span class="dot" style="background:var(--done)"></span>Completed <b>{{ completed }}</b></div>
    <div><span class="dot" style="background:var(--muted)"></span>Pending <b>{{ pending }}</b></div>
  </div>

  <div class="panel">
    <form class="add" method="post" action="/add">
      <input type="text" name="text" id="note-input" placeholder="What needs to be done?" required>
      <select name="priority" aria-label="Priority"><option>High</option><option selected>Medium</option><option>Low</option></select>
      <input type="date" name="due_date" aria-label="Due date">
      <button class="btn" id="add-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>Add Task</button>
    </form>
  </div>

  <form class="search" method="get" action="/">
    <div class="search-box">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input type="text" name="q" value="{{ q }}" placeholder="Search tasks..." aria-label="Search tasks">
    </div>
    <input type="hidden" name="filter" value="{{ flt }}">
    <button class="btn ghost">Search</button>
  </form>

  <div class="tabs">
    <a href="/?filter=all&q={{ q }}" class="{{ 'active' if flt=='all' }}">All</a>
    <a href="/?filter=pending&q={{ q }}" class="{{ 'active' if flt=='pending' }}">Pending</a>
    <a href="/?filter=completed&q={{ q }}" class="{{ 'active' if flt=='completed' }}">Completed</a>
  </div>

  <ul id="notes">
    {% for t in tasks %}
    <li class="{{ 'done' if t.done }}">
      <form method="post" action="/toggle/{{ t.id }}"><button class="check" title="Toggle" aria-label="Mark complete">{% if t.done %}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>{% endif %}</button></form>
      <div class="body">
        <div class="txt">{{ t.text }}</div>
        <div class="meta">{{ t.time }}
          <span class="badge">{{ 'COMPLETED' if t.done else 'PENDING' }}</span>
          <span class="prio {{ t.priority|lower }}">{{ t.priority }}</span>
          {% if t.due %}<span class="due {{ 'over' if t.overdue }}">Due {{ t.due }}</span>{% endif %}
        </div>
      </div>
      <a class="act edit" href="/edit/{{ t.id }}" title="Edit" aria-label="Edit task"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg></a>
      <form method="post" action="/delete/{{ t.id }}"><button class="act del" title="Delete" aria-label="Delete task"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6"/></svg></button></form>
    </li>
    {% endfor %}
  </ul>
  {% if not tasks %}
  <div class="empty">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.5 3.5C11 3 5 8 5 14.5c0 1 .2 1.9.5 2.7L3 20l1.4 1.4 2.6-2.5c.9.4 1.9.6 3 .6C17 19.5 21 13 20.5 3.5z"/></svg>
    <strong>No tasks found</strong>
    <span>Enjoy your free time or add a new task above!</span>
  </div>
  {% endif %}
</main>
<footer>Flask + PostgreSQL + Docker &middot; <span id="host">Served by: {{ host }}</span></footer>
</body></html>"""

EDIT_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Edit Task</title>""" + HEAD + """
</head><body><main>
  <div class="top">
    <div><h1>Edit Task</h1><p class="sub">Update the text, priority or due date.</p></div>
    <button type="button" class="icon-btn" onclick="toggleTheme()" aria-label="Toggle dark mode">""" + ICONS["moon"] + ICONS["sun"] + """</button>
  </div>
  <div class="panel">
    <form class="add" method="post" action="/edit/{{ t.id }}">
      <input type="text" name="text" value="{{ t.text }}" required>
      <select name="priority" aria-label="Priority">
        {% for p in ['High','Medium','Low'] %}<option {{ 'selected' if p==t.priority }}>{{ p }}</option>{% endfor %}
      </select>
      <input type="date" name="due_date" value="{{ t.due_iso }}" aria-label="Due date">
      <button class="btn">Save changes</button>
    </form>
  </div>
  <a class="back" href="/">&larr; Back to tasks</a>
</main></body></html>"""

# ---------------------------------------------------------------- ROUTES (unchanged)
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