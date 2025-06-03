import os


def perform_sanity_checks(data_path, labels_path):
    images_files = os.listdir(os.path.join(data_path, "pathmnist"))

    assert all(
        [image.endswith(".png") for image in images_files]
    ), "images should be .png"

    print("Sanity checks ran successfully.")
