import nibabel
import os
import numpy as np
import dicom
import yaml
from scipy.ndimage import zoom


def prepare_tcia_images(input_path, output_path, cases, img_height, img_width):

    for n, case in enumerate(cases):
        print("\rprocessing tcia images:", n + 1, "/", len(cases), end="")
        volumeID = "{:0>4}".format(case)
        filename1 = "PANCREAS_" + volumeID
        directory1 = os.path.join(input_path, filename1)
        filename2 = volumeID + ".npy"
        for path_, _, file_ in os.walk(directory1):
            L = len(file_)
            if L > 0:
                data = np.zeros((img_height, img_width, L), dtype=np.int16)
                for f in sorted(file_):
                    file1 = os.path.abspath(os.path.join(path_, f))
                    image = dicom.read_file(file1)
                    sliceID = image.data_element("InstanceNumber").value - 1
                    if (
                        image.pixel_array.shape[0] != img_height
                        or image.pixel_array.shape[1] != img_width
                    ):
                        raise Exception(
                            "Error: DICOM image does not fit "
                            + str(img_height)
                            + "x"
                            + str(img_width)
                            + " size!"
                        )
                    data[:, :, sliceID] = image.pixel_array
                file2 = os.path.join(output_path, filename2)
                np.save(file2, data)

    print()


def prepare_tcia_labels(input_path, output_path, cases):

    for n, case in enumerate(cases):
        print("\rprocessing tcia labels:", n + 1, "/", len(cases), end="")
        volumeID = "{:0>4}".format(case)
        filename = "label" + volumeID + ".nii.gz"

        data = nibabel.load(os.path.join(input_path, filename)).get_data()
        data = data.transpose(1, 0, 2)

        outfile = os.path.join(output_path, volumeID + ".npy")
        np.save(outfile, data)
    print()


def btcv_transformation(data):

    return data


def prepare_btcv_images(input_path, output_path, cases):
    for n, case in enumerate(cases):
        print("\rprocessing btcv images:", n + 1, "/", len(cases), end="")
        volumeID = "{:0>4}".format(case)
        filename = "img" + volumeID + ".nii.gz"

        data = nibabel.load(os.path.join(input_path, filename)).get_data()
        data = data.transpose(1, 0, 2)
        data = np.flip(data, axis=-1)
        data = zoom(data, [1, 1, 3])

        outfile = os.path.join(output_path, volumeID + ".npy")
        np.save(outfile, data)
    print()


def prepare_btcv_labels(input_path, output_path, cases):
    for n, case in enumerate(cases):
        print("\rprocessing btcv labels:", n + 1, "/", len(cases), end="")
        volumeID = "{:0>4}".format(case)
        filename = "label" + volumeID + ".nii.gz"

        data = nibabel.load(os.path.join(input_path, filename)).get_data()
        data = data.transpose(1, 0, 2)
        data = np.flip(data, axis=-1)
        data[data != 11] = 0
        data[data == 11] = 1
        data = np.repeat(data, [3] * data.shape[-1], axis=-1)

        outfile = os.path.join(output_path, volumeID + ".npy")
        np.save(outfile, data)
    print()


def prepare_btcv(
    data_path, labels_path, params_file, out_path,
):
    # images folder structure is expected to have list of imgXXXX.nii.gz
    # images folder structure is expected to have list of labelXXXX.nii.gz
    img_cases = list(map(lambda x: int(x[3:7]), os.listdir(data_path)))
    img_cases.sort()

    label_cases = list(map(lambda x: int(x[5:9]), os.listdir(labels_path)))
    label_cases.sort()

    assert img_cases == label_cases, "inconsistent images-labels files"

    images_out_path = os.path.join(out_path, "images")
    labels_out_path = os.path.join(out_path, "labels")
    os.makedirs(images_out_path, exist_ok=True)
    os.makedirs(labels_out_path, exist_ok=True)

    params = yaml.safe_load(open(params_file, "r"))

    prepare_btcv_images(data_path, images_out_path, img_cases)
    prepare_btcv_labels(labels_path, labels_out_path, label_cases)


def prepare_tcia(
    data_path, labels_path, params_file, out_path,
):
    # folder structure of data_path is expected to be like
    # "Pancreas-CT" folder of the official TCIA dataset
    img_cases = list(map(lambda x: int(x.split("_")[-1]), os.listdir(data_path)))
    img_cases.sort()

    label_cases = list(map(lambda x: int(x[5:9]), os.listdir(labels_path)))
    label_cases.sort()

    assert img_cases == label_cases, "inconsistent images-labels files"

    images_out_path = os.path.join(out_path, "images")
    labels_out_path = os.path.join(out_path, "labels")
    os.makedirs(images_out_path, exist_ok=True)
    os.makedirs(labels_out_path, exist_ok=True)

    params = yaml.safe_load(open(params_file, "r"))

    prepare_tcia_images(
        data_path,
        images_out_path,
        img_cases,
        params["image_height"],
        params["image_width"],
    )

    prepare_tcia_labels(labels_path, labels_out_path, label_cases)


def prepare_data(
    data_path, labels_path, params_file, out_path,
):
    # the way to infer btcv or tcia is the existence of nii.gz images
    # or folders starting with PANCREAS, according to the official
    # datasets structure
    if os.listdir(data_path)[0].endswith(".nii.gz"):
        prepare_btcv(
            data_path, labels_path, params_file, out_path,
        )
    elif os.listdir(data_path)[0].startswith("PANCREAS"):
        prepare_tcia(
            data_path, labels_path, params_file, out_path,
        )
    else:
        raise Exception("Cannot infer data structure")
