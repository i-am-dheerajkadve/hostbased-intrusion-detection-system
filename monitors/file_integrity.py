# monitors/file_integrity.py
import hashlib
import json
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from database import insert_event
from config import WATCH_DIRS

# Build baseline hashes for files in WATCH_DIRS
IGNORED_EXT = {".swp", ".tmp"}

def file_hash(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

class IntegrityMonitor:
    def __init__(self):
        self.baseline = {}  # path -> hash

    def build_baseline(self):
        for root_dir in WATCH_DIRS:
            if not os.path.exists(root_dir):
                continue
            for dirpath, _, filenames in os.walk(root_dir):
                for fname in filenames:
                    _, ext = os.path.splitext(fname)
                    if ext in IGNORED_EXT:
                        continue
                    path = os.path.join(dirpath, fname)
                    h = file_hash(path)
                    if h:
                        self.baseline[path] = h

    def check_snapshot(self):
        changed = []
        removed = []
        added = []
        # find removed or changed
        for path, old_hash in list(self.baseline.items()):
            if not os.path.exists(path):
                removed.append(path)
                del self.baseline[path]
            else:
                h = file_hash(path)
                if h is None:
                    continue
                if h != old_hash:
                    changed.append(path)
                    self.baseline[path] = h
        # find newly added
        for root_dir in WATCH_DIRS:
            if not os.path.exists(root_dir):
                continue
            for dirpath, _, filenames in os.walk(root_dir):
                for fname in filenames:
                    path = os.path.join(dirpath, fname)
                    if path not in self.baseline:
                        h = file_hash(path)
                        if h:
                            added.append(path)
                            self.baseline[path] = h
        for p in changed:
            msg = f"FILE_MODIFIED {p}"
            insert_event("file_integrity", "HIGH", msg)
            print("[file_integrity] modified:", p)
        for p in removed:
            msg = f"FILE_REMOVED {p}"
            insert_event("file_integrity", "HIGH", msg)
            print("[file_integrity] removed:", p)
        for p in added:
            msg = f"FILE_ADDED {p}"
            insert_event("file_integrity", "INFO", msg)
            print("[file_integrity] added:", p)

class WatchHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor

    def on_modified(self, event):
        if event.is_directory:
            return
        path = event.src_path
        h = file_hash(path)
        old = self.monitor.baseline.get(path)
        if old != h:
            self.monitor.baseline[path] = h
            insert_event("file_integrity", "HIGH", f"modified {path}")
            print("[watch] modified", path)

    def on_created(self, event):
        if event.is_directory:
            return
        path = event.src_path
        h = file_hash(path)
        if h:
            self.monitor.baseline[path] = h
            insert_event("file_integrity", "INFO", f"created {path}")
            print("[watch] created", path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if path in self.monitor.baseline:
            del self.monitor.baseline[path]
        insert_event("file_integrity", "HIGH", f"deleted {path}")
        print("[watch] deleted", path)

def start_file_integrity_thread(stop_event, poll_interval=30):
    import threading
    monitor = IntegrityMonitor()
    monitor.build_baseline()
    # Start watchdog observer on the watched dirs
    observer = Observer()
    handler = WatchHandler(monitor)
    for d in WATCH_DIRS:
        if os.path.exists(d):
            observer.schedule(handler, d, recursive=True)
    observer.start()
    def run():
        try:
            while not stop_event.is_set():
                monitor.check_snapshot()
                time.sleep(poll_interval)
        finally:
            observer.stop()
            observer.join()
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
