import os
import pandas as pd
from functions.imageProcessing.imageProcessing import batch_process_folder
from functions.analyseResults import mergeDFs, keepImagesWithCsvData, groundTruthMeasuredDataRelation, \
    analyse_results
from functions.processedTimestampsLog.processed_timestamps_log import load_processed_timestamps, \
    save_processed_timestamps
from config import DATA, PROCESSED_IMAGES, CSV, IMAGES, TRUTH_DATA, PROCESSED_LOG, TEMPLATE_FOLDER

if __name__ == '__main__':
    # Takes the latest folder of images
    latest_folder = sorted(os.listdir(os.path.join(DATA, IMAGES)))[-1]

    # Extract the timestamp
    timestamp = latest_folder.replace("images_", "")

    # When the latest folder is not to be used:
    # latest_folder = images_13_43_39_08_08_2025
    # timestamp = 13_43_39_08_08_2025

    # ---------------- SETUP PATHS --------------------------------
    timestamp_csv_folder = os.path.join(DATA, CSV, timestamp)
    timestamp_processed_images_folder = os.path.join(DATA, PROCESSED_IMAGES, timestamp)
    processed_timestamps_log_folder = os.path.join(DATA, PROCESSED_LOG)
    # ---------------- SETUP PATHS --------------------------------

    # ---------------- ENSURE PATH EXISTS --------------------------------
    os.makedirs(timestamp_csv_folder, exist_ok=True)
    os.makedirs(timestamp_processed_images_folder, exist_ok=True)
    os.makedirs(processed_timestamps_log_folder, exist_ok=True)
    # ---------------- ENSURE PATH EXISTS --------------------------------

    # ---------------- SETUP CSVs --------------------------------
    processed_timestamps_log = os.path.join(processed_timestamps_log_folder, "processed_timestamps.json")
    measured_data_csv = os.path.join(timestamp_csv_folder, "measured_data.csv")
    game_collected_data_csv = os.path.join(timestamp_csv_folder, timestamp + ".csv")
    truth_csv = os.path.join(DATA, TRUTH_DATA, "ks_nurburgring-layout_gp_a.csv")
    merged_datasets_csv = os.path.join(timestamp_csv_folder, "merged_datasets.csv")
    results_csv = os.path.join(timestamp_csv_folder, "results.csv")
    road_type_grouped_results_csv = os.path.join(timestamp_csv_folder, "road_type_results.csv")
    # ---------------- SETUP CSVs --------------------------------

    # ---------------- CREATE DFs --------------------------------
    game_df = pd.read_csv(game_collected_data_csv)
    truth_df = pd.read_csv(truth_csv)
    # ---------------- CREATE DFs --------------------------------

    # ---------------- RUNNING FUNCTIONS --------------------------------
    processed_timestamps = load_processed_timestamps(processed_timestamps_log)

    if timestamp not in processed_timestamps:
        print(f"\nRunning one-time image processing function (batch_process_folder) for {timestamp}\n")
        # Run the image processing, which also saves the measured data to the "measured_data_csv"
        batch_process_folder(latest_folder, timestamp_processed_images_folder, TEMPLATE_FOLDER,
                             measured_data_csv)
        print("Finished processing the gathered images\n")

        processed_timestamps.add(timestamp)
        save_processed_timestamps(processed_timestamps_log, processed_timestamps)
    else:
        print(f"\nSkipping image processing function (batch_process_folder) for {timestamp} (already processed)\n")

    measured_df = pd.read_csv(measured_data_csv)

    # Checks if there are collected data points that do not have images and the other way around
    missing_images, missing_data_points = keepImagesWithCsvData.compare_images_with_csv(game_collected_data_csv,
                                                                                        latest_folder)

    # Make sure to delete the data points that do not have images and the other way around
    print(f"Missing images (only in CSV file): {0 if len(missing_images) == 0 else missing_images}")
    print(f"Extra images (not in CSV file): {0 if len(missing_data_points) == 0 else missing_data_points}\n")

    # Merge together the game gathered data and the measured datasets
    game_collected_measured_data_combined_df = mergeDFs.merge_dfs(game_df, measured_df)
    print("Merged the game collected and measured data\n")

    # Mapping the measured and the truth data and combining them into one csv file
    truth_measured_combined_df = groundTruthMeasuredDataRelation.map_measured_to_truth(
        truth_df,
        game_collected_measured_data_combined_df,
    )
    print("The mapping of measured and truth data was successful\n")

    # Merge together previously merged dataset and the dataset with our measured racetrack information
    final_df_before_data_analysing = mergeDFs.merge_dfs(truth_measured_combined_df, measured_df)
    print("Final merge successfully completed. The data will now be analyzed and results will be printed out.\n")

    final_df_before_data_analysing.to_csv(merged_datasets_csv, index=False)

    # Begin the results calculation process
    analyse_results.evaluate_predictions(merged_datasets_csv, results_csv)

    user_ready = input(
        "\nHave you completed the road type grouping described in the README and as demonstrated at "
        "the top of the analyze_results.py file, needed for road-type evaluation? (y/n): ").strip().lower()
    if user_ready == "y":
        # For debugging purposes the try-except block can be commented
        try:
            analyse_results.evaluate_by_road_type(results_csv)
            analyse_results.generate_grouped_results(results_csv, road_type_grouped_results_csv)
            print("\nRoad-type evaluation and grouped results generated successfully.\n")
        except:
            print("\nAn error occurred when generating the grouped results. Check for any errors in your work.\n")
    else:
        print("\nSkipping road-type evaluation and grouped results until manual work is complete."
              "Once you have finished re-run the main.py code.\n")

    print("All the code has successfully finished running. The results can be in more detail seen in "
          "the results.csv file.\n")
