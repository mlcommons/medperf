from subprocess import check_call
import time


def start_collaborator(
    address,
    port,
    ca_cert_path,
    key_path,
    train_data_path,
    train_labels_path,
    val_data_path,
    val_labels_path,
):
    node_config = (
        f'train_data_path="{train_data_path}" '
        f'train_labels_path="{train_labels_path}" '
        f'val_data_path="{val_data_path}" '
        f'val_labels_path="{val_labels_path}"'
    )
    # TODO: catch keyboard interrupt?

    # the following logic is because the server will become available but the public keys
    # are not immediately registered (it takes a few seconds). The logic below will keep trying
    # for a certain amount of time.
    total_wait_time_after_first_error = 120  # seconds
    while True:
        try:
            check_call(
                [
                    "flower-supernode",
                    "--superlink",
                    f"{address}:{port}",
                    "--clientappio-api-address",
                    "127.0.0.1:9094",
                    "--node-config",
                    node_config,
                    "--root-certificates",
                    ca_cert_path,
                    "--auth-supernode-private-key",
                    key_path,
                ]
            )
        except Exception as e:
            print(f"Error connecting to the server: {e}")
            print("Retrying in 10 seconds...")
            time.sleep(10)
            total_wait_time_after_first_error -= 10
            if total_wait_time_after_first_error <= 0:
                print("Failed to connect to the server after multiple attempts.")
                break
