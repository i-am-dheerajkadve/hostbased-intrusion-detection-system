# config.py
import os

# Paths
LOG_FILES = [
    "/var/log/auth.log",   # Debian/Ubuntu
    "/var/log/syslog"      # Debian/Ubuntu
]

# Directory/paths to watch for file integrity (choose a subset for demonstration)
# Be careful: watching whole '/' is heavy. Use important dirs like /etc, /home/<user>
WATCH_DIRS = [
    "/etc",               # system configuration dir (recommended)
    # "/home/yourusername" # optionally uncomment
]

DB_PATH = os.path.expanduser("~ /root/hids_events.db")

# How often (seconds) to sample user activity features
USER_ACTIVITY_INTERVAL = 10

# How many samples before first ML model training
INITIAL_TRAIN_SAMPLES = 100

# IsolationForest hyperparams
IF_PARAMS = {
    "n_estimators": 100,
    "contamination": 0.01,
    "random_state": 42
}

# Email alerting (optional) - fill if you want SMTP alerts
SMTP = {
    "enabled": True,
    "server": "smtp.gmail.com",
    "port": 587,
    "username": "dheerajeducation892@gmail.com",
    "password": "ybgf hqkr rdmt ppoh",
    "from_addr": "dheerajeducation892@gmail.com",
    "to_addrs": ["dheerajkadve@gmail.com"]
}
