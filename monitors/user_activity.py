# monitors/user_activity.py
import psutil
import json
import time
from datetime import datetime
from database import insert_event
from config import USER_ACTIVITY_INTERVAL

def gather_user_features():
    # process_count, avg_cpu_percent, avg_mem_percent, num_root_processes, num_new_logins
    procs = list(psutil.process_iter(["pid", "username", "cpu_percent", "memory_percent", "name"]))
    proc_count = len(procs)
    cpu_perc = sum([p.info["cpu_percent"] or 0.0 for p in procs])
    mem_perc = sum([p.info["memory_percent"] or 0.0 for p in procs])
    root_procs = sum(1 for p in procs if p.info["username"] in ("root","0"))
    # open terminals / suspicious shells
    shells = ["bash", "sh", "zsh", "ksh", "dash"]
    shell_count = sum(1 for p in procs if any(s in (p.info["name"] or "") for s in shells))
    # logged in users
    try:
        users = psutil.users()
        num_users = len(users)
    except Exception:
        num_users = 0

    features = {
        "proc_count": proc_count,
        "cpu_sum": cpu_perc,
        "mem_sum": mem_perc,
        "root_proc_count": root_procs,
        "shell_count": shell_count,
        "num_users": num_users,
        "timestamp": datetime.utcnow().isoformat()
    }
    return features

def start_user_activity_thread(stop_event, sample_queue):
    import threading
    def run():
        while not stop_event.is_set():
            try:
                feat = gather_user_features()
                # push to queue for ML detector
                sample_queue.put(feat)
                # Create an event log for large deviations (basic heuristic)
                if feat["root_proc_count"] > 50:
                    insert_event("user_activity", "HIGH", f"many root processes: {feat['root_proc_count']}")
            except Exception as e:
                print("[user_activity] exception", e)
            time.sleep(USER_ACTIVITY_INTERVAL)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
