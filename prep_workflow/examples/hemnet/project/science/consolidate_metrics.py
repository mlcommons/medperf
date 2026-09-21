import pandas as pd
import os
from mod_constants import OUTPUT_PATH, TEMP_DATA_PATH, PERFORMANCE_DF

if __name__ == "__main__":

    final_df = pd.DataFrame()

    slide_subidrs = [subdir for subdir in os.listdir(TEMP_DATA_PATH)]

    for slide_subdir in slide_subidrs:
        full_subdir = TEMP_DATA_PATH.joinpath(slide_subdir)
        if not os.path.isdir(full_subdir):
            continue
        elif PERFORMANCE_DF not in os.listdir(full_subdir):
            print(
                f"Performance data not found for slide prefix {slide_subdir}. Will not be included in final metrics."
            )
            continue

        df_path = os.path.join(full_subdir, PERFORMANCE_DF)
        tmp_df = pd.read_csv(df_path, encoding="utf-8", index_col=0)
        final_df = pd.concat([final_df, tmp_df], axis=0)
        print(f"tmp_df=\n{tmp_df}")
        print(f"final_df=\n{final_df}")
        print("------------------------------------")

    final_path = OUTPUT_PATH.joinpath(PERFORMANCE_DF)
    final_df.to_csv(final_path)
