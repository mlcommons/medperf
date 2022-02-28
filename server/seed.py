import sys
import argparse
import requests
import json
import curlify


def send_request(endpoint, method, headers, data, out_field=None):
    headers.update({"accept": "application/json", "Content-Type": "application/json"})
    try:
        resp = requests.request(
            method=method, headers=headers, url=endpoint, data=json.dumps(data)
        )
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    if resp.status_code != 200 and resp.status_code != 201:
        sys.exit(
            "Response code is "
            + str(resp.status_code)
            + " : "
            + resp.text
            + " curl request "
            + curlify.to_curl(resp.request)
        )
    res = json.loads(resp.text)
    if out_field:
        if out_field not in res:
            sys.exit(out_field + "not in reponse" + resp.text)
        else:
            return res[out_field]


def header(token=None):
    if not token:
        return {}
    else:
        return {"Authorization": "Token " + token}


def seed(args):
    # Get Admin API token using admin credentials
    admin_token = send_request(
        args.server + "/auth-token/",
        "POST",
        header(),
        {"username": args.username, "password": args.password},
        "token",
    )
    print("Admin User Token:", admin_token)

    # Create a new user 'testbenchmarkowner' by admin(Admin API token is used)
    benchmark_owner = send_request(
        args.server + "/users/",
        "POST",
        header(admin_token),
        {
            "username": "testbenchmarkowner",
            "email": "testbo@example.com",
            "password": "test",
            "first_name": "testowner",
            "last_name": "benchmark",
        },
        "id",
    )
    print("Benchmark Owner User Created(by Admin User). ID:", benchmark_owner)

    # Create a new user 'testmodelowner' by admin(Admin API token is used)
    model_owner = send_request(
        args.server + "/users/",
        "POST",
        header(admin_token),
        {
            "username": "testmodelowner",
            "email": "testmo@example.com",
            "password": "test",
            "first_name": "testowner",
            "last_name": "model",
        },
        "id",
    )
    print("Model Owner User Created(by Admin User). Id:", model_owner)

    # Create a new user 'testdataowner' by admin(Admin API token is used)
    data_owner = send_request(
        args.server + "/users/",
        "POST",
        header(admin_token),
        {
            "username": "testdataowner",
            "email": "testdo@example.com",
            "password": "test",
            "first_name": "testowner",
            "last_name": "data",
        },
        "id",
    )
    print("Data Owner User Created(by Admin User). Id:", data_owner)

    print("##########################BENCHMARK OWNER##########################")
    # Get Benchmark Owner API token(token of testbenchmarkowner user)
    benchmark_owner_token = send_request(
        args.server + "/auth-token/",
        "POST",
        header(),
        {"username": "testbenchmarkowner", "password": "test"},
        "token",
    )
    print("Benchmark Owner Token:", benchmark_owner_token)

    # Create a Data preprocessor MLCube by Benchmark Owner
    data_preprocessor_mlcube = send_request(
        args.server + "/mlcubes/",
        "POST",
        header(benchmark_owner_token),
        {
            "name": "xrv_prep",
            "git_mlcube_url": (
                "https://raw.githubusercontent.com/aristizabal95/medical/"
                "d7fbc8f476b03577a9fc66ea7bd9119a60e95e8c/cubes/xrv_prep/mlcube/mlcube.yaml"
            ),
            "git_parameters_url": (
                "https://raw.githubusercontent.com/aristizabal95/medperf-server/"
                "1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_prep/parameters.yaml"
            ),
            "metadata": {},
        },
        "id",
    )
    print(
        "Data Preprocessor MLCube Created(by Benchmark Owner). ID:",
        data_preprocessor_mlcube,
    )

    # Update state of the Data preprocessor MLCube to OPERATION
    data_preprocessor_mlcube_state = send_request(
        args.server + "/mlcubes/" + str(data_preprocessor_mlcube) + "/",
        "PUT",
        header(benchmark_owner_token),
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Data Preprocessor MlCube state updated to",
        data_preprocessor_mlcube_state,
        "by Benchmark Owner",
    )

    # Create a reference model executor mlcube by Benchmark Owner
    reference_model_executor_mlcube = send_request(
        args.server + "/mlcubes/",
        "POST",
        header(benchmark_owner_token),
        {
            "name": "xrv_chex_densenet",
            "git_mlcube_url": (
                "https://raw.githubusercontent.com/aristizabal95/medperf-server/"
                "1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_chex_densenet/mlcube.yaml"
            ),
            "git_parameters_url": (
                "https://raw.githubusercontent.com/aristizabal95/medperf-server/"
                "1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_chex_densenet/parameters.yaml"
            ),
            "tarball_url": "https://storage.googleapis.com/medperf-storage/xrv_chex_densenet.tar.gz",
            "tarball_hash": "c5c408b5f9ef8b1da748e3b1f2d58b8b3eebf96e",
            "metadata": {},
        },
        "id",
    )
    print(
        "Reference Model Executor MlCube Created(by Benchmark Owner). ID:",
        reference_model_executor_mlcube,
    )

    # Update state of the Reference Model Executor MLCube to OPERATION
    reference_model_executor_mlcube_state = send_request(
        args.server + "/mlcubes/" + str(reference_model_executor_mlcube) + "/",
        "PUT",
        header(benchmark_owner_token),
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Reference Model Executor MlCube state updated to",
        reference_model_executor_mlcube_state,
        "by Benchmark Owner",
    )

    # Create a Data evalutor MLCube by Benchmark Owner
    data_evaluator_mlcube = send_request(
        args.server + "/mlcubes/",
        "POST",
        header(benchmark_owner_token),
        {
            "name": "xrv_metrics",
            "git_mlcube_url": (
                "https://raw.githubusercontent.com/aristizabal95/medperf-server/"
                "1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_metrics/mlcube.yaml"
            ),
            "git_parameters_url": (
                "https://raw.githubusercontent.com/aristizabal95/medperf-server/"
                "1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_metrics/parameters.yaml"
            ),
            "metadata": {},
        },
        "id",
    )
    print(
        "Data Evaluator MlCube Created(by Benchmark Owner). ID:", data_evaluator_mlcube,
    )

    # Update state of the Data Evaluator MLCube to OPERATION
    data_evaluator_mlcube_state = send_request(
        args.server + "/mlcubes/" + str(data_evaluator_mlcube) + "/",
        "PUT",
        header(benchmark_owner_token),
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Data Evaluator MlCube state updated to",
        data_evaluator_mlcube_state,
        "by Benchmark Owner",
    )

    # Create a new benchmark by Benchmark owner
    benchmark = send_request(
        args.server + "/benchmarks/",
        "POST",
        header(benchmark_owner_token),
        {
            "name": "xrv",
            "description": "benchmark-sample",
            "docs_url": "string",
            "demo_dataset_tarball_url": "https://storage.googleapis.com/medperf-storage/mock_chexpert_dset.tar.gz",
            "demo_dataset_tarball_hash": "59ad2f17cd8f62ae1728cefb4d64d736503e8ed3",
            "demo_dataset_generated_uid": "string",
            "data_preparation_mlcube": data_preprocessor_mlcube,
            "reference_model_mlcube": reference_model_executor_mlcube,
            "data_evaluator_mlcube": data_evaluator_mlcube,
        },
        "id",
    )
    print("Benchmark Created(by Benchmark Owner). ID:", benchmark)

    # Update the benchmark state to OPERATION
    benchmark_state = send_request(
        args.server + "/benchmarks/" + str(benchmark) + "/",
        "PUT",
        header(benchmark_owner_token),
        {"state": "OPERATION"},
        "state",
    )
    print("Benchmark state updated to", benchmark_state, "by Benchmark owner")

    # Mark the benchmark to be APPROVED
    benchmark_status = send_request(
        args.server + "/benchmarks/" + str(benchmark) + "/",
        "PUT",
        header(admin_token),
        {"approval_status": "APPROVED"},
        "approval_status",
    )
    print("Benchmark Id:", benchmark, "is marked", benchmark_status, "(by Admin)")

    print("##########################MODEL OWNER##########################")
    # Model Owner Interaction
    # Get Model Owner API token(token of testmodelowner user)
    model_owner_token = send_request(
        args.server + "/auth-token/",
        "POST",
        header(),
        {"username": "testmodelowner", "password": "test"},
        "token",
    )
    print("Model Owner Token:", model_owner_token)

    # Create a model mlcube by Model Owner
    model_executor1_mlcube = send_request(
        args.server + "/mlcubes/",
        "POST",
        header(model_owner_token),
        {
            "name": "xrv_resnet",
            "git_mlcube_url": (
                "https://raw.githubusercontent.com/aristizabal95/medical/"
                "1474432849e071c6f42e968b6461da7129ff0282/cubes/xrv_resnet/mlcube/mlcube.yaml"
            ),
            "git_parameters_url": (
                "https://raw.githubusercontent.com/aristizabal95/medical/ "
                "1474432849e071c6f42e968b6461da7129ff0282/cubes/xrv_resnet/mlcube/workspace/parameters.yaml"
            ),
            "tarball_url": "https://storage.googleapis.com/medperf-storage/xrv_resnet.tar.gz",
            "tarball_hash": "e70a6c8e0931537b4b3dd8c06560f227605e9ed1",
            "metadata": {},
        },
        "id",
    )
    print("Model MLCube Created(by Model Owner). ID:", model_executor1_mlcube)

    # Update state of the Model MLCube to OPERATION
    model_executor1_mlcube_state = send_request(
        args.server + "/mlcubes/" + str(model_executor1_mlcube) + "/",
        "PUT",
        header(model_owner_token),
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Model MlCube state updated to", model_executor1_mlcube_state, "by Model Owner",
    )

    # Create another model mlcube by Model Owner
    model_executor2_mlcube = send_request(
        args.server + "/mlcubes/",
        "POST",
        header(model_owner_token),
        {
            "name": "xrv_nih_densenet",
            "git_mlcube_url": (
                "https://raw.githubusercontent.com/aristizabal95/medperf-server/"
                "1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_nih_densenet/mlcube.yaml"
            ),
            "git_parameters_url": (
                "https://raw.githubusercontent.com/aristizabal95/medperf-server/"
                "1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_nih_densenet/parameters.yaml"
            ),
            "tarball_url": "https://storage.googleapis.com/medperf-storage/xrv_nih_densenet.tar.gz",
            "tarball_hash": "2cbba4d29292ca4eadce46070478050503cd9621",
            "metadata": {},
        },
        "id",
    )
    print("Model MLCube Created(by Model Owner). ID:", model_executor2_mlcube)

    # Update state of the Model MLCube to OPERATION
    model_executor2_mlcube_state = send_request(
        args.server + "/mlcubes/" + str(model_executor2_mlcube) + "/",
        "PUT",
        header(model_owner_token),
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Model MlCube state updated to", model_executor2_mlcube_state, "by Model Owner",
    )

    # Associate the model-executor1 mlcube to the created benchmark by model owner user
    model_executor1_in_benchmark = send_request(
        args.server + "/mlcubes/benchmarks/",
        "POST",
        header(model_owner_token),
        {
            "model_mlcube": model_executor1_mlcube,
            "benchmark": benchmark,
            "results": {"key1": "value1", "key2": "value2"},
        },
        "approval_status",
    )

    print(
        "Model MlCube Id:",
        model_executor1_mlcube,
        "associated to Benchmark Id:",
        benchmark,
        "(by Model Owner) which is in",
        model_executor1_in_benchmark,
        "state",
    )

    # Mark the model-executor1 association with created benchmark as approved by benchmark owner
    model_executor1_in_benchmark_status = send_request(
        args.server
        + "/mlcubes/"
        + str(model_executor1_mlcube)
        + "/benchmarks/"
        + str(benchmark)
        + "/",
        "PUT",
        header(benchmark_owner_token),
        {"approval_status": "APPROVED"},
        "approval_status",
    )
    print(
        "Model MlCube Id:",
        model_executor1_mlcube,
        "associated to Benchmark Id:",
        benchmark,
        "is marked",
        model_executor1_in_benchmark_status,
        "(by Benchmark Owner)",
    )

    # Associate the model-executor2 mlcube to the created benchmark by model owner user
    model_executor2_in_benchmark = send_request(
        args.server + "/mlcubes/benchmarks/",
        "POST",
        header(model_owner_token),
        {
            "model_mlcube": model_executor2_mlcube,
            "benchmark": benchmark,
            "results": {"key1": "value1", "key2": "value2"},
        },
        "approval_status",
    )
    print(
        "Model MlCube Id:",
        model_executor2_mlcube,
        "associated to Benchmark Id:",
        benchmark,
        "(by Model Owner) which is in",
        model_executor2_in_benchmark,
        "state",
    )

    # Mark the model-executor2 association with created benchmark as approved by benchmark owner
    model_executor2_in_benchmark_status = send_request(
        args.server
        + "/mlcubes/"
        + str(model_executor2_mlcube)
        + "/benchmarks/"
        + str(benchmark)
        + "/",
        "PUT",
        header(benchmark_owner_token),
        {"approval_status": "APPROVED"},
        "approval_status",
    )
    print(
        "Model MlCube Id:",
        model_executor2_mlcube,
        "associated to Benchmark Id:",
        benchmark,
        "is marked",
        model_executor2_in_benchmark_status,
        "(by Benchmark Owner)",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the db with demo entries")
    parser.add_argument(
        "--server",
        type=str,
        help="Server host address to connect",
        default="http://127.0.0.1:8000",
    )
    parser.add_argument("--username", type=str, help="Admin username", default="admin")
    parser.add_argument("--password", type=str, help="Admin password", default="admin")
    args = parser.parse_args()
    seed(args)
