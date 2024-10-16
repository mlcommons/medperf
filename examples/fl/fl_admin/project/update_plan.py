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
