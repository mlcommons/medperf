import shutil


def prepare_dataset(
    data_path, labels_path, parameters, output_path, output_labels_path
):
    task = parameters["task"]
    assert task in [
        "segmentation",
        "segmentation-radiotherapy",
        "pathology",
    ], "Invalid task"

    shutil.copytree(data_path, output_path, dirs_exist_ok=True)
    shutil.copytree(labels_path, output_labels_path, dirs_exist_ok=True)
