import json
import os


def load_processed_timestamps(processed_log):
    if os.path.exists(processed_log):
        with open(processed_log, "r") as f:
            return set(json.load(f))
    return set()


def save_processed_timestamps(processed_log, timestamps):
    with open(processed_log, "w") as f:
        json.dump(list(timestamps), f)
