import yaml
import os
import shutil


def generic_setup(output_logs):
    tmpfolder = os.path.join(output_logs, ".tmp")
    os.makedirs(tmpfolder, exist_ok=True)
    # NOTE: this should be set before any code imports tempfile
    os.environ["TMPDIR"] = tmpfolder
    workspace_folder = os.path.join(output_logs, "workspace")
    os.makedirs(workspace_folder, exist_ok=True)
    create_workspace(workspace_folder)
    return workspace_folder


def setup_collaborator(
    data_path,
    labels_path,
    node_cert_folder,
    ca_cert_folder,
    plan_path,
    output_logs,
    workspace_folder,
):
    prepare_plan(plan_path, workspace_folder)
    cn = get_collaborator_cn()
    prepare_node_cert(node_cert_folder, "client", f"col_{cn}", workspace_folder)
    prepare_ca_cert(ca_cert_folder, workspace_folder)


def setup_aggregator(
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
    prepare_plan(plan_path, workspace_folder)
    prepare_cols_list(collaborators, workspace_folder)
    prepare_init_weights(input_weights, workspace_folder)
    fqdn = get_aggregator_fqdn(workspace_folder)
    prepare_node_cert(node_cert_folder, "server", f"agg_{fqdn}", workspace_folder)
    prepare_ca_cert(ca_cert_folder, workspace_folder)


def generic_teardown(output_logs):
    tmp_folder = os.path.join(output_logs, ".tmp")
    shutil.rmtree(tmp_folder, ignore_errors=True)


def create_workspace(fl_workspace):
    plan_folder = os.path.join(fl_workspace, "plan")
    workspace_config = os.path.join(fl_workspace, ".workspace")
    defaults_file = os.path.join(plan_folder, "defaults")

    os.makedirs(plan_folder, exist_ok=True)
    with open(defaults_file, "w") as f:
        f.write("../../workspace/plan/defaults\n\n")
    with open(workspace_config, "w") as f:
        f.write("current_plan_name: default\n\n")


def get_aggregator_fqdn(fl_workspace):
    plan_path = os.path.join(fl_workspace, "plan", "plan.yaml")
    plan = yaml.safe_load(open(plan_path))
    return plan["network"]["settings"]["agg_addr"].lower()


def get_collaborator_cn():
    return os.environ["MEDPERF_PARTICIPANT_LABEL"]


def get_weights_path(fl_workspace):
    plan_path = os.path.join(fl_workspace, "plan", "plan.yaml")
    plan = yaml.safe_load(open(plan_path))
    return {
        "init": plan["aggregator"]["settings"]["init_state_path"],
        "best": plan["aggregator"]["settings"]["best_state_path"],
        "last": plan["aggregator"]["settings"]["last_state_path"],
    }


def prepare_plan(plan_path, fl_workspace):
    target_plan_folder = os.path.join(fl_workspace, "plan")
    os.makedirs(target_plan_folder, exist_ok=True)

    target_plan_file = os.path.join(target_plan_folder, "plan.yaml")
    shutil.copyfile(plan_path, target_plan_file)


def prepare_cols_list(collaborators_file, fl_workspace):
    with open(collaborators_file) as f:
        cols_dict = yaml.safe_load(f)
    cn_different = False
    for col_label in cols_dict.keys():
        cn = cols_dict[col_label]
        if cn != col_label:
            cn_different = True
    if not cn_different:
        # quick hack to support old and new openfl versions
        cols_dict = list(cols_dict.keys())

    target_plan_folder = os.path.join(fl_workspace, "plan")
    os.makedirs(target_plan_folder, exist_ok=True)
    target_plan_file = os.path.join(target_plan_folder, "cols.yaml")
    with open(target_plan_file, "w") as f:
        yaml.dump({"collaborators": cols_dict}, f)


def prepare_init_weights(input_weights, fl_workspace):
    error_msg = f"{input_weights} should contain only one file: *.pbuf"

    files = os.listdir(input_weights)
    file = files[0]  # TODO: this may cause failure in MAC OS
    if len(files) != 1 or not file.endswith(".pbuf"):
        raise RuntimeError(error_msg)

    file = os.path.join(input_weights, file)

    target_weights_subpath = get_weights_path(fl_workspace)["init"]
    target_weights_path = os.path.join(fl_workspace, target_weights_subpath)
    target_weights_folder = os.path.dirname(target_weights_path)
    os.makedirs(target_weights_folder, exist_ok=True)
    os.symlink(file, target_weights_path)


def prepare_node_cert(
    node_cert_folder, target_cert_folder_name, target_cert_name, fl_workspace
):
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

    target_cert_folder = os.path.join(fl_workspace, "cert", target_cert_folder_name)
    os.makedirs(target_cert_folder, exist_ok=True)
    target_cert_file = os.path.join(target_cert_folder, f"{target_cert_name}.crt")
    target_key_file = os.path.join(target_cert_folder, f"{target_cert_name}.key")

    os.symlink(key_file, target_key_file)
    os.symlink(cert_file, target_cert_file)


def prepare_ca_cert(ca_cert_folder, fl_workspace):
    error_msg = f"{ca_cert_folder} should contain only one file: *.crt"

    files = os.listdir(ca_cert_folder)
    file = files[0]
    if len(files) != 1 or not file.endswith(".crt"):
        raise RuntimeError(error_msg)

    file = os.path.join(ca_cert_folder, file)

    target_ca_cert_folder = os.path.join(fl_workspace, "cert")
    os.makedirs(target_ca_cert_folder, exist_ok=True)
    target_ca_cert_file = os.path.join(target_ca_cert_folder, "cert_chain.crt")

    os.symlink(file, target_ca_cert_file)
