import os
from subprocess import check_call, Popen
import time


def start_aggregator(
    workspace_folder,
    port,
    admin_port,
    ca_cert_path,
    cert_path,
    key_path,
    initial_weights,
    output_weights,
    report_path,
):
    env = os.environ.copy()
    env["INITIAL_MODEL_PATH"] = initial_weights
    env["OUTPUT_MODEL_PATH"] = output_weights

    Popen(
        [
            "flower-superlink",
            "--fleet-api-address",
            f"0.0.0.0:{port}",
            "--control-api-address",
            f"127.0.0.1:{admin_port}",
            "--ssl-ca-certfile",
            ca_cert_path,
            "--ssl-certfile",
            cert_path,
            "--ssl-keyfile",
            key_path,
        ],
        env=env,
    )
    time.sleep(10)
    env = os.environ.copy()
    env["FLWR_HOME"] = workspace_folder
    check_call(
        ["flwr", "run", workspace_folder, "medperf-deployment", "--stream"], env=env
    )

    with open(report_path, "w") as f:
        f.write("IsDone: 1")
