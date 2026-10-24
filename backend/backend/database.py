from pathlib import Path
import sqlite3
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "vehicle_analytics.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                color TEXT NOT NULL,
                confidence REAL NOT NULL,
                track_id INTEGER,
                frame_number INTEGER
            )
        """)
        conn.commit()

def save_detection(vehicle_type, color, confidence, track_id=None, frame_number=None):
    with connect() as conn:
        conn.execute(
            """INSERT INTO detections
            (timestamp, vehicle_type, color, confidence, track_id, frame_number)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(timespec="seconds"), vehicle_type, color,
             float(confidence), track_id, frame_number)
        )
        conn.commit()

def get_stats():
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
        by_type = conn.execute(
            "SELECT vehicle_type, COUNT(*) AS count FROM detections GROUP BY vehicle_type ORDER BY count DESC"
        ).fetchall()
        by_color = conn.execute(
            "SELECT color, COUNT(*) AS count FROM detections GROUP BY color ORDER BY count DESC"
        ).fetchall()
        return {
            "total_detections": total,
            "by_type": [{"name": row["vehicle_type"], "count": row["count"]} for row in by_type],
            "by_color": [{"name": row["color"], "count": row["count"]} for row in by_color],
        }

def get_recent_detections(limit=50):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM detections ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

def clear_detections():
    with connect() as conn:
        conn.execute("DELETE FROM detections")
        conn.commit()
