import sqlite3
from datetime import datetime

DB_PATH = "agent_history.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                source TEXT,
                question TEXT,
                answer TEXT,
                model TEXT,
                mode TEXT
            );
        ''')

def log_to_db(question, answer, source="text", model="gpt-4o", mode="short"):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO history (timestamp, source, question, answer, model, mode)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            source,
            question,
            answer,
            model,
            mode
        ))
