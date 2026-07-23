"""AI Worker — SQLite storage backend with schema & CRUD helpers."""
import sqlite3
import json
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".agent")
DB_PATH = os.path.join(DB_DIR, "ai_worker.db")

os.makedirs(DB_DIR, exist_ok=True)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_type TEXT NOT NULL DEFAULT 'task',
    description TEXT NOT NULL,
    duration_min INTEGER,
    rating INTEGER,
    decisions TEXT,
    outcome TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    priority TEXT DEFAULT 'medium',
    category TEXT,
    blocker TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    context TEXT,
    session_id INTEGER,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    confidence REAL DEFAULT 1.0,
    tags TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    when_to_use TEXT,
    example TEXT,
    source_insight_ids TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS memory (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    priority TEXT DEFAULT 'medium',
    target_date TEXT,
    progress REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS insight_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    payload TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

_db_local = None

def get_db():
    global _db_local
    if _db_local is None:
        _db_local = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_local.row_factory = sqlite3.Row
        _db_local.executescript(SCHEMA_SQL)
    return _db_local

# ── Session helpers ──────────────────────────────
def log_session(session_type, description, duration_min=None, rating=None, decisions=None, outcome=None):
    db = get_db()
    db.execute(
        "INSERT INTO sessions (session_type, description, duration_min, rating, decisions, outcome) VALUES (?,?,?,?,?,?)",
        (session_type, description, duration_min, rating, json.dumps(decisions or []), outcome)
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]

def get_recent_sessions(limit=10):
    return get_db().execute(
        "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()

# ── Task helpers ─────────────────────────────────
def add_task(title, priority="medium", category=None, notes=None):
    db = get_db()
    db.execute(
        "INSERT INTO tasks (title, priority, category, notes) VALUES (?,?,?,?)",
        (title, priority, category, notes)
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]

def update_task(task_id, **kwargs):
    db = get_db()
    allowed = {"status", "priority", "blocker", "notes", "title", "category", "completed_at"}
    for k, v in kwargs.items():
        if k in allowed:
            db.execute(f"UPDATE tasks SET {k}=? WHERE id=?", (v, task_id))
    if kwargs.get("status") == "completed" and "completed_at" not in kwargs:
        db.execute("UPDATE tasks SET completed_at=datetime('now','localtime') WHERE id=? AND completed_at IS NULL", (task_id,))
    db.commit()

def list_tasks(status=None):
    if status:
        return get_db().execute("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
    return get_db().execute("SELECT * FROM tasks ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'blocked' THEN 1 ELSE 2 END, created_at DESC").fetchall()

def get_task(task_id):
    return get_db().execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()

def delete_task(task_id):
    get_db().execute("DELETE FROM tasks WHERE id=?", (task_id,))
    get_db().commit()

# ── Decision helpers ─────────────────────────────
def log_decision(decision, reason=None, context=None, date=None):
    db = get_db()
    db.execute(
        "INSERT INTO decisions (date, decision, reason, context) VALUES (?,?,?,?)",
        (date or datetime.now().strftime("%Y-%m-%d"), decision, reason, json.dumps(context or {}))
    )
    db.commit()

def get_decisions(limit=20):
    return get_db().execute("SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()

# ── Insight helpers ──────────────────────────────
def add_insight(insight_type, content, source=None, confidence=1.0, tags=None):
    db = get_db()
    db.execute(
        "INSERT INTO insights (type, content, source, confidence, tags) VALUES (?,?,?,?,?)",
        (insight_type, content, source, confidence, json.dumps(tags or []))
    )
    db.commit()

def get_insights(limit=50, insight_type=None):
    if insight_type:
        return get_db().execute(
            "SELECT * FROM insights WHERE type=? ORDER BY created_at DESC LIMIT ?", (insight_type, limit)
        ).fetchall()
    return get_db().execute(
        "SELECT * FROM insights ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()

def search_insights(query, limit=20):
    return get_db().execute(
        "SELECT *, 0 as rank FROM insights WHERE content LIKE ? OR tags LIKE ? ORDER BY confidence DESC LIMIT ?",
        (f"%{query}%", f"%{query}%", limit)
    ).fetchall()

# ── Skill helpers ────────────────────────────────
def add_skill(name, description, when_to_use, example, source_insight_ids=None):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO skills (name, description, when_to_use, example, source_insight_ids) VALUES (?,?,?,?,?)",
        (name, description, when_to_use, example, json.dumps(source_insight_ids or []))
    )
    db.commit()

def get_skills(limit=50):
    return get_db().execute("SELECT * FROM skills ORDER BY usage_count DESC, updated_at DESC LIMIT ?", (limit,)).fetchall()

def increment_skill(name):
    db = get_db()
    db.execute("UPDATE skills SET usage_count=usage_count+1, updated_at=datetime('now','localtime') WHERE name=?", (name,))
    db.commit()

# ── Memory helpers ───────────────────────────────
def set_memory(key, value, category="general"):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO memory (key, value, category, updated_at) VALUES (?,?,?,datetime('now','localtime'))",
        (key, value, category)
    )
    db.commit()

def get_memory(key):
    row = get_db().execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None

def delete_memory(key):
    get_db().execute("DELETE FROM memory WHERE key=?", (key,))
    get_db().commit()

def list_memory(category=None):
    if category:
        return get_db().execute("SELECT * FROM memory WHERE category=? ORDER BY updated_at DESC", (category,)).fetchall()
    return get_db().execute("SELECT * FROM memory ORDER BY updated_at DESC").fetchall()

# ── Goal helpers ─────────────────────────────────
def add_goal(title, description=None, priority="medium", target_date=None):
    db = get_db()
    db.execute(
        "INSERT INTO goals (title, description, priority, target_date) VALUES (?,?,?,?)",
        (title, description, priority, target_date)
    )
    db.commit()

def update_goal(goal_id, **kwargs):
    db = get_db()
    allowed = {"title", "description", "status", "priority", "target_date", "progress", "completed_at"}
    for k, v in kwargs.items():
        if k in allowed:
            db.execute(f"UPDATE goals SET {k}=? WHERE id=?", (v, goal_id))
    if kwargs.get("status") == "completed":
        db.execute("UPDATE goals SET completed_at=datetime('now','localtime') WHERE id=? AND completed_at IS NULL", (goal_id,))
    db.commit()

def list_goals(status=None):
    if status:
        return get_db().execute("SELECT * FROM goals WHERE status=? ORDER BY priority, created_at DESC", (status,)).fetchall()
    return get_db().execute("SELECT * FROM goals ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, priority, created_at DESC").fetchall()

# ── Event logging ────────────────────────────────
def log_event(event_type, source, payload=None):
    db = get_db()
    db.execute(
        "INSERT INTO insight_events (event_type, source, payload) VALUES (?,?,?)",
        (event_type, source, json.dumps(payload or {}))
    )
    db.commit()

def get_events(event_type=None, limit=50):
    if event_type:
        return get_db().execute(
            "SELECT * FROM insight_events WHERE event_type=? ORDER BY created_at DESC LIMIT ?", (event_type, limit)
        ).fetchall()
    return get_db().execute("SELECT * FROM insight_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
