import pandas as pd
import numpy as np
import os


def map_measured_to_truth(truth_data_csv, measured_data_csv, output_csv):
    track_length = 5148 # length for the Nurburgring GP track
    files = [f for f in os.listdir(measured_data_csv) if f.endswith('.csv')]
    files.sort()
    latest_file = files[-1] if files else None

    if not latest_file:
        raise FileNotFoundError("No gathered data files found in folder.")

    gathered_data_path = os.path.join(measured_data_csv, latest_file)

    # Load data
    truth_df = pd.read_csv(truth_data_csv)
    gathered_df = pd.read_csv(gathered_data_path)

    # Create normalized track position
    truth_df['track_pos'] = np.linspace(0, 1, len(truth_df), endpoint=False)

    results = []
    for _, row in gathered_df.iterrows():
        car_lap_pos = row['lap_position']

        # Closest index in truth track
        i_closest = (truth_df['track_pos'] - car_lap_pos).abs().idxmin()
        truth_row = truth_df.iloc[i_closest]

        # Distance to raceline
        car_x, car_y = row['pos_x'], row['pos_y']
        raceline_x, raceline_y = truth_row['pos_x'], truth_row['pos_y']
        dist_to_raceline = np.sqrt((car_x - raceline_x)**2 + (car_y - raceline_y)**2)

        # Track width and lateral distances
        truth_width = np.hypot(
            truth_row['left_border_x'] - truth_row['right_border_x'],
            truth_row['left_border_y'] - truth_row['right_border_y']
        )
        truth_left_rel_width = np.hypot(
            truth_row['pos_x'] - truth_row['left_border_x'],
            truth_row['pos_y'] - truth_row['left_border_y']
        )
        truth_right_rel_width = np.hypot(
            truth_row['pos_x'] - truth_row['right_border_x'],
            truth_row['pos_y'] - truth_row['right_border_y']
        )

        results.append({
            'car_x': car_x,
            'car_y': car_y,
            'lap_position': car_lap_pos,
            'closest_track_index': i_closest,
            'calc_track_pos': truth_row['track_pos'],
            'track_pos_diff (m)': abs(car_lap_pos - truth_row['track_pos']) * track_length,
            'track_raceline_x': raceline_x,
            'track_raceline_y': raceline_y,
            'distance_to_raceline': dist_to_raceline,
            'left_border': (float(truth_row['left_border_x']), float(truth_row['left_border_y'])),
            'right_border': (float(truth_row['right_border_x']), float(truth_row['right_border_y'])),
            'filename': row['image_filename'],
            'truth_left_rel_width': truth_left_rel_width,
            'truth_right_rel_width': truth_right_rel_width,
            'truth_width': truth_width
        })

    # Save to file
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_csv, index=False)
    print(f"Saved mapping results to {output_csv}")
