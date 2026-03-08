import os

import numpy as np

num_to_modality = {
    "_0000": "_brain_t1n.nii.gz",
    "_0001": "_brain_t2w.nii.gz",
    "_0002": "_brain_t2f.nii.gz",
    "_0003": "_brain_t1c.nii.gz",
}


def get_subdirs(parent_directory):
    subjects = os.listdir(parent_directory)
    subjects = [
        p
        for p in subjects
        if os.path.isdir(os.path.join(parent_directory, p)) and not p.startswith(".")
    ]
    return sorted(subjects)


def symlink_one_subject(
    postopp_subject_dir,
    postopp_labels_dirpath,
    nnunet_labels_train_pardir,
    timestamp_selection,
    verbose=False,
):
    if verbose:
        print(
            f"\n#######\nsymlinking subject: {postopp_subject_dir}\n########\nPostopp_labels_dirpath: {postopp_labels_dirpath}"
        )
        print("\n\n\n")
    postopp_subject_dirpath = os.path.join(postopp_labels_dirpath, postopp_subject_dir)
    all_timestamps = get_subdirs(postopp_subject_dirpath)
    if timestamp_selection == "latest":
        timestamps = all_timestamps[-1:]
    elif timestamp_selection == "earliest":
        timestamps = all_timestamps[0:1]
    elif timestamp_selection == "all":
        timestamps = all_timestamps
    else:
        raise ValueError(
            f"timestamp_selection currently only supports 'latest', 'earliest', and 'all'"
            f" but you have requested: '{timestamp_selection}'"
        )

    for timestamp in timestamps:
        timestamp_without_dots = timestamp.replace(".", "_")
        postopp_subject_timestamp_dirpath = os.path.join(
            postopp_subject_dirpath, timestamp
        )
        postopp_subject_timestamp_label_dirpath = os.path.join(
            postopp_labels_dirpath, postopp_subject_dir, timestamp
        )
        if not os.path.exists(postopp_subject_timestamp_label_dirpath):
            raise ValueError(
                f"Subject label file for data at: {postopp_subject_timestamp_dirpath} was not"
                f" found in the expected location: {postopp_subject_timestamp_label_dirpath}"
            )

        timed_subject = postopp_subject_dir + "_" + timestamp
        timed_subject_without_dots = postopp_subject_dir + "_" + timestamp_without_dots

        # Symlink label first
        label_src_path = os.path.join(
            postopp_subject_timestamp_label_dirpath, timed_subject + "_final_seg.nii.gz"
        )
        label_dst_path = os.path.join(
            nnunet_labels_train_pardir, timed_subject_without_dots + ".nii.gz"
        )
        os.symlink(src=label_src_path, dst=label_dst_path)

    return timestamps


def make_yaml_serializable(final_dict):
    if not isinstance(final_dict, dict):
        return
    for key, val in final_dict.items():
        if isinstance(val, np.ndarray):
            final_dict[key] = val.tolist()
        else:
            make_yaml_serializable(val)
