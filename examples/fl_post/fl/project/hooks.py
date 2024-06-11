import os
import shutil
import pandas as pd
from utils import get_collaborator_cn


def __modify_df(df):
    # gandlf convention: labels columns could be "target", "label", "mask"
    # subject id column is subjectid. data columns are Channel_0.
    # Others could be scalars. # TODO
    labels_columns = ["target", "label", "mask"]
    data_columns = ["channel_0"]
    subject_id_column = "subjectid"
    for column in df.columns:
        if column.lower() == subject_id_column:
            continue
        if column.lower() in labels_columns:
            prepend_str = "labels/"
        elif column.lower() in data_columns:
            prepend_str = "data/"
        else:
            continue

        df[column] = prepend_str + df[column].astype(str)


def collaborator_pre_training_hook(
    data_path,
    labels_path,
    node_cert_folder,
    ca_cert_folder,
    plan_path,
    output_logs,
    init_nnunet_directory,
):
    # runtime env vars should be set as early as possible
    tmpfolder = os.path.join(output_logs, ".tmp")
    os.environ["TMPDIR"] = tmpfolder
    os.makedirs(tmpfolder, exist_ok=True)
    os.environ["RESULTS_FOLDER"] = os.path.join(tmpfolder, "nnUNet_trained_models")
    os.environ["nnUNet_raw_data_base"] = os.path.join(tmpfolder, "nnUNet_raw_data_base")
    os.environ["nnUNet_preprocessed"] = os.path.join(tmpfolder, "nnUNet_preprocessed")
    import nnunet_setup
  
    cn = get_collaborator_cn()
    workspace_folder = os.path.join(output_logs, "workspace")
    os.makedirs(workspace_folder, exist_ok=True)

    os.symlink(data_path, f"{workspace_folder}/data", target_is_directory=True)
    os.symlink(labels_path, f"{workspace_folder}/labels", target_is_directory=True)

    nnunet_setup.main([workspace_folder], 
                      537, # FIXME: does this need to be set in any particular way?
                      f'{init_nnunet_directory}/model_initial_checkpoint.model', 
                      f'{init_nnunet_directory}/model_initial_checkpoint.model.pkl', 
                      'FLPost', 
                      .8, 
                      'by_subject_time_pair', 
                      '3d_fullres', 
                      'nnUNetTrainerV2', 
                      '0', 
                      plans_identifier=None, 
                      num_institutions=1, 
                      cuda_device='0', 
                      verbose=False)

    data_config = f"{cn},Task537_FLPost"
    plan_folder = os.path.join(workspace_folder, "plan")
    os.makedirs(plan_folder, exist_ok=True)
    data_config_path = os.path.join(plan_folder, "data.yaml")
    with open(data_config_path, "w") as f:
        f.write(data_config)
    shutil.copytree('/mlcube_project/src', os.path.join(workspace_folder, 'src'))

def collaborator_post_training_hook(
    data_path,
    labels_path,
    node_cert_folder,
    ca_cert_folder,
    plan_path,
    output_logs,
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
):
    pass
