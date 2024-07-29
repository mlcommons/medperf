import os
import shutil


def setup_ws(node_cert_folder, ca_cert_folder, plan_path, temp_dir):
    workspace_folder = os.path.join(temp_dir, "workspace")
    create_workspace(workspace_folder)
    prepare_plan(plan_path, workspace_folder)
    cn = get_admin_cn()
    prepare_node_cert(node_cert_folder, "client", f"col_{cn}", workspace_folder)
    prepare_ca_cert(ca_cert_folder, workspace_folder)
    return workspace_folder, cn


def create_workspace(fl_workspace):
    plan_folder = os.path.join(fl_workspace, "plan")
    workspace_config = os.path.join(fl_workspace, ".workspace")
    defaults_file = os.path.join(plan_folder, "defaults")

    os.makedirs(plan_folder, exist_ok=True)
    with open(defaults_file, "w") as f:
        f.write("../../workspace/plan/defaults\n\n")
    with open(workspace_config, "w") as f:
        f.write("current_plan_name: default\n\n")


def get_admin_cn():
    return os.environ["MEDPERF_ADMIN_PARTICIPANT_CN"]


def get_col_label_to_add():
    return os.environ["MEDPERF_COLLABORATOR_LABEL_TO_ADD"]


def get_col_cn_to_add():
    return os.environ["MEDPERF_COLLABORATOR_CN_TO_ADD"]


def get_col_label_to_remove():
    return os.environ["MEDPERF_COLLABORATOR_LABEL_TO_REMOVE"]


def get_col_cn_to_remove():
    return os.environ["MEDPERF_COLLABORATOR_CN_TO_REMOVE"]


def prepare_plan(plan_path, fl_workspace):
    target_plan_folder = os.path.join(fl_workspace, "plan")
    os.makedirs(target_plan_folder, exist_ok=True)

    target_plan_file = os.path.join(target_plan_folder, "plan.yaml")
    shutil.copyfile(plan_path, target_plan_file)


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
