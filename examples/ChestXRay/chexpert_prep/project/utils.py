import os
from PIL import Image
import numpy as np


def get_image_data_df(df, data_path):
    img_df = df.apply(
        lambda x: get_image_data(x["Path"], data_path), axis=1, result_type="expand"
    )
    img_df = img_df.rename(
        {0: "width", 1: "height", 2: "min", 3: "max", 4: "mean", 5: "std"}, axis=1
    )
    return img_df


def get_image_data(img_path, data_path):
    img_path = os.path.join(data_path, img_path)
    with Image.open(img_path) as im:
        img = np.array(im)
        w, h = img.shape
        min_val = img.min()
        max_val = img.max()
        mean_val = img.mean()
        std_val = img.std()

    return [w, h, min_val, max_val, mean_val, std_val]
