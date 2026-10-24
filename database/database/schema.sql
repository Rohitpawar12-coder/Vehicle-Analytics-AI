-- SQLite schema is created automatically by backend/database.py.
-- This file documents the current table structure.
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    color TEXT NOT NULL,
    confidence REAL NOT NULL,
    track_id INTEGER,
    frame_number INTEGER
);
