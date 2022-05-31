import pandas as pd
import argparse
import os
import yaml
import json

from utils import get_image_data_df


class Stats:
    def __init__(self, data_path, out_file, params):
        self.data_path = data_path
        self.data_file = os.path.join(data_path, params["output_datafile"])
        self.df = pd.read_csv(self.data_file)
        self.out_file = out_file
        self.labels = params["labels"]

    def run(self):
        stats_df = self.df.describe()
        desired_stats = ["mean", "std", "min", "max"]
        col_stats = stats_df.loc[desired_stats].to_json(orient="columns")
        col_stats = json.loads(col_stats)

        cat_cols = self.df.select_dtypes(object).drop("Path", axis=1).columns.tolist()
        cat_cols = list(set(cat_cols + self.labels))
        cat_stats = {}
        for col in cat_cols:
            dist = (self.df[col].value_counts() / len(self.df)).to_json(
                orient="columns"
            )
            dist = json.loads(dist)
            cat_stats[col] = dist

        col_stats.update(cat_stats)

        img_data = get_image_data_df(self.df, self.data_path).describe()
        pixel_cols = ["min", "max", "mean", "std"]
        cols_rename = {col: "pixels_" + col for col in pixel_cols}
        img_data = img_data.rename(cols_rename, axis=1)
        img_stats = img_data.loc[desired_stats].to_json(orient="columns")
        img_stats = json.loads(img_stats)
        img_stats["channels"] = 1

        stats = {
            "size": len(self.df),
            "images statistics": img_stats,
            "column statistics": col_stats,
            "labels": self.labels,
        }
        with open(self.out_file, "w") as f:
            yaml.dump(stats, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_path", "--data-path", type=str, required=True, help="prepared data path"
    )
    parser.add_argument(
        "--params_file",
        "--params-file",
        type=str,
        required=True,
        help="Configuration file for the data-preparation step",
    )
    parser.add_argument(
        "--out_path",
        "--out-path",
        type=str,
        required=True,
        help="path to store statistics data",
    )
    args = parser.parse_args()
    with open(args.params_file, "r") as f:
        params = yaml.full_load(f)

    stats_path = args.out_path

    checker = Stats(args.data_path, stats_path, params)
    checker.run()
