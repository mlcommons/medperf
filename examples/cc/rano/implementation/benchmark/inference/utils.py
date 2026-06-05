import os

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
    postopp_data_dirpath,
    nnunet_images_train_pardir,
    timestamp_selection,
    verbose=False,
):
    if verbose:
        print(
            f"\n#######\nsymlinking subject: {postopp_subject_dir}\n########\nPostopp_data_dirpath: {postopp_data_dirpath}\n"
        )
        print("\n\n")
    postopp_subject_dirpath = os.path.join(postopp_data_dirpath, postopp_subject_dir)
    all_timestamps = get_subdirs(postopp_subject_dirpath)
    if timestamp_selection == "latest":
        timestamps = all_timestamps[-1:]
    elif timestamp_selection == "earliest":
        timestamps = all_timestamps[0:1]
    elif timestamp_selection == "all":
        timestamps = all_timestamps
    else:
        raise ValueError(
            (
                "timestamp_selection currently only supports 'latest', 'earliest', and 'all',"
                f" but you have requested: '{timestamp_selection}'"
            )
        )

    for timestamp in timestamps:
        timestamp_without_dots = timestamp.replace(".", "_")
        postopp_subject_timestamp_dirpath = os.path.join(
            postopp_subject_dirpath, timestamp
        )

        timed_subject = postopp_subject_dir + "_" + timestamp
        timed_subject_without_dots = postopp_subject_dir + "_" + timestamp_without_dots

        # Symlink images
        for num in num_to_modality:
            src_path = os.path.join(
                postopp_subject_timestamp_dirpath, timed_subject + num_to_modality[num]
            )
            dst_path = os.path.join(
                nnunet_images_train_pardir, timed_subject_without_dots + num + ".nii.gz"
            )
            os.symlink(src=src_path, dst=dst_path)

    return timestamps
