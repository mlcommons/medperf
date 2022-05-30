from pathlib import Path
import yaml

from sanity_check import check_subject_validity


def get_statistics(data_path: str, labels_path: str) -> dict:
    """Computes statistics about the data. This statistics are uploaded
    to the Medperf platform under the data owner's approval. Include
    every statistic you consider useful for determining the nature of the
    data, but keep in mind that we want to keep the data as private as 
    possible.

    Args:
        data_path (str): The input data folder.
        labels_path (str): The input labels folder.

    Returns:
        dict: dictionary with all the computed statistics
    """
    number_valid_subjects, number_of_invalid_subjects = 0, 0

    for curr_subject_dir in Path(data_path).iterdir():
        if curr_subject_dir.is_dir():
            if check_subject_validity(curr_subject_dir, Path(labels_path)):
                number_valid_subjects += 1
            else:
                number_of_invalid_subjects += 1

            ## this can be expanded to get more information about the data, such as the number labels in each segmentation, and so on.

    stats = {
        "Valid_Subjects": number_valid_subjects,
        "Invalid_Subjects": number_of_invalid_subjects,
    }

    return stats


def run_statistics(data_path: str, labels_path: str, out_file: str):
    stats = get_statistics(data_path, labels_path)

    with open(out_file, "w") as f:
        yaml.dump(stats, f)
