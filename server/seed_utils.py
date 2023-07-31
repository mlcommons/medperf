from pathlib import Path
import sys
import requests
import json
import curlify
import os
import django
from django.contrib.auth import get_user_model

ASSETS_URL = (
    "https://raw.githubusercontent.com/hasan7n/medperf/"
    "99b0d84bc107415d9fc6f69c4ea3fcdfbf22315d/examples/chestxray_tutorial/"
)


class Server:
    def __init__(self, host, cert):
        self.host = host
        self.cert = cert

    def validate(self, verify=False, version=None):
        try:
            resp = requests.request(
                method="GET",
                url=self.host + "/version",
                verify=self.cert,
            )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        if resp.status_code != 200:
            sys.exit("Response code is " + str(resp.status_code))

        res = json.loads(resp.text)
        if "version" not in res:
            sys.exit("Version response is empty")
        print("Server running at version " + res["version"])
        if verify:
            if res["version"] != version:
                sys.exit("Server version do not match with the client argument")
            print("Server version match with client version")
        self.version = res["version"]
        return res["version"]

    def request(self, endpoint, method, token, data, out_field=None):
        headers = {}
        if token:
            headers = {"Authorization": "Bearer " + token}
        headers.update(
            {"accept": "application/json", "Content-Type": "application/json"}
        )
        try:
            resp = requests.request(
                method=method,
                headers=headers,
                url=self.host + "/api/" + self.version + endpoint,
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


def set_user_as_admin(api_server, access_token):
    user_id = api_server.request("/me/", "GET", access_token, {}, out_field="id")

    cwd = os.getcwd()
    os.chdir(Path(__file__).parent)
    os.environ["DJANGO_SETTINGS_MODULE"] = "medperf.settings"
    django.setup()
    User = get_user_model()
    user = User.objects.get(id=user_id)

    user.is_staff = True
    user.is_superuser = True
    user.save()

    os.chdir(cwd)


def create_benchmark(api_server, benchmark_owner_token, admin_token):
    print("##########################BENCHMARK OWNER##########################")

    # Create a Data preprocessor MLCube by Benchmark Owner
    data_preprocessor_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        benchmark_owner_token,
        {
            "name": "chestxray_prep",
            "git_mlcube_url": (ASSETS_URL + "data_preparator/mlcube/mlcube.yaml"),
            "mlcube_hash": "425d1d64c2247e8270ec7159b858ae1cc34d2281",
            "git_parameters_url": (
                ASSETS_URL + "data_preparator/mlcube/workspace/parameters.yaml"
            ),
            "parameters_hash": "2b28ab34a12e0c0767ea9022ab14e9a0dfba67f2",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "4cefa8a2b9580220a0503076f1e961e4d86ec72dad8e1e78b9c43444dee9a4cd",
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
            "name": "chestxray_cnn",
            "git_mlcube_url": (ASSETS_URL + "model_custom_cnn/mlcube/mlcube.yaml"),
            "mlcube_hash": "5e5ca7f0228b2b660f4dc672fa8cc23e28df2df4",
            "git_parameters_url": (
                ASSETS_URL + "model_custom_cnn/mlcube/workspace/parameters.yaml"
            ),
            "parameters_hash": "c5f977a7d1b40d125e6450b3cc0956ea5b0a652c",
            "additional_files_tarball_url": (
                "https://storage.googleapis.com/medperf-storage/"
                "chestxray_tutorial/cnn_weights.tar.gz"
            ),
            "additional_files_tarball_hash": "6c2346c11a3e5e7afa575bce711eea755266b1ed",
            "image_hash": "",
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
            "name": "chestxray_metrics",
            "git_mlcube_url": (ASSETS_URL + "metrics/mlcube/mlcube.yaml"),
            "mlcube_hash": "7b3bd8ece694470abf5cb76159d638811d698049",
            "git_parameters_url": (
                ASSETS_URL + "metrics/mlcube/workspace/parameters.yaml"
            ),
            "parameters_hash": "277598e53d6a75431e9bec610595e8590be5bf01",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "2dbea6a3ba40d553905427c8bb156f219970306f55061462918fd19b220e9b51",
            "additional_files_tarball_url": "",
            "additional_files_tarball_hash": "",
            "metadata": {},
        },
        "id",
    )
    print(
        "Data Evaluator MlCube Created(by Benchmark Owner). ID:",
        data_evaluator_mlcube,
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
            "name": "chestxray",
            "description": "benchmark-sample",
            "docs_url": "",
            "demo_dataset_tarball_url": "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz",
            "demo_dataset_tarball_hash": "fd54a97f52ebc0e2f533a17b77165ee4d343f5b4",
            "demo_dataset_generated_uid": "730d2474d8f22340d9da89fa2eb925fcb95683e0",
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
    return benchmark


def create_model(api_server, model_owner_token, benchmark_owner_token, benchmark):
    print("##########################MODEL OWNER##########################")
    # Model Owner Interaction

    # Create a model mlcube by Model Owner
    model_executor1_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        model_owner_token,
        {
            "name": "chestxray_mobilenet",
            "git_mlcube_url": (ASSETS_URL + "model_mobilenetv2/mlcube/mlcube.yaml"),
            "mlcube_hash": "172a58c365864552d0718e094e9454a2f8eec30f",
            "git_parameters_url": (
                ASSETS_URL + "model_mobilenetv2/mlcube/workspace/parameters.yaml"
            ),
            "parameters_hash": "b36a5bbf9cbdad8be232840e040235918e98a2c6",
            "additional_files_tarball_url": (
                "https://storage.googleapis.com/medperf-storage/"
                "chestxray_tutorial/mobilenetv2_weights.tar.gz"
            ),
            "additional_files_tarball_hash": "b99eb6d11a141e32333389d234e819da7a409c17",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "7ae4a8ecbe899b5486c699d934d74bce7f3aa73d779e0138e6d119cd8040b46e",
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
        "Model MlCube state updated to",
        model_executor1_mlcube_state,
        "by Model Owner",
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
