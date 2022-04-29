import os
import shutil
import argparse
import pandas as pd
import numpy as np
import pickle

## plotting
# import cv2

## pydicom suite
import pydicom
from pydicom.data import get_testdata_file
from pydicom import dcmread

## image conversion
from PIL import Image
import nibabel as nib

# import re
from skimage.transform import resize
import time
from PIL import Image
import re


def prepare(path, data_id):
    """Process each dataset based on individual characteristics

    Args:
        path to pull data from 
    """
    # assert type(train) == bool, 'Wrong train/test selection input'

    if train:
        suffix = "_train"
    else:
        suffix = "_test"

    if dataset == "synapse":
        feature_id = re.findall(r"[\w']+", feature_dir)[-3][-4:]
        label_id = re.findall(r"[\w']+", label_dir)[-3][-4:]
        assert feature_id == label_id, "Feature and label mis-match: {0}".format(
            feature_id
        )

        feature_array = load_nifty_data(feature_dir)
        feature_array = rotate_image(feature_array, 1)
        feature_final = np.moveaxis(feature_array, -1, 0)

        label_array = load_nifty_data(label_dir)
        label_array = rotate_image(label_array, 1)
        label_final = np.moveaxis(label_array, -1, 0)

    else:
        feature_id = re.findall(r"[\w']+", feature_dir)[-1][-4:]
        label_id = re.findall(r"[\w']+", label_dir)[-3][-4:]
        assert feature_id == label_id, "Feature and label mis-match: {0}".format(
            feature_id
        )

        feature_array = load_dicom_data(feature_dir)
        feature_array = rotate_image(feature_array, 2, (1, 2))
        feature_final = rotate_image(feature_array, 2, (0, 2))
        # feature_final = np.flip(feature_array, axis=0)
        # feature_final = feature_array

        label_array = load_nifty_data(label_dir)
        label_array = np.transpose(label_array, (2, 0, 1))
        # label_array = rotate_image(label_array, 2)
        # label_final = np.moveaxis(label_array, -1, 0)
        label_tcia = rotate_image(label_array, 1, (1, 2))
        label_final = np.flip(label_tcia, axis=0)
        # label_final = rotate_image(label_array, 2, (0, 2))

    # save_dir = os.path.join(parent_save_folder, dataset + suffix, feature_id)
    print("parent save folder:", parent_save_folder)
    save_dir = os.path.join(parent_save_folder, feature_id)
    # print('saving dir: {0}'.format(save_dir))
    return save_dir, feature_final, label_final


def train_test_split(patient_list, train_rate):
    """
    split the patient into training and testing set
    """
    patient_permute = np.random.permutation(patient_list)
    train_size = int(len(patient_list) * train_rate)
    patient_train = patient_permute[:train_size]
    patient_test = patient_permute[train_size:]
    return patient_train, patient_test


def partition_pickle_data(path, image_patient, target_patient):
    """
    partition data and save partitioned data in pickle format
    
    Args:
        path: path to save pickled files
        image_patient: array of data to pickle
        target_patient: the ground truth value that corresponds to the 2.5D image patient segmentation
        patient_id: patient id number, corresponding to .nifti ID or folder name
    Returns:
        image_names: list of image 2.5D image segmentation arrays
    """
    for n in range(image_patient.shape[0] - 2):
        print("path:", path)
        file_name1 = path + "_" + str(n) + ".npy"
        # identify the three arrays of interest
        pickle_image = image_patient[n : n + 3, :, :]
        # identify the ground truth and append
        target = target_patient[n + 1, :, :]
        # print("file save name:", file_name1)
        pickle_image = np.append(pickle_image, np.expand_dims(target, axis=0), axis=0)
        np.save(file_name1, pickle_image)
    return


def process_label(label, dataset):
    """
    preprocess label data to have the same class
    """
    if dataset == "synapse":
        label[label != 11] = 0
        label[label == 11] = 1
    elif dataset == "task07":
        label[label != 0] = 1
    else:
        pass
    return label


def clip_dicom(image_array):
    image_array[image_array > 240] = 240.0
    image_array[image_array < -160] = -160.0
    image_array = (image_array - np.min(image_array)) / (
        np.max(image_array) - np.min(image_array) + 1e-12
    )
    return image_array


def rotate_image(image_array, degree, axis=(0, 1)):
    image_array = np.rot90(image_array, degree, axis)
    return image_array


def drop_resize(image, resize_dim=256):
    dim_0 = image.shape[0]
    dim_1 = image.shape[1]
    dim_2 = image.shape[2]

    if dim_1 < resize_dim or dim_2 < resize_dim:
        return np.array([])

    if dim_1 == resize_dim and dim_2 == resize_dim:
        resized_image = image
    else:
        resized_image = resize(image, (dim_0, resize_dim, resize_dim))

    return resized_image


def load_nifty_data(path):
    """
    data loading helper for .nii.gz format data
    """
    image = nib.load(path)
    image_array = image.get_fdata()
    return image_array


def load_dicom_data(path):
    """
    data loading helper for .dicom format data
    """
    sub_folders1 = [f for f in os.listdir(path) if not f.startswith(".")]
    assert len(sub_folders1) == 1, "Multiple files found: {0}".format(sub_folders1)
    sub_path1 = os.path.join(path, sub_folders1[0])

    sub_folders2 = [f for f in os.listdir(sub_path1) if not f.startswith(".")]
    assert len(sub_folders2) == 1, "Multiple files found: {0}".format(sub_folders2)
    sub_path2 = os.path.join(sub_path1, sub_folders2[0])
    # print('sub_path2: {0}'.format(sub_path2))

    image_patient = []
    for name in sorted(os.listdir(sub_path2)):
        # print('name of file: {0}'.format(name))
        assert name.split(".")[-1] == "dcm", "Invalid file format in {0}".format(
            os.path.join(sub_path2, name)
        )
        # print(os.path.join(sub_path2, name))
        image_dcm = dcmread(os.path.join(sub_path2, name))
        image_np = image_dcm.pixel_array
        image_patient.append(np.expand_dims(image_np, axis=0))

    image_patient = np.concatenate(image_patient, axis=0)
    # print(image_patient.shape)
    return image_patient


def trim_channel(feature_image):
    """
    trim the empty scans in a patient's full CT scan
    """
    start = 0
    end = feature_image.shape[0] - 1
    while np.mean(feature_image[start, :, :]) == 0:
        start += 1

    while np.mean(feature_image[end, :, :]) == 0:
        end -= 1

    return start, end


def standardize_image(image):
    return (image - np.min(image)) / np.ptp(image)


def debug(feature, label):
    feature_ids = [f.split("_")[0][-7:] for f in feature]
    label_ids = [f.split("_")[0][-7:] for f in label]
    if len(feature_ids) > len(label_ids):
        missing = [i for i in label_ids if i not in feature_ids]
        print("missing label for patients {0}".format(missing))
    else:
        missing = [i for i in feature_ids if i not in label_ids]
        print("missing feature for patients {0}".format(missing))
    return


## new function to include resizing


def dataset_specific_process(
    parent_save_folder, feature_dir, label_dir, dataset, train
):
    assert type(train) == bool, "Wrong train/test selection input"

    if train:
        suffix = "_train"
    else:
        suffix = "_test"

    if dataset == "synapse":
        feature_id = re.findall(r"[\w']+", feature_dir)[-3][-4:]
        label_id = re.findall(r"[\w']+", label_dir)[-3][-4:]
        assert feature_id == label_id, "Feature and label mis-match: {0}".format(
            feature_id
        )
        print("feature dir:", feature_dir)
        feature_array = load_nifty_data(feature_dir)
        feature_array = rotate_image(feature_array, 1)
        feature_final = np.moveaxis(feature_array, -1, 0)

        label_array = load_nifty_data(label_dir)
        label_array = rotate_image(label_array, 1)
        label_final = np.moveaxis(label_array, -1, 0)
    else:
        feature_id = re.findall(r"[\w']+", feature_dir)[-1][-4:]
        label_id = re.findall(r"[\w']+", label_dir)[-3][-4:]
        assert feature_id == label_id, "Feature and label mis-match: {0}".format(
            feature_id
        )

        feature_array = load_dicom_data(feature_dir)
        feature_array = rotate_image(feature_array, 2, (1, 2))
        feature_final = rotate_image(feature_array, 2, (0, 2))
        # feature_final = np.flip(feature_array, axis=0)
        # feature_final = feature_array

        label_array = load_nifty_data(label_dir)
        label_array = np.transpose(label_array, (2, 0, 1))
        # label_array = rotate_image(label_array, 2)
        # label_final = np.moveaxis(label_array, -1, 0)
        label_tcia = rotate_image(label_array, 1, (1, 2))
        label_final = np.flip(label_tcia, axis=0)
        # label_final = rotate_image(label_array, 2, (0, 2))

    save_dir = os.path.join(parent_save_folder, feature_id)
    # save_dir = os.path.join(parent_save_folder, dataset + suffix, feature_id)
    # save_dir = os.path.join(parent_save_folder, feature_id)
    print("saving dir: {0}".format(save_dir))
    return save_dir, feature_final, label_final


def data_preprocess(
    feature_folder, label_folder, dataset, parent_save_folder, train_rate=1
):
    """
    load data into numpy array and store as pickle files
    
    Args:
        feature_folder: directory for target data (train / test)
        label_folder: directory for image folders inside each patient's data
        dataset: dataset name (select between 'synapse', 'task07', 'tcia')
        parent_save_folder: parent directory for data saving
        train_rate:
    Returns:
        image_names: list of image 2.5D image segmentation arrays
        target_names: list of ground truth references
    """

    assert dataset in ["synapse", "task07", "tcia"], "Wrong dataset input"

    processed_train = []
    processed_test = []

    # files = os.listdir(kaggle_folder)
    feature_files = [
        f for f in os.listdir(os.path.join(feature_folder)) if not f.startswith(".")
    ]
    label_files = [
        f for f in os.listdir(os.path.join(label_folder)) if not f.startswith(".")
    ]

    feature_data = sorted(feature_files)
    label_data = sorted(label_files)
    # debug(feature_data, label_data)
    assert len(feature_data) == len(
        label_data
    ), "Feature size and label size does not match up"

    patient_data = list(zip(feature_data, label_data))
    patient_train, patient_test = train_test_split(patient_data, train_rate)

    # iterates through each folder in the specified train/test folder
    start_time = time.time()
    for i, (feature_train, label_train) in enumerate(patient_train):
        feature_dir = os.path.join(feature_folder, feature_train)
        label_dir = os.path.join(label_folder, label_train)

        save_dir, feature_array, label_array = dataset_specific_process(
            parent_save_folder, feature_dir, label_dir, dataset, True
        )
        feature_array = clip_dicom(feature_array)
        label_array = process_label(label_array, dataset)

        assert (
            feature_array.shape == label_array.shape
        ), "Feature and label shape does not match up".format(feature_dir)

        assert (
            feature_array.shape[1] == 512
        ), "Inconsistant feature and label shape: {0}".format(feature_dir)

        feature_array = feature_array.astype("float32")
        label_array = label_array.astype("int8")

        partition_pickle_data(save_dir, feature_array, label_array)
        processed_train.append(save_dir)

        if len(patient_train) < 10 or (i + 1) % int(len(patient_train) / 10) == 0:
            end_time = time.time()
            print(
                "Training data preprocess progress: {0:.2f}, time spent: {1:.4f} min".format(
                    (i + 1) / len(patient_train), (end_time - start_time) / 60
                )
            )

    # return processed_train, processed_test
    return processed_train


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Medperf Data Preparator Example")
    parser.add_argument(
        "--images_path", dest="images", type=str, help="path containing raw names"
    )
    parser.add_argument(
        "--labels_path", dest="labels", type=str, help="path containing labels"
    )
    parser.add_argument(
        "--out", dest="out", type=str, help="path to store prepared data"
    )

    args = parser.parse_args()
    print(args.images)

    #     with open(args.parameters_file, "r") as stream:
    #         parameters = yaml.load(stream, Loader=yaml.FullLoader)
    #     logger.info("Parameters have been read (%s).", args.parameters_file)

    path = args.images
    label = args.labels
    out = args.out

    # data_folder = '/mnt/disks/lits-data/dfci-ai-pilot-federatedlearn/pancreas/'
    # data_folder = path
    # parent_save_folder = '/mnt/disks/lits-data/dfci-ai-pilot-federatedlearn/'
    parent_folder = out
    # feature_folder_tcia = 'TCIA-images'
    feature_folder = path
    # label_folder_tcia = 'TCIA-labels'
    label_folder = label
    print("feature folder:", feature_folder)
    image_path = os.listdir(feature_folder)
    print(image_path[0])
    if "nii.gz" in image_path[0]:
        print("Processing Synapse Data")
        key = "synapse"
    else:
        key = "tcia"
        print("Processing TCIA data")

    #     feature_folder: directory for target data (train / test)
    #     label_folder: directory for image folders inside each patient's data
    #     dataset: dataset name (select between 'synapse', 'task07', 'tcia')
    #     parent_save_folder: parent directory for data saving

    output_synapse = data_preprocess(
        feature_folder=feature_folder,
        label_folder=label_folder,
        dataset=key,
        parent_save_folder=parent_folder,
    )
