import sqlite3
from pathlib import Path

DB_PATH = Path("db/incidents.db")

class KnowledgeBaseAgent:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                pipeline TEXT,
                task_id TEXT,
                error TEXT,
                severity TEXT,
                retry_count INTEGER,
                pipeline_type TEXT,
                source_system TEXT,
                summary TEXT,
                next_steps TEXT,
                fix TEXT,
                validation TEXT
            )
            """)

    def log_incident(self, event, severity="Medium", retry_count=0, pipeline_type="ETL", source_system="Local", summary="", next_steps="", fix="", validation=""):
        with self.conn:
            self.conn.execute("""
            INSERT INTO incidents (
                timestamp, pipeline, task_id, error, severity, retry_count, pipeline_type, source_system, summary, next_steps, fix, validation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event["timestamp"], event["pipeline"], event["task_id"], event["error"],
                severity, retry_count, pipeline_type, source_system, summary, next_steps, fix, validation
            ))

    def fetch_incidents(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
        return cursor.fetchall()