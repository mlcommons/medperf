from torch.utils.data import Dataset
import numpy as np
import collections
import os
import pprint
import pandas as pd
from skimage.io import imread, imsave
import random

default_pathologies = [
    "Atelectasis",
    "Consolidation",
    "Infiltration",
    "Pneumothorax",
    "Edema",
    "Emphysema",
    "Fibrosis",
    "Effusion",
    "Pneumonia",
    "Pleural_Thickening",
    "Cardiomegaly",
    "Nodule",
    "Mass",
    "Hernia",
    "Lung Lesion",
    "Fracture",
    "Lung Opacity",
    "Enlarged Cardiomediastinum",
]


def normalize(img, maxval, reshape=False):
    """Scales images to be roughly [-1024 1024]."""

    if img.max() > maxval:
        raise Exception(
            "max image value ({}) higher than expected bound ({}).".format(
                img.max(), maxval
            )
        )

    img = (2 * (img.astype(np.float32) / maxval) - 1.0) * 1024

    if reshape:
        # Check that images are 2D arrays
        if len(img.shape) > 2:
            img = img[:, :, 0]
        if len(img.shape) < 2:
            print("error, dimension lower than 2 for image")

        # add color channel
        img = img[None, :, :]

    return img


class Dataset:
    def __init__(self):
        pass

    def totals(self):
        counts = [
            dict(collections.Counter(items[~np.isnan(items)]).most_common())
            for items in self.labels.T
        ]
        return dict(zip(self.pathologies, counts))

    def __repr__(self):
        pprint.pprint(self.totals())
        return self.string()

    def check_paths_exist(self):
        # if self.imagezipfile is not None:

        if not os.path.isdir(self.imgpath):
            raise Exception("imgpath must be a directory")
        if not os.path.isfile(self.csvpath):
            raise Exception("csvpath must be a file")


class XRVDataset(Dataset):
    def __init__(self, datapath, transform=None, seed=0):
        super(XRVDataset, self).__init__()
        np.random.seed(seed)
        self.imgpath = datapath
        self.csvpath = os.path.join(datapath, "data.csv")
        self.transform = transform
        self.pathologies = [
            "Enlarged Cardiomediastinum",
            "Cardiomegaly",
            "Lung Opacity",
            "Lung Lesion",
            "Edema",
            "Consolidation",
            "Pneumonia",
            "Atelectasis",
            "Pneumothorax",
            "Pleural Effusion",
            "Pleural Other",
            "Fracture",
            "Support Devices",
        ]

        self.pathologies = sorted(self.pathologies)

        self.check_paths_exist()
        self.csv = pd.read_csv(self.csvpath)

    def string(self):
        return self.__class__.__name__ + " num_samples={}".format(len(self))

    def __len__(self):
        return len(self.csv)

    def __getitem__(self, idx):

        sample = {}
        sample["idx"] = idx
        sample["Path"] = self.csv["Path"].iloc[idx]
        sample["lab"] = self.csv.drop(["Path"], axis=1).iloc[idx].values

        imgid = self.csv["Path"].iloc[idx]
        img_path = os.path.join(self.imgpath, imgid)
        img = imread(img_path)

        sample["img"] = normalize(img, maxval=255, reshape=True)

        transform_seed = np.random.randint(2147483647)

        if self.transform is not None:
            random.seed(transform_seed)
            sample["img"] = self.transform(sample["img"])

        return sample
