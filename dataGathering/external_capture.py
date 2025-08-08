import atexit
import os
import signal
import sys
import time
import pyautogui
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DATA, IMAGES

# Create session name
now = time.localtime()
session_name = "{:02d}_{:02d}_{:02d}_{:02d}_{:02d}_{:04d}".format(
    now.tm_hour, now.tm_min, now.tm_sec, now.tm_mday, now.tm_mon, now.tm_year
)

# Write session name to file so the plugin can read it
session_name_file = "session_name.txt"
with open(session_name_file, "w") as f:
    f.write(session_name)

# Create screenshot output folder
output_dir = os.path.join(DATA, IMAGES, f"images_{session_name}")
os.makedirs(output_dir, exist_ok=True)

# Path to the timestamp file used for coordination
timestamp_file = "last_image_timestamp.txt"

# === Optional delay before starting ===
print("Waiting 30 seconds before starting capture...")
time.sleep(30)


def cleanup():
    for file in [session_name_file, timestamp_file]:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Deleted temporary file: {file}")
            except Exception as e:
                print(f"Could not delete {file}: {e}")


atexit.register(cleanup)  # Run cleanup on normal exit
signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))  # Handle Ctrl+C
signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))  # Handle terminal kill

# === Screenshot loop ===
print("Saving screenshots to:", output_dir)
while True:
    try:
        ts = round(time.time() * 1000)
        screenshot = pyautogui.screenshot()
        with open(timestamp_file, "w") as f:
            f.write(str(ts))
        filename = f"frame_{ts}.png"
        filepath = f"{output_dir}/{filename}"
        screenshot.save(filepath)

        print("Saved:", filepath, True)
        time.sleep(0.1)

    except Exception as e:
        print("Error:", e)
        time.sleep(0.1)

