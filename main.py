# main.py
import threading, queue, time, signal, sys
from database import init_db
from monitors.file_integrity import start_file_integrity_thread
from monitors.logs_monitor import start_logs_thread
from monitors.user_activity import start_user_activity_thread
from ml_detector import MLDetector
from alerting import alert_console, alert_email
from config import INITIAL_TRAIN_SAMPLES

stop_event = threading.Event()

def graceful_stop(signum, frame):
    print("[main] stopping...")
    stop_event.set()

signal.signal(signal.SIGINT, graceful_stop)
signal.signal(signal.SIGTERM, graceful_stop)

def main():
    print("Initializing DB...")
    init_db()
    from config import WATCH_DIRS, LOG_FILES
    print("Watch dirs:", WATCH_DIRS)
    print("Log files:", LOG_FILES)

    # Create a queue for feature samples coming from user_activity
    sample_q = queue.Queue()

    # Start monitors
    print("[main] starting file integrity monitor...")
    start_file_integrity_thread(stop_event, poll_interval=30)
    print("[main] starting logs monitor...")
    start_logs_thread(stop_event)
    print("[main] starting user activity monitor...")
    start_user_activity_thread(stop_event, sample_q)

    # ML Detector
    detector = MLDetector()

    # keep collecting and scoring
    print("[main] entering main loop. Press Ctrl-C to stop.")
    try:
        while not stop_event.is_set():
            try:
                feat = sample_q.get(timeout=1)
            except queue.Empty:
                time.sleep(0.1)
                continue
            # Add as training sample initially until model trained
            if not detector.trained:
                detector.add_training_sample(feat)
                print("[main] collected training sample", len(detector.training_data))
                continue
            # Score
            score, is_anomaly = detector.score(feat)
            # store
            import json
            from database import insert_feature
            insert_feature(json.dumps(feat), score, is_anomaly)
            if is_anomaly:
                msg = f"Anomalous user activity detected. score={score:.4f} features={feat}"
                alert_console("ml_detector", "HIGH", msg)
                if False:
                    alert_email("HIDS anomaly", msg)
            else:
                print("[main] normal sample score", score)
    finally:
        stop_event.set()
        print("[main] exiting.")

if __name__ == "__main__":
    main()
