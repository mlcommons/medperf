import pandas as pd
from shutil import copyfile
import os
import yaml
import argparse


class Preprocessor:
    def __init__(self, data_path, labels_path, params_file, output_path):
        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)
        self.data_path = data_path
        self.output_path = output_path
        self.data_csv_path = os.path.join(data_path, self.params["input_datafile"])
        self.output_csv_path = os.path.join(output_path, self.params["output_datafile"])

    def run(self):
        df = pd.read_csv(self.data_csv_path)
        img_path_lists = df["Path"].str.split("/")
        df["Path"] = self.data_path + os.sep + img_path_lists.str[1:].str.join("/")

        # create imgs directory
        imgs_path = os.path.join(self.output_path, self.params["output_imagepath"])
        if not os.path.exists(imgs_path):
            os.mkdir(imgs_path)

        # Relate current path to destination path
        imgs_df = df["Path"].copy()
        dest = self.params["output_imagepath"] + os.sep + img_path_lists.str[2] + ".jpg"
        dest = dest.rename("Destination")
        imgs_df = pd.concat([imgs_df, dest], axis=1)
        imgs_df["Destination"] = self.output_path + os.sep + imgs_df["Destination"]

        # Copy images to destination path
        imgs_df.apply(lambda x: copyfile(x["Path"], x["Destination"]), axis=1)

        # Point dataframe to destination paths
        df["Path"] = dest

        # Impute NA's
        df["AP/PA"].fillna(df["AP/PA"].mode()[0], inplace=True)

        # Store preprocessed data
        df.to_csv(self.output_csv_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_path",
        "--data-path",
        type=str,
        required=True,
        help="Location of chexpert dataset",
    )
    parser.add_argument(
        "--labels_path",
        "--labels-path",
        type=str,
        required=True,
        help="chexpert labels file. csv expected",
    )
    parser.add_argument(
        "--params_file",
        "--params-file",
        type=str,
        required=True,
        help="Configuration file for the data-preparation step",
    )
    parser.add_argument(
        "--output_path",
        "--output-path",
        type=str,
        required=True,
        help="Location to store the prepared data",
    )
    args = parser.parse_args()
    preprocessor = Preprocessor(
        args.data_path, args.labels_path, args.params_file, args.output_path
    )
    preprocessor.run()
