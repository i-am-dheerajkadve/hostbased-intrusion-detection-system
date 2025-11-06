# monitors/logs_monitor.py
import time
import os
import threading
from database import insert_event
from config import LOG_FILES

def tail_f(path, stop_event, callback):
    try:
        with open(path, "r") as f:
            # Go to end of file
            f.seek(0, os.SEEK_END)
            while not stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                callback(path, line.rstrip("\n"))
    except FileNotFoundError:
        print(f"[logs_monitor] file not found: {path}")
    except Exception as e:
        print("[logs_monitor] exception", e)

def parse_log_line(path, line):
    # Basic heuristics for suspicious lines
    low = line.lower()
    if "failed password" in low or "authentication failure" in low:
        insert_event("logs", "HIGH", f"{path}: {line}")
        print("[logs_monitor] suspicious auth:", line)
    elif "invalid user" in low or "authentication failure" in low:
        insert_event("logs", "HIGH", f"{path}: {line}")
    elif "accepted password" in low:
        insert_event("logs", "INFO", f"{path}: {line}")
    # Add more heuristics as required

def start_logs_thread(stop_event):
    threads = []
    for p in LOG_FILES:
        t = threading.Thread(target=tail_f, args=(p, stop_event, parse_log_line), daemon=True)
        t.start()
        threads.append(t)
    return threads
