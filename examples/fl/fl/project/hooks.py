import os
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
):
    cn = get_collaborator_cn()
    workspace_folder = os.path.join(output_logs, "workspace")

    target_data_folder = os.path.join(workspace_folder, "data", cn)
    os.makedirs(target_data_folder, exist_ok=True)
    target_data_data_folder = os.path.join(target_data_folder, "data")
    target_data_labels_folder = os.path.join(target_data_folder, "labels")
    target_train_csv = os.path.join(target_data_folder, "train.csv")
    target_valid_csv = os.path.join(target_data_folder, "valid.csv")

    os.symlink(data_path, target_data_data_folder)
    os.symlink(labels_path, target_data_labels_folder)
    train_csv = os.path.join(data_path, "train.csv")
    valid_csv = os.path.join(data_path, "valid.csv")

    train_df = pd.read_csv(train_csv)
    __modify_df(train_df)
    train_df.to_csv(target_train_csv, index=False)

    valid_df = pd.read_csv(valid_csv)
    __modify_df(valid_df)
    valid_df.to_csv(target_valid_csv, index=False)

    data_config = f"{cn},data/{cn}"
    plan_folder = os.path.join(workspace_folder, "plan")
    os.makedirs(plan_folder, exist_ok=True)
    data_config_path = os.path.join(plan_folder, "data.yaml")
    with open(data_config_path, "w") as f:
        f.write(data_config)


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
