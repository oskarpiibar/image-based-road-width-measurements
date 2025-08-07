import os
import csv
from dataGathering import car_data

# === State ===
csv_created = False
csv_file = None
csv_writer = None
last_logged_ts = None
APP_NAME = 'image_capture'


def acMain(ac_version):
    global csv_created, csv_file, csv_writer


    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Create timestamped CSV
    session_file = "session_name.txt"
    with open(session_file, "r") as f:
        session_name = f.read().strip()

    filepath = os.path.join(data_dir, session_name + ".csv")
    csv_file = open(filepath, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['timestamp', 'lap_position', 'pos_x', 'pos_y', 'image_filename'])

    csv_created = True
    return APP_NAME


def acUpdate(deltaT):
    global csv_writer, csv_created, last_logged_ts

    lap_pos = car_data.get_lap_position()
    x, y = car_data.get_world_location()

    if not csv_created:
        return

    ts_file = "last_image_timestamp.txt"

    if not os.path.exists(ts_file):
        return

    try:
        with open(ts_file, 'r') as f:
            ts_str = f.read().strip()
            if not ts_str:
                return
            ts = int(ts_str)
    except:
        return

    if ts == last_logged_ts:
        return  # Already logged this one

    last_logged_ts = ts

    image_filename = "frame_{0}.png".format(ts)
    csv_writer.writerow([ts, lap_pos, x, y, image_filename])
    csv_file.flush()


def acShutdown():
    global csv_file
    if csv_file is not None:
        csv_file.close()
