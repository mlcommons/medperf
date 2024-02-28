import yaml
import os
import pandas as pd

WORKSPACE = os.environ["FL_WORKSPACE"]


def get_aggregator_fqdn():
    plan_path = os.path.join(WORKSPACE, "plan", "plan.yaml")
    plan = yaml.safe_load(open(plan_path))
    return plan["network"]["settings"]["agg_addr"].lower()


def get_collaborator_cn():
    # TODO: check if there is a way this can cause a collision/race condition
    # TODO: from inside the file
    return os.environ["COLLABORATOR_CN"]


def get_weights_path():
    plan_path = os.path.join(WORKSPACE, "plan", "plan.yaml")
    plan = yaml.safe_load(open(plan_path))
    return {
        "init": plan["aggregator"]["settings"]["init_state_path"],
        "best": plan["aggregator"]["settings"]["best_state_path"],
        "last": plan["aggregator"]["settings"]["last_state_path"],
    }


def prepare_plan(parameters_file, network_config):
    with open(parameters_file) as f:
        params = yaml.safe_load(f)
    if "plan" not in params:
        raise RuntimeError("Parameters file should contain a `plan` entry")
    with open(network_config) as f:
        network_config_dict = yaml.safe_load(f)
    plan = params["plan"]
    plan["network"]["settings"].update(network_config_dict)
    target_plan_folder = os.path.join(WORKSPACE, "plan")
    os.makedirs(target_plan_folder, exist_ok=True)
    target_plan_file = os.path.join(target_plan_folder, "plan.yaml")
    with open(target_plan_file, "w") as f:
        yaml.dump(plan, f)


def prepare_cols_list(collaborators_file):
    with open(collaborators_file) as f:
        cols = f.read().strip().split("\n")

    target_plan_folder = os.path.join(WORKSPACE, "plan")
    os.makedirs(target_plan_folder, exist_ok=True)
    target_plan_file = os.path.join(target_plan_folder, "cols.yaml")
    with open(target_plan_file, "w") as f:
        yaml.dump({"collaborators": cols}, f)


def prepare_init_weights(input_weights):
    error_msg = f"{input_weights} should contain only one file: *.pbuf"

    files = os.listdir(input_weights)
    file = files[0]
    if len(files) != 1 or not file.endswith(".pbuf"):
        raise RuntimeError(error_msg)

    file = os.path.join(input_weights, file)

    target_weights_subpath = get_weights_path()["init"]
    target_weights_path = os.path.join(WORKSPACE, target_weights_subpath)
    target_weights_folder = os.path.dirname(target_weights_path)
    os.makedirs(target_weights_folder, exist_ok=True)
    os.symlink(file, target_weights_path)


def prepare_node_cert(node_cert_folder, target_cert_folder_name, target_cert_name):
    error_msg = f"{node_cert_folder} should contain only two files: *.crt and *.key"

    files = os.listdir(node_cert_folder)
    file_extensions = [file.split(".")[-1] for file in files]
    if len(files) != 2 or sorted(file_extensions) != ["crt", "key"]:
        raise RuntimeError(error_msg)

    if files[0].endswith(".crt") and files[1].endswith(".key"):
        cert_file = files[0]
        key_file = files[1]
    else:
        key_file = files[0]
        cert_file = files[1]

    key_file = os.path.join(node_cert_folder, key_file)
    cert_file = os.path.join(node_cert_folder, cert_file)

    target_cert_folder = os.path.join(WORKSPACE, "cert", target_cert_folder_name)
    os.makedirs(target_cert_folder, exist_ok=True)
    target_cert_file = os.path.join(target_cert_folder, f"{target_cert_name}.crt")
    target_key_file = os.path.join(target_cert_folder, f"{target_cert_name}.key")

    os.symlink(key_file, target_key_file)
    os.symlink(cert_file, target_cert_file)


def prepare_ca_cert(ca_cert_folder):
    error_msg = f"{ca_cert_folder} should contain only one file: *.crt"

    files = os.listdir(ca_cert_folder)
    file = files[0]
    if len(files) != 1 or not file.endswith(".crt"):
        raise RuntimeError(error_msg)

    file = os.path.join(ca_cert_folder, file)

    target_ca_cert_folder = os.path.join(WORKSPACE, "cert")
    os.makedirs(target_ca_cert_folder, exist_ok=True)
    target_ca_cert_file = os.path.join(target_ca_cert_folder, "cert_chain.crt")

    os.symlink(file, target_ca_cert_file)


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


def prepare_data(data_path, labels_path, cn):
    target_data_folder = os.path.join(WORKSPACE, "data", cn)
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
    plan_folder = os.path.join(WORKSPACE, "plan")
    os.makedirs(plan_folder, exist_ok=True)
    data_config_path = os.path.join(plan_folder, "data.yaml")
    with open(data_config_path, "w") as f:
        f.write(data_config)
