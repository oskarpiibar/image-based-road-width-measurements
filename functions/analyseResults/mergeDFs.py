def merge_dfs(main_df, extra_df):
    # Perform inner join on 'filename' and keep extra columns at the end
    df_merged = main_df.merge(extra_df, how='inner', on='filename')

    # Reorder to append new columns from df_extra to the end
    original_columns = list(main_df.columns)
    new_columns = [col for col in df_merged.columns if col not in original_columns]
    df_merged = df_merged[original_columns + new_columns]

    return df_merged
