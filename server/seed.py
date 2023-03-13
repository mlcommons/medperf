import sys
import argparse
import requests
import json
import curlify

ASSETS_URL = (
    "https://raw.githubusercontent.com/aristizabal95/medperf-2/"
    "9dc2b03757d1883ccb3d47b7286acca8ba025db4/examples/ChestXRay/"
)


class Server:
    def __init__(self, host, cert):
        self.host = host
        self.cert = cert

    def request(self, endpoint, method, token, data, out_field=None):
        headers = {}
        if token:
            headers = {"Authorization": "Token " + token}
        headers.update(
            {"accept": "application/json", "Content-Type": "application/json"}
        )
        try:
            resp = requests.request(
                method=method,
                headers=headers,
                url=self.host + endpoint,
                data=json.dumps(data),
                verify=self.cert,
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


def seed(args):
    # Get Admin API token using admin credentials
    api_server = Server(host=args.server, cert=args.cert)
    admin_token = api_server.request(
        "/auth-token/",
        "POST",
        None,
        {"username": args.username, "password": args.password},
        "token",
    )
    print("Admin User Token:", admin_token)

    # Create a new user 'testbenchmarkowner' by admin(Admin API token is used)
    benchmark_owner = api_server.request(
        "/users/",
        "POST",
        admin_token,
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
    model_owner = api_server.request(
        "/users/",
        "POST",
        admin_token,
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
    data_owner = api_server.request(
        "/users/",
        "POST",
        admin_token,
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
    benchmark_owner_token = api_server.request(
        "/auth-token/",
        "POST",
        None,
        {"username": "testbenchmarkowner", "password": "test"},
        "token",
    )
    print("Benchmark Owner Token:", benchmark_owner_token)

    # Create a Data preprocessor MLCube by Benchmark Owner
    data_preprocessor_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        benchmark_owner_token,
        {
            "name": "xrv_prep",
            "git_mlcube_url": (ASSETS_URL + "chexpert_prep/mlcube/mlcube.yaml"),
            "mlcube_hash": "074d0593ed5a0a168bf99e077cd09538fb65e001",
            "git_parameters_url": (
                ASSETS_URL + "chexpert_prep/mlcube/workspace/parameters.yaml"
            ),
            "parameters_hash": "72b3a7570b9e56e31511f2a75041ecc820dd5cc3",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "additional_files_tarball_url": "",
            "additional_files_tarball_hash": "",
            "metadata": {},
        },
        "id",
    )
    print(
        "Data Preprocessor MLCube Created(by Benchmark Owner). ID:",
        data_preprocessor_mlcube,
    )

    # Update state of the Data preprocessor MLCube to OPERATION
    data_preprocessor_mlcube_state = api_server.request(
        "/mlcubes/" + str(data_preprocessor_mlcube) + "/",
        "PUT",
        benchmark_owner_token,
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Data Preprocessor MlCube state updated to",
        data_preprocessor_mlcube_state,
        "by Benchmark Owner",
    )

    # Create a reference model executor mlcube by Benchmark Owner
    reference_model_executor_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        benchmark_owner_token,
        {
            "name": "xrv_chex_densenet",
            "git_mlcube_url": (ASSETS_URL + "xrv_chex_densenet/mlcube/mlcube.yaml"),
            "mlcube_hash": "4cbecdfd7eebb96691f2d7b634a4fdf02b386bbf",
            "git_parameters_url": (
                ASSETS_URL + "xrv_chex_densenet/mlcube/workspace/parameters.yaml"
            ),
            "parameters_hash": "4271dbfa5e22a85b2a62ae3cefb340defc2fe74e",
            "additional_files_tarball_url": "https://storage.googleapis.com/medperf-storage/xrv_chex_densenet.tar.gz",
            "additional_files_tarball_hash": "c5c408b5f9ef8b1da748e3b1f2d58b8b3eebf96e",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "metadata": {},
        },
        "id",
    )
    print(
        "Reference Model Executor MlCube Created(by Benchmark Owner). ID:",
        reference_model_executor_mlcube,
    )

    # Update state of the Reference Model Executor MLCube to OPERATION
    reference_model_executor_mlcube_state = api_server.request(
        "/mlcubes/" + str(reference_model_executor_mlcube) + "/",
        "PUT",
        benchmark_owner_token,
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Reference Model Executor MlCube state updated to",
        reference_model_executor_mlcube_state,
        "by Benchmark Owner",
    )

    # Create a Data evalutor MLCube by Benchmark Owner
    data_evaluator_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        benchmark_owner_token,
        {
            "name": "xrv_metrics",
            "git_mlcube_url": (ASSETS_URL + "metrics/mlcube/mlcube.yaml"),
            "mlcube_hash": "5adafd609bb5100ff34f8dd563bd98f67de7d01f",
            "git_parameters_url": (
                ASSETS_URL + "metrics/mlcube/workspace/parameters.yaml"
            ),
            "parameters_hash": "302f2f565c630c18b96c89a7584987b95f43be80",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "additional_files_tarball_url": "",
            "additional_files_tarball_hash": "",
            "metadata": {},
        },
        "id",
    )
    print(
        "Data Evaluator MlCube Created(by Benchmark Owner). ID:", data_evaluator_mlcube,
    )

    # Update state of the Data Evaluator MLCube to OPERATION
    data_evaluator_mlcube_state = api_server.request(
        "/mlcubes/" + str(data_evaluator_mlcube) + "/",
        "PUT",
        benchmark_owner_token,
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Data Evaluator MlCube state updated to",
        data_evaluator_mlcube_state,
        "by Benchmark Owner",
    )

    # Create a new benchmark by Benchmark owner
    benchmark = api_server.request(
        "/benchmarks/",
        "POST",
        benchmark_owner_token,
        {
            "name": "xrv",
            "description": "benchmark-sample",
            "docs_url": "",
            "demo_dataset_tarball_url": "https://storage.googleapis.com/medperf-storage/xrv_demo_data.tar.gz",
            "demo_dataset_tarball_hash": "137950e4e7b8de3baa4a9982c3ebea6a52bd33d3",
            "demo_dataset_generated_uid": "f35c2d89caf140edb78e187a54d048c0590cb3ea",
            "data_preparation_mlcube": data_preprocessor_mlcube,
            "reference_model_mlcube": reference_model_executor_mlcube,
            "data_evaluator_mlcube": data_evaluator_mlcube,
        },
        "id",
    )
    print("Benchmark Created(by Benchmark Owner). ID:", benchmark)

    # Update the benchmark state to OPERATION
    benchmark_state = api_server.request(
        "/benchmarks/" + str(benchmark) + "/",
        "PUT",
        benchmark_owner_token,
        {"state": "OPERATION"},
        "state",
    )
    print("Benchmark state updated to", benchmark_state, "by Benchmark owner")

    # Mark the benchmark to be APPROVED
    benchmark_status = api_server.request(
        "/benchmarks/" + str(benchmark) + "/",
        "PUT",
        admin_token,
        {"approval_status": "APPROVED"},
        "approval_status",
    )
    print("Benchmark Id:", benchmark, "is marked", benchmark_status, "(by Admin)")

    print("##########################MODEL OWNER##########################")
    # Model Owner Interaction
    # Get Model Owner API token(token of testmodelowner user)
    model_owner_token = api_server.request(
        "/auth-token/",
        "POST",
        None,
        {"username": "testmodelowner", "password": "test"},
        "token",
    )
    print("Model Owner Token:", model_owner_token)

    # Create a model mlcube by Model Owner
    model_executor1_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        model_owner_token,
        {
            "name": "xrv_resnet",
            "git_mlcube_url": (ASSETS_URL + "xrv_resnet/mlcube/mlcube.yaml"),
            "mlcube_hash": "b2f17ed06c7b1225810588630abdc4d6ee8b3137",
            "git_parameters_url": (
                ASSETS_URL + "xrv_resnet/mlcube/workspace/parameters.yaml"
            ),
            "parameters_hash": "cd747953cf4b95e104d2c2b03385c656e44ffaec",
            "additional_files_tarball_url": "https://storage.googleapis.com/medperf-storage/xrv_resnet.tar.gz",
            "additional_files_tarball_hash": "e70a6c8e0931537b4b3dd8c06560f227605e9ed1",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "metadata": {},
        },
        "id",
    )
    print("Model MLCube Created(by Model Owner). ID:", model_executor1_mlcube)

    # Update state of the Model MLCube to OPERATION
    model_executor1_mlcube_state = api_server.request(
        "/mlcubes/" + str(model_executor1_mlcube) + "/",
        "PUT",
        model_owner_token,
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Model MlCube state updated to", model_executor1_mlcube_state, "by Model Owner",
    )

    # Associate the model-executor1 mlcube to the created benchmark by model owner user
    model_executor1_in_benchmark = api_server.request(
        "/mlcubes/benchmarks/",
        "POST",
        model_owner_token,
        {
            "model_mlcube": model_executor1_mlcube,
            "benchmark": benchmark,
            "metadata": {"key1": "value1", "key2": "value2"},
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
    model_executor1_in_benchmark_status = api_server.request(
        "/mlcubes/"
        + str(model_executor1_mlcube)
        + "/benchmarks/"
        + str(benchmark)
        + "/",
        "PUT",
        benchmark_owner_token,
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the db with demo entries")
    parser.add_argument(
        "--server",
        type=str,
        help="Server host address to connect",
        default="https://127.0.0.1:8000",
    )
    parser.add_argument("--username", type=str, help="Admin username", default="admin")
    parser.add_argument("--password", type=str, help="Admin password", default="admin")
    parser.add_argument("--cert", type=str, help="Server certificate")
    args = parser.parse_args()
    seed(args)
