import sqlite3
import os

DB_PATH = "/data/provisioning.db"

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY,
        username TEXT,
        server_ip TEXT,
        server_ssh_port INTEGER,
        system_username TEXT,
        status TEXT DEFAULT 'in_progress'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        log_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
]

PROXY_TOKENS = os.getenv("PROXY_TOKENS", "abc123").split(",")


def init_db():
    os.makedirs("/data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for ddl in SCHEMA:
        cur.execute(ddl)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Database helper functions for tasks and logs
def insert_task(task_id, username, server_ip, server_ssh_port, system_username):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO tasks (task_id, username, server_ip, server_ssh_port, system_username) VALUES (?, ?, ?, ?, ?)",
        (task_id, username, server_ip, server_ssh_port, system_username)
    )
    conn.commit()
    conn.close()

def update_task_status(task_id, status):
    conn = get_db()
    conn.execute("UPDATE tasks SET status = ? WHERE task_id = ?", (status, task_id))
    conn.commit()
    conn.close()

def insert_log(task_id, log_text):
    conn = get_db()
    conn.execute("INSERT INTO logs (task_id, log_text) VALUES (?, ?)", (task_id, log_text))
    conn.commit()
    conn.close()

def get_task_status(task_id):
    conn = get_db()
    row = conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    log_row = conn.execute("SELECT log_text FROM logs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1", (task_id,)).fetchone()
    conn.close()
    return (row["status"] if row else "not_found", log_row["log_text"] if log_row else "")

def validate_token(token: str) -> bool:
    return token in PROXY_TOKENS