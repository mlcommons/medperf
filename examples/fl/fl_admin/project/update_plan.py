from subprocess import check_call


def set_straggler_cutoff_time(workspace_folder, admin_cn, field_value):
    if not field_value.isnumeric():
        raise TypeError(
            f"Expected an integer for straggler cutoff time, got {field_value}"
        )
    check_call(
        [
            "fx",
            "admin",
            "set_straggler_cutoff_time",
            "-n",
            admin_cn,
            "--timeout_in_seconds",
            field_value,
        ],
        cwd=workspace_folder,
    )


def set_dynamic_task_arg(workspace_folder, admin_cn, task_name, arg_name, field_value):
    try:
        float(field_value)
    except ValueError:
        TypeError(f"Expected a float for dynamic task arg, got {field_value}")

    check_call(
        [
            "fx",
            "admin",
            "set_dynamic_task_arg",
            "-n",
            admin_cn,
            "--task_name",
            task_name,
            "--arg_name",
            arg_name,
            "--value",
            field_value,
        ],
        cwd=workspace_folder,
    )
