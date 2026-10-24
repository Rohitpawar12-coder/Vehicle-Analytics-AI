from pathlib import Path
import sqlite3
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "vehicle_analytics.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

def save_detection(vehicle_type, color, confidence, track_id=None, frame_number=None):
    with connect() as conn:
        conn.execute("""
            INSERT INTO detections
            (timestamp, vehicle_type, color, confidence, track_id, frame_number)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(timespec="seconds"),
            str(vehicle_type),
            str(color),
            float(confidence),
            track_id,
            frame_number
        ))

def get_recent_detections(limit=50):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM detections ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

def get_stats():
    with connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM detections"
        ).fetchone()[0]

        rows = conn.execute("""
            SELECT LOWER(vehicle_type) AS vehicle_type, COUNT(*) AS count
            FROM detections
            GROUP BY LOWER(vehicle_type)
        """).fetchall()

        counts = {row["vehicle_type"]: row["count"] for row in rows}

        return {
            "total_detections": total,
            "cars": counts.get("car", 0),
            "trucks": counts.get("truck", 0),
            "buses": counts.get("bus", 0),
            "motorcycles": counts.get("motorcycle", counts.get("motorbike", 0)),
            "by_type": [{"name": row["vehicle_type"], "count": row["count"]} for row in rows]
        }

def clear_detections():
    with connect() as conn:
        conn.execute("DELETE FROM detections")
