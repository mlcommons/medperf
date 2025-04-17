import os
import shutil
from utils import get_collaborator_cn


def collaborator_pre_training_hook(
    data_path,
    labels_path,
    node_cert_folder,
    ca_cert_folder,
    plan_path,
    output_logs,
    init_nnunet_directory,
    workspace_folder,
):
    import nnunet_setup

    cn = get_collaborator_cn()

    os.symlink(data_path, f"{workspace_folder}/data", target_is_directory=True)
    os.symlink(labels_path, f"{workspace_folder}/labels", target_is_directory=True)

    # this function returns metadata (model weights and config file) to be distributed out of band
    # evan should use this without stuff to overwrite/sync so that it produces the correct metdata
    # when evan runs, init_model_path, init_model_info_path should be None
    # plans_path should also be None (the returned thing will point to where it lives so that it will be synced with others)

    nnunet_setup.main(
        postopp_pardir=workspace_folder,
        three_digit_task_num=537,  # FIXME: does this need to be set in any particular way?
        init_model_path=f"{init_nnunet_directory}/model_initial_checkpoint.model",
        init_model_info_path=f"{init_nnunet_directory}/model_initial_checkpoint.model.pkl",
        task_name="FLPost",
        percent_train=0.8,
        split_logic="by_subject_time_pair",
        network="3d_fullres",
        network_trainer="nnUNetTrainerV2",
        fold="0",
        plans_path=f"{init_nnunet_directory}/nnUNetPlans_pretrained_POSTOPP_plans_3D.pkl",  # NOTE: IT IS NOT AN OPENFL PLAN
        cuda_device="0",
        verbose=False,
    )

    data_config = f"{cn},Task537_FLPost"
    plan_folder = os.path.join(workspace_folder, "plan")
    os.makedirs(plan_folder, exist_ok=True)
    data_config_path = os.path.join(plan_folder, "data.yaml")
    with open(data_config_path, "w") as f:
        f.write(data_config)
    shutil.copytree("/mlcube_project/src", os.path.join(workspace_folder, "src"))


def collaborator_post_training_hook(
    data_path,
    labels_path,
    node_cert_folder,
    ca_cert_folder,
    plan_path,
    output_logs,
    workspace_folder,
):
    pass


def aggregator_pre_training_hook(
    input_weights,
    node_cert_folder,
    ca_cert_folder,
    output_logs,
    output_weights,
    plan_path,
    collaborators,
    report_path,
    workspace_folder,
):
    pass


def aggregator_post_training_hook(
    input_weights,
    node_cert_folder,
    ca_cert_folder,
    output_logs,
    output_weights,
    plan_path,
    collaborators,
    report_path,
    workspace_folder,
):
    pass
