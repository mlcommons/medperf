from subprocess import check_call
from utils import (
    get_col_label_to_add,
    get_col_cn_to_add,
    get_col_label_to_remove,
    get_col_cn_to_remove,
    get_update_field_name,
    get_update_value_name,
)
from update_plan import set_straggler_cutoff_time, set_dynamic_task_arg


def get_experiment_status(workspace_folder, admin_cn, output_status_file):
    check_call(
        [
            "fx",
            "admin",
            "get_experiment_status",
            "-n",
            admin_cn,
            "--output_file",
            output_status_file,
        ],
        cwd=workspace_folder,
    )


def add_collaborator(workspace_folder, admin_cn):
    col_label = get_col_label_to_add()
    col_cn = get_col_cn_to_add()
    check_call(
        [
            "fx",
            "admin",
            "add_collaborator",
            "-n",
            admin_cn,
            "--col_label",
            col_label,
            "--col_cn",
            col_cn,
        ],
        cwd=workspace_folder,
    )


def remove_collaborator(workspace_folder, admin_cn):
    col_label = get_col_label_to_remove()
    col_cn = get_col_cn_to_remove()
    check_call(
        [
            "fx",
            "admin",
            "remove_collaborator",
            "-n",
            admin_cn,
            "--col_label",
            col_label,
            "--col_cn",
            col_cn,
        ],
        cwd=workspace_folder,
    )


def update_plan(workspace_folder, admin_cn):
    field_name = get_update_field_name()
    field_value = get_update_value_name()
    if field_name == "straggler_handling_policy.settings.straggler_cutoff_time":
        set_straggler_cutoff_time(workspace_folder, admin_cn, field_value)
    elif field_name.startswith("dynamictaskargs"):
        assert field_name in [
            "dynamictaskargs.train.train_cutoff_time",
            "dynamictaskargs.train.val_cutoff_time",
            "dynamictaskargs.train.train_completion_dampener",
            "dynamictaskargs.aggregated_model_validation.val_cutoff_time",
        ]
        _, task_name, arg_name = field_name.strip().split(".")
        set_dynamic_task_arg(
            workspace_folder, admin_cn, task_name, arg_name, field_value
        )
    else:
        raise ValueError(f"Unsupported field name: {field_name}")
