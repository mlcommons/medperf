# I tested with torch==2.4.0 (2.6.0 gives troubles, but we an deal with those if we want to go with that version)
# note there is a folder I am pulling from for imports aa couple of lines down, then also NNUnet V1 needs to be
# installed in the environment


import os
import argparse

import pandas as pd
import yaml

from utils import symlink_one_subject, get_subdirs, make_yaml_serializable

from metrics_GLI import get_LesionWiseResults


def symlink_folder_for_nnunet_validation(
    postopp_pardir, symlink_dir, timestamp_selection="all", verbose=True
):
    """
    Set up a directory of symlinks to data using file/folder structure that NNUnet expects. The data folder will be used
    by the NNUet predict.py script, and the labels will later be used to evaluate the predictions.
    postopp_pardir (str):
        The path to the post-operative data directory created by the medperf data prep pipeline.
    symlink_dir (str):
        The path to the directory where the symlinks will be created. This directory should not already exist.
    timestamp_selection (str):
        The timestamp selection to use for the symlinks. This should be one of the following:
        'latest': Use the latest timestamp for each subject.
        'earliest': Use the earliest timestamp for each subject.
        'all': Use all timestamps for each subject.
    """

    sym_labels_dir = os.path.join(symlink_dir, "labels")

    if not os.path.exists(symlink_dir):
        raise ValueError(
            f"Symlink directory {symlink_dir} does not exist. Please create it first."
        )

    if os.path.exists(sym_labels_dir):
        raise ValueError(
            f"Symlink directory {sym_labels_dir} already exists. Please delete it first."
        )
    else:
        os.makedirs(sym_labels_dir, exist_ok=False)

    all_subjects = get_subdirs(postopp_pardir)

    # Track the subjects and timestamps for each shard
    subject_to_timestamps = {}

    for subject_dir in all_subjects:
        subject_to_timestamps[subject_dir] = symlink_one_subject(
            postopp_subject_dir=subject_dir,
            postopp_labels_dirpath=postopp_pardir,
            nnunet_labels_train_pardir=sym_labels_dir,
            timestamp_selection=timestamp_selection,
            verbose=verbose,
        )
    return sym_labels_dir


if __name__ == "__main__":
    tmp_folder = "/tmp/symlinks"
    os.makedirs(tmp_folder, exist_ok=True)
    parser = argparse.ArgumentParser()
    # add arguments
    parser.add_argument(
        "--postopp_pardir",
        type=str,
        default="/mlcommons/volumes/labels",
        help="Path to data resulting from medperf data prep.",
    )
    parser.add_argument(
        "--symlink_dir",
        type=str,
        default=tmp_folder,
        help="Path to the directory where the symlinks will be created.",
    )
    parser.add_argument(
        "--inference_output_dir",
        type=str,
        default="/mlcommons/volumes/predictions",
        help="Path to the directory where the inference output will be saved.",
    )
    parser.add_argument(
        "--output_metrics",
        type=str,
        default="/mlcommons/volumes/results/results.yaml",
        help="Path to the csv file holding metric lesion wise results for each case.",
    )
    parser.add_argument(
        "--local_outputs",
        type=str,
        default="/mlcommons/volumes/local_outputs",
        help="Path to the folder where local-only outputs such as lookup dict can be stored.",
    )

    args = parser.parse_args()
    postopp_pardir = args.postopp_pardir
    symlink_dir = args.symlink_dir
    inference_output_dir = args.inference_output_dir
    output_metrics = args.output_metrics
    local_outputs = args.local_outputs

    # create symlinks for the data and labels
    sym_labels_dir = symlink_folder_for_nnunet_validation(
        postopp_pardir, symlink_dir, timestamp_selection="all", verbose=True
    )

    print(
        f"Scoring predictions: {inference_output_dir} against labels: {sym_labels_dir}...\n"
    )

    case_idx_lookup_dict = {"LocalCaseIdx": [], "CaseName": []}

    # look at consistency between files for prediction and ground truth
    # NOTE: code below (until #---#) copied and modified from: https://github.com/MIC-DKFZ/nnUNet/blob/v1.7.1/documentation/dataset_conversion.md
    files_in_pred = [
        fname for fname in os.listdir(inference_output_dir) if fname.endswith(".nii.gz")
    ]
    files_in_gt = [
        fname for fname in os.listdir(sym_labels_dir) if fname.endswith(".nii.gz")
    ]
    have_no_gt = [i for i in files_in_pred if i not in files_in_gt]
    assert (
        len(have_no_gt) == 0
    ), "Some files in folder_predicted have not ground truth in folder_gt"
    have_no_pred = [i for i in files_in_gt if i not in files_in_pred]
    if len(have_no_pred) > 0:
        raise ValueError(
            f"All predictions were expected to have ground truth, but the following did not: {have_no_pred}"
        )

    files_in_gt.sort()
    files_in_pred.sort()

    # construct full paths
    full_filenames_pred = [
        os.path.join(inference_output_dir, fname) for fname in files_in_pred
    ]
    full_filenames_gt = [os.path.join(sym_labels_dir, fname) for fname in files_in_gt]
    # ---#

    results_df = None
    per_lesion_df = None

    # Because calling metrics will create folders in the working directory, switch to /tmp
    metrics_workdir = "/tmp/workdir"
    os.makedirs(metrics_workdir, exist_ok=True)
    os.chdir(metrics_workdir)
    for case_idx, (inference_output_file, sym_labels_file) in enumerate(
        zip(full_filenames_pred, full_filenames_gt)
    ):
        single_result_df, single_per_lesion_df = get_LesionWiseResults(
            pred_file=inference_output_file,
            gt_file=sym_labels_file,
            challenge_name="Fets2.0",
        )

        # insert the case idx and filename
        single_result_df["LocalCaseIdx"] = case_idx
        single_per_lesion_df["LocalCaseIdx"] = case_idx

        # prepare to locally store case index to name
        case_idx_lookup_dict["LocalCaseIdx"].append(case_idx)
        case_idx_lookup_dict["CaseName"].append(inference_output_file.split("/")[-1])

        if results_df is None:
            results_df = single_result_df
            per_lesion_df = single_per_lesion_df

        else:
            results_df = pd.concat(
                [results_df, single_result_df], axis=0, ignore_index=True
            )
            per_lesion_df = pd.concat(
                [per_lesion_df, single_per_lesion_df], axis=0, ignore_index=True
            )

    # save per case results to csv
    results_dict = results_df.to_dict()
    per_lesion_dict = per_lesion_df.to_dict()

    # remove case index before aggregating
    agg_df = (
        results_df.drop(columns=["LocalCaseIdx"]).groupby("Labels").mean().reset_index()
    )
    agg_df["CaseCount"] = results_df["LocalCaseIdx"].nunique()
    agg_dict = agg_df.to_dict()

    final_dict = {
        "results_dict": results_dict,
        "per_lesion_dict": per_lesion_dict,
        "agg_dict": agg_dict,
    }
    make_yaml_serializable(final_dict)

    with open(output_metrics, "w") as f:
        yaml.safe_dump(final_dict, f)

    # save local outputs
    os.makedirs(local_outputs, exist_ok=True)
    case_idx_lookup_csv = os.path.join(local_outputs, "case_idx_lookup.csv")
    pd.DataFrame(case_idx_lookup_dict).to_csv(case_idx_lookup_csv)
