"""
Validate model predictions output for BraTS-MEN-RT
and BraTS-Path 2024.
"""

import os
from glob import glob

import numpy as np
import pandas as pd
import SimpleITK as sitk
import yaml
from cnb_tools import validation_toolkit as vtk


def check_image_dims(path):
    base_size = np.array([182, 218, 182])
    image = sitk.ReadImage(path)
    size_array = np.array(image.GetSize())
    assert (base_size == size_array).all(), (
        "Image size is not [182, 218, 182] for " + path
    )


def _check_counts(pred, gold):
    if len(pred) != len(gold):
        raise ValueError("Predictions number don't match labels")

    if sorted(pred) != sorted(gold):
        raise ValueError("Predictions don't match submission criteria")


def check_for_postop(labels, predictions):
    label_id_len = len("xxxxx-xxx-seg.nii.gz")
    subjectids = [
        label[-label_id_len:].replace("-seg", "") for label in os.listdir(labels)
    ]

    pred_id_len = len("xxxxx-xxx.nii.gz")
    pred_subjectids = [pred[-pred_id_len:] for pred in os.listdir(predictions)]
    _check_counts(pred_subjectids, subjectids)

    for pred in os.listdir(predictions):
        check_image_dims(os.path.join(predictions, pred))


def check_for_radiotherapy(labels, predictions):
    label_id_len = len("xxxx-x_gtv.nii.gz")
    subjectids = [
        label[-label_id_len:].replace("_gtv", "") for label in os.listdir(labels)
    ]
    pred_id_len = len("xxxx-x.nii.gz")
    pred_subjectids = [pred[-pred_id_len:] for pred in os.listdir(predictions)]
    _check_counts(pred_subjectids, subjectids)


def check_for_pathology(parent):
    pred_file = glob(os.path.join(parent, "*.csv"))
    if len(pred_file) != 1:
        raise ValueError("There should only be one predictions CSV file")

    try:
        pred = pd.read_csv(pred_file[0], usecols=["SubjectID", "Prediction"])
    except ValueError as exc:
        raise ValueError(
            "Predictions file should contain two columns: `SubjectID` "
            "and `Prediction` (case-sensitive)"
        ) from exc

    if vtk.check_duplicate_keys(pred["SubjectID"]) != "":
        raise ValueError("Duplicate SubjectIDs found")

    if vtk.check_values_range(pred["Prediction"], min_val=0, max_val=5) != "":
        raise ValueError("`Prediction` should be integers between 0 and 5")

    if not all(pred["SubjectID"].str.contains(r"BraTSPath_\w+_\d{7}\.png$")):
        raise ValueError(
            "'SubjectID' values do not contain the filenames in the dataset"
        )


def calculate_metrics(labels, predictions, parameters, output_path):
    task = parameters["task"]

    if task == "segmentation":
        check_for_postop(labels, predictions)
    elif task == "segmentation-radiotherapy":
        check_for_radiotherapy(labels, predictions)
    else:
        check_for_pathology(predictions)

    with open(output_path, "w") as f:
        yaml.dump({"valid": True}, f)
