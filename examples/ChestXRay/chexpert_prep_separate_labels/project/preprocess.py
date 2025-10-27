from PIL import Image
import numpy as np
import pandas as pd
from tqdm import tqdm
import os
import yaml
import argparse
import inspect
import importlib
from shutil import copytree
import torchxrayvision as xrv
import torchvision


class Preprocessor:
    def __init__(
        self, img_path, csv_path, params_file, output_path, output_labels_path
    ):
        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)
        self.img_path = img_path
        self.csv_path = csv_path
        self.output_path = output_path
        self.output_csv_path = os.path.join(output_path, self.params["output_datafile"])
        self.output_labels_csv_path = os.path.join(
            output_labels_path, self.params["output_labelsfile"]
        )

    def run(self):
        # Before any wrangling of the data, let's make sure the library identifies
        # the format
        transform = torchvision.transforms.Compose(
            [xrv.datasets.XRayCenterCrop(), xrv.datasets.XRayResizer(224)]
        )
        data = None
        print(self.csv_path)
        for name, dset in inspect.getmembers(
            importlib.import_module("torchxrayvision.datasets"), inspect.isclass
        ):
            if "_Dataset" in name:
                try:
                    data = dset(
                        self.img_path,
                        self.csv_path,
                        views=["PA", "AP"],
                        transform=transform,
                    )
                    print(f"{name} format recognized")
                    break
                except:
                    continue

        if data is None:
            print("A dataset format could not be identified for the provided paths")
            exit()

        # create imgs directory
        imgs_path = os.path.join(self.output_path, self.params["output_imagepath"])
        if not os.path.exists(imgs_path):
            os.mkdir(imgs_path)

        # iterate over the Dataset and write images using the idx for name and
        # the csv with the path of the image and the labels
        datarows = []

        # In some cases, images are missing which will throw an error
        # For this, we need to iterate manually and escape those cases
        n_rows = len(data)

        with tqdm(total=n_rows) as pbar:
            for i in range(n_rows):
                try:
                    row = data[i]
                except FileNotFoundError as e:
                    pbar.update(1)
                    continue

                idx = row["idx"]
                labels = row["lab"].tolist()
                img = row["img"].squeeze()
                img_filename = f"{idx}.jpg"
                img_path = os.path.join(imgs_path, img_filename)
                csv_img_path = os.path.join(
                    self.params["output_imagepath"], img_filename
                )
                datarow = [csv_img_path] + labels
                datarows.append(datarow)

                # torchxrayvision does some weird normalization that can't be stored
                # in normal image formats. Let's undo that process
                img = ((((img / 1024) + 1) / 2) * 255).round().astype(np.uint8)
                img = Image.fromarray(img.squeeze())
                img.save(img_path)
                pbar.update(1)

        columns = ["Path"] + data.pathologies
        prepared_df = pd.DataFrame(data=datarows, columns=columns)
        filtered_cols = ["Path"] + self.params["labels"]
        data_df = prepared_df["Path"]
        labels_df = prepared_df[filtered_cols]
        data_df.to_csv(self.output_csv_path, index=False)
        labels_df.to_csv(self.output_labels_csv_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--img_path",
        "--img-path",
        type=str,
        required=True,
        help="Location of images",
    )
    parser.add_argument(
        "--csv_path",
        "--csv-path",
        type=str,
        required=True,
        help="Location of dataset csv",
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
    parser.add_argument(
        "--output_labels_path",
        "--output-labels-path",
        type=str,
        required=True,
        help="Location to store the prepared labels",
    )
    args = parser.parse_args()
    for arg in vars(args):
        setattr(args, arg, getattr(args, arg).replace("'", ""))
    preprocessor = Preprocessor(
        args.img_path,
        args.csv_path,
        args.params_file,
        args.output_path,
        args.output_labels_path,
    )
    preprocessor.run()
