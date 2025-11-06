# ml_detector.py
import json
import numpy as np
import threading
from sklearn.ensemble import IsolationForest
from database import insert_feature, save_model_meta, read_model_meta
from config import IF_PARAMS, INITIAL_TRAIN_SAMPLES
import time
import pickle
import os

MODEL_PATH = os.path.expanduser("~/hids_if_model.pkl")

class MLDetector:
    def __init__(self):
        self.model = None
        self.lock = threading.Lock()
        self.training_data = []
        self.trained = False
        # load existing model if any
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                self.trained = True
                print("[ml_detector] loaded model from disk")
            except Exception as e:
                print("[ml_detector] failed loading model:", e)

    def _save_model(self):
        try:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
            save_model_meta("last_saved", str(time.time()))
        except Exception as e:
            print("[ml_detector] failed saving model:", e)

    def features_to_vector(self, feat):
        # deterministic ordering
        return np.array([
            feat.get("proc_count", 0),
            feat.get("cpu_sum", 0.0),
            feat.get("mem_sum", 0.0),
            feat.get("root_proc_count", 0),
            feat.get("shell_count", 0),
            feat.get("num_users", 0)
        ], dtype=float)

    def add_training_sample(self, feat):
        vec = self.features_to_vector(feat)
        with self.lock:
            self.training_data.append(vec)
            if (not self.trained) and len(self.training_data) >= INITIAL_TRAIN_SAMPLES:
                self.train_model()

    def train_model(self):
        with self.lock:
            X = np.vstack(self.training_data)
            print("[ml_detector] training IsolationForest on", X.shape)
            self.model = IsolationForest(**IF_PARAMS)
            self.model.fit(X)
            self.trained = True
            self._save_model()

    def score(self, feat):
        vec = self.features_to_vector(feat).reshape(1, -1)
        if not self.trained:
            # not trained: return neutral score
            return 0.0, False
        with self.lock:
            score = self.model.decision_function(vec)[0]  # higher -> normal, lower -> anomaly
            pred = self.model.predict(vec)[0]  # -1 anomaly, 1 normal
            is_anomaly = (pred == -1)
            return float(score), bool(is_anomaly)

    def online_update(self, feat):
        # For simple projects, we don't do incremental updates to IsolationForest.
        # Instead we collect more training data and retrain offline when desired.
        pass
