import pandas as pd
import argparse
import os
import yaml

from utils import get_image_data_df


class Checker:
    def __init__(self, data_path, data_file):
        self.data_path = data_path
        self.data_file = os.path.join(data_path, data_file)
        self.df = pd.read_csv(self.data_file)

    def run(self):
        self.__check_na()
        self.__check_images_data()

    def __check_na(self):
        na_series = self.df.isna().sum()
        na_cols = ", ".join(na_series[na_series != 0].index)
        assert na_series.sum() == 0, f"Some columns contain null values: {na_cols}"

    def __check_images_data(self):
        img_data = get_image_data_df(self.df, self.data_path)
        assert img_data["width"].min() >= 320, "Image width is less than 320"
        assert img_data["height"].min() >= 320, "Image width is less than 320"
        assert img_data["min"].min() >= 0, "Image pixel range goes below 0"
        assert (
            img_data["max"].max() > 1
        ), "Image pixel is in float format. 8 byte format expected"
        assert img_data["max"].max() <= 255, "Image pixel range goes beyond 255"


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
    args = parser.parse_args()
    with open(args.params_file, "r") as f:
        params = yaml.full_load(f)

    checker = Checker(args.data_path, params["output_datafile"])
    checker.run()
