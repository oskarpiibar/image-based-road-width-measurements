import pandas as pd
import numpy as np


def map_measured_to_truth(truth_data_df, measured_data_df):
    track_length = 5148 # length for the Nurburgring GP track
    truth_data_df = truth_data_df.copy()

    # Create normalized track position
    truth_data_df['track_pos'] = np.linspace(0, 1, len(truth_data_df), endpoint=False)

    results = []
    for _, row in measured_data_df.iterrows():
        car_lap_pos = row['lap_position']

        # Closest index in truth track
        i_closest = (truth_data_df['track_pos'] - car_lap_pos).abs().idxmin()
        truth_row = truth_data_df.iloc[i_closest]

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
            'filename': row['filename'],
            'truth_left_rel_width': truth_left_rel_width,
            'truth_right_rel_width': truth_right_rel_width,
            'truth_width': truth_width
        })

    return pd.DataFrame(results)
