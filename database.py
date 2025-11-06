# database.py
import sqlite3
import threading
from datetime import datetime
from config import DB_PATH

_lock = threading.Lock()

def init_db():
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            severity TEXT,
            message TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            feature_blob TEXT,
            score REAL,
            is_anomaly INTEGER
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS model_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        conn.commit()
        conn.close()

def insert_event(source, severity, message):
    ts = datetime.utcnow().isoformat()
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO events (timestamp, source, severity, message) VALUES (?, ?, ?, ?)",
            (ts, source, severity, message)
        )
        conn.commit()
        conn.close()

def insert_feature(feature_blob_json, score, is_anomaly):
    ts = datetime.utcnow().isoformat()
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO features (timestamp, feature_blob, score, is_anomaly) VALUES (?, ?, ?, ?)",
                    (ts, feature_blob_json, float(score), int(bool(is_anomaly))))
        conn.commit()
        conn.close()

def save_model_meta(key, value):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO model_meta (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

def read_model_meta(key):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT value FROM model_meta WHERE key=?", (key,))
        r = cur.fetchone()
        conn.close()
        return r[0] if r else None
