# I tested with torch==2.4.0 (2.6.0 gives troubles, but we an deal with those if we want to go with that version)
# note there is a folder I am pulling from for imports aa couple of lines down, then also NNUnet V1 needs to be
# installed in the environment

import os
import subprocess
import shutil
import argparse
from utils import get_subdirs, symlink_one_subject


MODEL = "3d_fullres"
FOLD_NUM = 0
FOLD = f"fold_{FOLD_NUM}"
TASK_NAME = "Task500_Postopp_Inference"
PLANS_FOLDER_NAME = "nnUNetPlans_pretrained_POSTOPP"


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

    sym_data_dir = os.path.join(symlink_dir, "data")

    if not os.path.exists(symlink_dir):
        raise ValueError(
            f"Symlink directory {symlink_dir} does not exist. Please create it first."
        )

    if os.path.exists(sym_data_dir):
        raise ValueError(
            f"Symlink directory {sym_data_dir} already exists. Please delete it first."
        )
    else:
        os.makedirs(sym_data_dir, exist_ok=False)

    all_subjects = get_subdirs(postopp_pardir)

    # Track the subjects and timestamps for each shard
    subject_to_timestamps = {}

    for subject_dir in all_subjects:
        subject_to_timestamps[subject_dir] = symlink_one_subject(
            postopp_subject_dir=subject_dir,
            postopp_data_dirpath=postopp_pardir,
            nnunet_images_train_pardir=sym_data_dir,
            timestamp_selection=timestamp_selection,
            verbose=verbose,
        )
    return sym_data_dir


if __name__ == "__main__":
    tmp_folder = "/tmp/symlinks"
    os.makedirs(tmp_folder, exist_ok=True)
    parser = argparse.ArgumentParser()
    # add arguments
    parser.add_argument(
        "--postopp_pardir",
        type=str,
        default="/mlcommons/volumes/data",
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

    # this folder needs to contain the plans.pkl file, as well as the fold
    # directory with name given by FOLD (above) that in turn contains both the model to be inferenced
    # (which must have the name 'model_final_checkpoint.model') and the model config file
    # (which must have the name 'model_final_checkpoint.model.pkl')
    parser.add_argument(
        "--source_plans_dir",
        type=str,
        default="/mlcommons/volumes/additional_files",
        help="Path to the source plans directory containing the plans.pkl file and model files.",
    )

    args = parser.parse_args()
    postopp_pardir = args.postopp_pardir
    symlink_dir = args.symlink_dir
    inference_output_dir = args.inference_output_dir
    source_plans_dir = args.source_plans_dir

    # create plans dir and copy plans
    staging_plans_dir = os.path.join(
        symlink_dir,
        "nnUNet",
        f"{MODEL}",
        TASK_NAME,
        f"nnUNetTrainerV2__{PLANS_FOLDER_NAME}",
    )
    os.makedirs(staging_plans_dir, exist_ok=True)
    # copy in plans.pkl file
    shutil.copyfile(
        os.path.join(source_plans_dir, "plans.pkl"),
        os.path.join(staging_plans_dir, "plans.pkl"),
    )

    # create the fold dir and copy model checkpoint and checkpoint pickle
    staging_fold_dir = os.path.join(staging_plans_dir, FOLD)
    os.makedirs(staging_fold_dir, exist_ok=True)
    fold_dir = os.path.join(source_plans_dir, FOLD)
    shutil.copyfile(
        os.path.join(fold_dir, "model_final_checkpoint.model"),
        os.path.join(staging_fold_dir, "model_final_checkpoint.model"),
    )
    shutil.copyfile(
        os.path.join(fold_dir, "model_final_checkpoint.model.pkl"),
        os.path.join(staging_fold_dir, "model_final_checkpoint.model.pkl"),
    )

    # create symlinks for the data and labels
    sym_data_dir = symlink_folder_for_nnunet_validation(
        postopp_pardir, symlink_dir, timestamp_selection="all", verbose=True
    )

    # NNUNet uses this environmental variable to locate training assets
    os.environ["RESULTS_FOLDER"] = symlink_dir

    # gpu command
    gpu = f"export CUDA_VISIBLE_DEVICES={0}; "

    # run nnunet
    #  -i '/media/ecalabr/raid/mening_reseg_inputs' -o '/media/ecalabr/raid/mening_reseg_out' -t 903 -f all
    nnunet_executable = os.environ.get("NNUNET_EXECUTABLE", "nnUNet_predict")
    cmd = (
        f"{gpu} {nnunet_executable} -i {sym_data_dir} -o {inference_output_dir} -t {TASK_NAME} "
        f"-f {FOLD_NUM} -p {PLANS_FOLDER_NAME} -m {MODEL}"
    )

    print(cmd)

    subprocess.call(cmd, shell=True)

    # shutil.rmtree(tmp_folder, ignore_errors=True)
