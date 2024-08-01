import os
import shutil


def train_initial_model(
    data_path,
    labels_path,
    output_logs,
    init_nnunet_directory,
):
    # runtime env vars should be set as early as possible
    tmpfolder = os.path.join(output_logs, ".tmp")
    os.makedirs(tmpfolder, exist_ok=True)
    os.environ["RESULTS_FOLDER"] = os.path.join(tmpfolder, "nnUNet_trained_models")
    os.environ["nnUNet_raw_data_base"] = os.path.join(tmpfolder, "nnUNet_raw_data_base")
    os.environ["nnUNet_preprocessed"] = os.path.join(tmpfolder, "nnUNet_preprocessed")
    import nnunet_setup

    workspace_folder = os.path.join(output_logs, "workspace")
    os.makedirs(workspace_folder, exist_ok=True)

    os.symlink(data_path, f"{workspace_folder}/data", target_is_directory=True)
    os.symlink(labels_path, f"{workspace_folder}/labels", target_is_directory=True)

    res = nnunet_setup.main(
        postopp_pardir=workspace_folder,
        three_digit_task_num=537,  # FIXME: does this need to be set in any particular way?
        init_model_path=None,
        init_model_info_path=None,
        task_name="FLPost",
        percent_train=0.8,
        split_logic="by_subject_time_pair",
        network="3d_fullres",
        network_trainer="nnUNetTrainerV2",
        fold="0",
        plans_path=None,
        cuda_device="0",
        verbose=False,
    )

    initial_model_path = res["initial_model_path"]
    initial_model_info_path = res["initial_model_info_path"]
    plans_path = res["plans_path"]

    shutil.move(initial_model_path, init_nnunet_directory)
    shutil.move(initial_model_info_path, init_nnunet_directory)
    shutil.move(plans_path, init_nnunet_directory)
