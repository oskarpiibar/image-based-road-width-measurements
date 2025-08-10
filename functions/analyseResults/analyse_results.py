from sklearn.metrics import mean_absolute_percentage_error, r2_score
from scipy.stats import pearsonr
import pandas as pd

# === Needs to be defined manually, look at the example below. First image excluded
# STRAIGHTS = [(2, 22), (51, 90), (101, 160), (230, 240), (271, 300), (371, 457),
#              (480, 532), (554, 597), (609, 622), (644, 692), (714, 787), (801, 835), (856, 896)]
# RIGHT_TURNS = [(23, 47), (186, 193), (262, 270), (356, 370), (458, 478), (540, 553),
#                (623, 643), (693, 713), (794, 800), (836, 855)]
# LEFT_TURNS = [(206, 227), (242, 258), (328, 346), (533, 548), (598, 608), (788, 793)]

STRAIGHTS = [(2, 8), (16, 19)]
RIGHT_TURNS = [(9, 15)]
LEFT_TURNS = [] # <- in the occurrence of no left turns

meter_to_pixel_ratio = 0.01249999999999986
ground_truth_ratio = 0.018871954437029596


def expand_ranges(ranges):
    indices = set()
    for start, end in ranges:
        indices.update(range(start - 1, end))
    return indices


def evaluate_predictions(input_csv_path, output_csv, pred_col='road_width', truth_col='truth_width'):
    df = pd.read_csv(input_csv_path)
    df_full = df.copy()

    # Removes the first row as the first row equals to the truth data.
    # If that's not the case comment the next line and uncomment the df_analysis = df.copy line
    # df_analysis = df.iloc[1:].copy()
    df_analysis = df.copy()

    # Add per-row MAPE (absolute percentage error)
    df_analysis["MAPE"] = (abs(df_analysis[pred_col] - df_analysis[truth_col]) / df_analysis[truth_col]).astype(float)

    df_analysis = df_analysis[df_analysis["MAPE"] < 0.45]

    y_pred = df_analysis[pred_col].astype(float).values
    y_true = df_analysis[truth_col].astype(float).values

    # Overall metrics with the ground truth ratio
    mape = mean_absolute_percentage_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    corr, _ = pearsonr(y_true, y_pred)

    print("Ground truth ratio metrics\n")
    print(f"MAPE width: {mape:.4f}")
    print(f"R-squared width: {r2:.4f}")
    print(f"Pearson’s correlation width: {corr:.4f}\n")

    # Calculate relative distance difference from measured width
    df_analysis["rel_dist_diff_from_width"] = df_analysis["road_width"] - \
                                              (df_analysis["distance_right"] + df_analysis["distance_left"])


    #Transfer to the other width with the calculated
    df_analysis["other_width"] = df_analysis["road_width"] * meter_to_pixel_ratio / ground_truth_ratio
    df_analysis["MAPE_other"] = (abs(df_analysis["other_width"] - df_analysis[truth_col]) / df_analysis[truth_col]).astype(float)

    y_pred_other = df_analysis["other_width"].astype(float).values

    mape_other = mean_absolute_percentage_error(y_true, y_pred_other)
    r2_other = r2_score(y_true, y_pred_other)
    corr_other, _ = pearsonr(y_true, y_pred_other)

    print("Calculated ratio variable metrics\n")
    print(f"MAPE calculated ratio var: {mape_other:.4f}")
    print(f"R-squared calculated ratio var: {r2_other:.4f}")
    print(f"Pearson’s correlation calculated ratio var: {corr_other:.4f}\n")


    # Trial with a random ratio variable (performs really good)
    df_analysis["trial"] = df_analysis["road_width"] * 0.0160 / 0.018871954437029596
    df_analysis["MAPE_trial"] = (
                abs(df_analysis["trial"] - df_analysis[truth_col]) / df_analysis[truth_col]).astype(float)

    y_pred_trial = df_analysis["trial"].astype(float).values

    mape_trial = mean_absolute_percentage_error(y_true, y_pred_trial)
    r2_trial = r2_score(y_true, y_pred_trial)
    corr_trial, _ = pearsonr(y_true, y_pred_trial)

    print("Trial ratio variable metrics\n")
    print(f"MAPE width trial ratio var: {mape_trial:.4f}")
    print(f"R-squared width trial ratio var: {r2_trial:.4f}")
    print(f"Pearson’s correlation width trial ratio var: {corr_trial:.4f}\n")

    # Relative position MAPE
    df_analysis["pred_rel_pos"] = df_analysis["distance_left"] + df_analysis["distance_right"]
    df_analysis["true_rel_pos"] = df_analysis["truth_left_rel_width"] + df_analysis["truth_right_rel_width"]

    df_analysis["rel_pos_mape"] = (
            abs(df_analysis["pred_rel_pos"] - df_analysis["true_rel_pos"]) / df_analysis["true_rel_pos"]
    ).astype(float)

    y_pred_rel = df_analysis["pred_rel_pos"].astype(float).values
    y_true_rel = df_analysis["true_rel_pos"].astype(float).values

    mape_rel = mean_absolute_percentage_error(y_true_rel, y_pred_rel)
    r2_rel = r2_score(y_true_rel, y_pred_rel)
    corr_rel, _ = pearsonr(y_true_rel, y_pred_rel)

    print("Relative distance metrics\n")
    print(f"MAPE relative distance: {mape_rel:.4f}")
    print(f"R-squared relative distance: {r2_rel:.4f}")
    print(f"Pearson’s correlation relative distance: {corr_rel:.4f}\n")

    df_full.loc[df_analysis.index, "MAPE"] = df_analysis["MAPE"]
    df_full.loc[df_analysis.index, "rel_dist_diff_from_width"] = df_analysis["rel_dist_diff_from_width"]
    df_full.loc[df_analysis.index, "other_width"] = df_analysis["other_width"]
    df_full.loc[df_analysis.index, "MAPE_other"] = df_analysis["MAPE_other"]
    df_full.loc[df_analysis.index, "rel_pos_mape"] = df_analysis["rel_pos_mape"]

    # Save updated CSV with row-wise MAPE
    df_full.to_csv(output_csv, index=False)


def evaluate_subset(df, indices, pred_col='road_width', truth_col='truth_width'):
    subset = df.iloc[list(indices)].copy()
    y_true = subset[truth_col].astype(float)
    y_pred = subset[pred_col].astype(float)

    mape = mean_absolute_percentage_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    corr, _ = pearsonr(y_true, y_pred)
    return mape, r2, corr


def evaluate_by_road_type(csv_path):
    df = pd.read_csv(csv_path)

    df_analysis = df.iloc[1:].copy()

    groups = {
        "Straight": expand_ranges(STRAIGHTS),
        "Right Turn": expand_ranges(RIGHT_TURNS),
        "Left Turn": expand_ranges(LEFT_TURNS),
    }

    for name, indices in groups.items():
        valid_indices = [i for i in indices if 0 <= i < len(df_analysis)]
        if not valid_indices:
            print(f"\n=== {name} ===")
            print("No data available for this group.\n")
            continue

        mape, r2, corr = evaluate_subset(df_analysis, valid_indices)
        print(f"\n=== {name} ===")
        print(f"MAPE: {mape:.4f}")
        print(f"R-squared: {r2:.4f}")
        print(f"Pearson correlation: {corr:.4f}\n")


def generate_grouped_results(input_csv_path, output_csv_path):
    df = pd.read_csv(input_csv_path)

    # Skip first row as per convention
    df = df.iloc[1:].copy()

    # Map of road type to expanded indices
    groups = {
        "straight": expand_ranges(STRAIGHTS),
        "right": expand_ranges(RIGHT_TURNS),
        "left": expand_ranges(LEFT_TURNS),
    }

    # Assign road type per index
    road_types = ["unknown"] * len(df)
    for road_type, indices in groups.items():
        for idx in indices:
            if idx < len(df):  # Ensure index is within bounds
                road_types[idx] = road_type

    df["road_type"] = road_types

    # Filter to only known types
    df_filtered = df[df["road_type"] != "unknown"]

    # Select and reorder columns
    output_df = df_filtered[[
        "filename",
        "road_type",
        "truth_width",
        "truth_left_rel_width",
        "truth_right_rel_width",
        "road_width",
        "distance_left",
        "distance_right",
        "MAPE"
    ]].sort_values("filename")

    # Save to single output file
    output_df.to_csv(output_csv_path, index=False)
