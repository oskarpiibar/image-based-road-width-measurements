import os
import pandas as pd

import os
import pandas as pd


def compare_images_with_csv(csv_path, image_folder):
    df = pd.read_csv(csv_path)
    valid_filenames = set(df["image_filename"].dropna().astype(str))

    all_images = [f for f in os.listdir(image_folder) if f.endswith(".png")]

    missing_in_folder = valid_filenames - set(all_images)
    extra_in_folder = set(all_images) - valid_filenames

    print(f"Images expected by CSV       : {len(valid_filenames)}")
    print(f"Images actually in folder    : {len(all_images)}")
    print(f"Missing images (only in CSV) : {len(missing_in_folder)}")
    print(f"Extra images (not in CSV)    : {len(extra_in_folder)}")

    return missing_in_folder, extra_in_folder
