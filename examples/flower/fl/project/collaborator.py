from subprocess import check_call


def start_collaborator(
    address, port, train_data_path, train_labels_path, val_data_path, val_labels_path
):
    node_config = (
        f'train_data_path="{train_data_path}" '
        f'train_labels_path="{train_labels_path}" '
        f'val_data_path="{val_data_path}" '
        f'val_labels_path="{val_labels_path}"'
    )
    # TODO: catch keyboard interrupt?
    check_call(
        [
            "flower-supernode",
            "--insecure",
            "--superlink",
            f"{address}:{port}",
            "--clientappio-api-address",
            "127.0.0.1:9094",
            "--node-config",
            node_config,
        ]
    )


def check_connectivity(workspace_folder):
    # not implemented for flower
    pass
