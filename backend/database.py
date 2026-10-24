import os
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timezone

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres@127.0.0.1:5432/vehicle_analytics"
)

def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                vehicle_type TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT 'Unknown',
                confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
                track_id BIGINT,
                frame_number BIGINT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_events (
                id BIGSERIAL PRIMARY KEY,
                vehicle_id VARCHAR(100) NOT NULL,
                color VARCHAR(50) NOT NULL DEFAULT 'Unknown',
                event_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                direction VARCHAR(20) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_detections_timestamp
            ON detections (timestamp DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vehicle_events_timestamp
            ON vehicle_events (event_timestamp DESC)
        """)

def save_detection(vehicle_type, color, confidence, track_id=None, frame_number=None):
    with connect() as conn:
        conn.execute("""
            INSERT INTO detections
                (timestamp, vehicle_type, color, confidence, track_id, frame_number)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            datetime.now(timezone.utc),
            str(vehicle_type),
            str(color),
            float(confidence),
            track_id,
            frame_number
        ))

def get_recent_detections(limit=50):
    with connect() as conn:
        rows = conn.execute("""
            SELECT id, timestamp, vehicle_type, color, confidence, track_id, frame_number
            FROM detections ORDER BY id DESC LIMIT %s
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]

def get_stats():
    with connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS count FROM detections"
        ).fetchone()["count"]

        rows = conn.execute("""
            SELECT LOWER(vehicle_type) AS vehicle_type, COUNT(*) AS count
            FROM detections GROUP BY LOWER(vehicle_type)
        """).fetchall()

        counts = {row["vehicle_type"]: row["count"] for row in rows}

        return {
            "total_detections": total,
            "cars": counts.get("car", 0),
            "trucks": counts.get("truck", 0),
            "buses": counts.get("bus", 0),
            "motorcycles": counts.get("motorcycle", counts.get("motorbike", 0)),
            "by_type": [
                {"name": row["vehicle_type"], "count": row["count"]}
                for row in rows
            ]
        }

def clear_detections():
    with connect() as conn:
        conn.execute("DELETE FROM detections")
def save_vehicle_event(vehicle_id, color, direction):
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO vehicle_events
                (vehicle_id, color, event_timestamp, direction)
            VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
            """,
            (str(vehicle_id), str(color), str(direction))
        )
