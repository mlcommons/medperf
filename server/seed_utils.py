from pathlib import Path
import sys
import requests
import json
import curlify
import os
import django
from django.contrib.auth import get_user_model
import yaml


ASSETS_URL = (
    "https://raw.githubusercontent.com/mlcommons/medperf/"
    "9bfb828ab19caf4fd9a4a90be69c693d4e2ff29d/examples/chestxray_tutorial/"
)


def _load_asset_content(file_relative_url: str):
    asset_url = f"{ASSETS_URL}/{file_relative_url}"

    response = requests.get(asset_url)
    content = yaml.safe_load(response.content)

    return content


def load_container_config(dirname: str):
    return _load_asset_content(f"{dirname}/container_config.yaml")


def load_parameters_config(dirname: str):
    return _load_asset_content(f"{dirname}/workspace/parameters.yaml")


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

    data_prep_config = load_container_config("data_preparator")
    data_prep_params = load_parameters_config("data_preparator")
    # Create a Data preprocessor MLCube by Benchmark Owner
    data_preprocessor_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        benchmark_owner_token,
        {
            "name": "chestxray_prep",
            "container_config": data_prep_config,
            "parameters_config": data_prep_params,
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "sha256:f8697dc1c646395ad1ac54b8c0373195dbcfde0c4ef5913d4330a5fe481ae9a4",
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

    model_cnn_container_config = load_container_config("model_custom_cnn")
    model_cnn_parameters_config = load_parameters_config("model_custom_cnn")
    # Create a reference model executor mlcube by Benchmark Owner
    reference_model_executor_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        benchmark_owner_token,
        {
            "name": "chestxray_cnn",
            "container_config": model_cnn_container_config,
            "parameters_config": model_cnn_parameters_config,
            "additional_files_tarball_url": (
                "https://storage.googleapis.com/medperf-storage/"
                "chestxray_tutorial/cnn_weights.tar.gz"
            ),
            "additional_files_tarball_hash": "bff003e244759c3d7c8b9784af0819c7f252da8626745671ccf7f46b8f19a0ca",
            "image_hash": "sha256:a1bdddce05b9d156df359dd570de8031fdd1ea5a858f755139bed4a95fad19d1",
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

    evaluator_container_config = load_container_config("metrics")
    evaluator_parameters_config = load_parameters_config("metrics")
    # Create a Data evalutor MLCube by Benchmark Owner
    data_evaluator_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        benchmark_owner_token,
        {
            "name": "chestxray_metrics",
            "container_config": evaluator_container_config,
            "parameters_config": evaluator_parameters_config,
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "sha256:d33904c1104d0a3df314f29c603901a8584fec01e58b90d7ae54c8d74d32986c",
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
            "demo_dataset_tarball_hash": "71faabd59139bee698010a0ae3a69e16d97bc4f2dde799d9e187b94ff9157c00",
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

    mobilenet_container_config = load_container_config("model_mobilenetv2")
    mobilenet_parameters_config = load_parameters_config("model_mobilenetv2")

    # Create a model mlcube by Model Owner
    model_executor1_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        model_owner_token,
        {
            "name": "chestxray_mobilenet",
            "container_config": mobilenet_container_config,
            "parameters_config": mobilenet_parameters_config,
            "additional_files_tarball_url": (
                "https://storage.googleapis.com/medperf-storage/"
                "chestxray_tutorial/mobilenetv2_weights.tar.gz"
            ),
            "additional_files_tarball_hash": "771f67bba92a11c83d16a522f0ba1018020ff758e2277d33f49056680c788892",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "sha256:f27deb052eafd48ad1e350ceef7b0b9600aef0ea3f8cba47baee2b1d17411a83",
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
