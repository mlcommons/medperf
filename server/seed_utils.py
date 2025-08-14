from __future__ import annotations
from pathlib import Path
import sys
import requests
import json
import curlify
import os
import django
from django.contrib.auth import get_user_model

ASSETS_URL = (
    "https://raw.githubusercontent.com/mlcommons/medperf/"
    "9bfb828ab19caf4fd9a4a90be69c693d4e2ff29d/examples/chestxray_tutorial/"
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
            "git_mlcube_url": (ASSETS_URL + "data_preparator/container_config.yaml"),
            "mlcube_hash": "173d593918abdde0e008dc4dbad12393e9b26cd27787570337f7ef4923946e31",
            "git_parameters_url": (
                ASSETS_URL + "data_preparator/workspace/parameters.yaml"
            ),
            "parameters_hash": "1541e05437040745d2489e8d2cf14795d4839eecc15c1ac959c84f6b77c1a5df",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "d941e09d160bba3cf5c09b48f490e3b9e891597341e560954ff7512478eaef22",
            "additional_files_tarball_url": "",
            "additional_files_tarball_hash": "",
            "metadata": {
                "digest": "f8697dc1c646395ad1ac54b8c0373195dbcfde0c4ef5913d4330a5fe481ae9a4"
            },
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
            "git_mlcube_url": (ASSETS_URL + "model_custom_cnn/container_config.yaml"),
            "mlcube_hash": "7ffb958bf83841b5f601a2538d004740216c336872c824a2fc3b9b346c6291dc",
            "git_parameters_url": (
                ASSETS_URL + "model_custom_cnn/workspace/parameters.yaml"
            ),
            "parameters_hash": "af0aed4735b5075c198f8b49b3afbf7a0d7eaaaaa2a2b914d5931f0bee51d3f6",
            "additional_files_tarball_url": (
                "https://storage.googleapis.com/medperf-storage/"
                "chestxray_tutorial/cnn_weights.tar.gz"
            ),
            "additional_files_tarball_hash": "bff003e244759c3d7c8b9784af0819c7f252da8626745671ccf7f46b8f19a0ca",
            "image_hash": "877b8df79678215dfdcb63fe6bc1dab58e9c29113437c2c5627442551e3087c5",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "metadata": {
                "digest": "a1bdddce05b9d156df359dd570de8031fdd1ea5a858f755139bed4a95fad19d1"
            },
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
            "git_mlcube_url": (ASSETS_URL + "metrics/container_config.yaml"),
            "mlcube_hash": "1617c231a9a9cc596664222056e19718ef860552ab8cf99a97f52318e0d566f7",
            "git_parameters_url": (ASSETS_URL + "metrics/workspace/parameters.yaml"),
            "parameters_hash": "16cad451c54b801a5b50d999330465d7f68ab5f6d30a0674268d2d17c7f26b73",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "c61b4079be59ba3bb31090bdf89f7f603023f77d28ca0475b5320efaa36866aa",
            "additional_files_tarball_url": "",
            "additional_files_tarball_hash": "",
            "metadata": {
                "digest": "d33904c1104d0a3df314f29c603901a8584fec01e58b90d7ae54c8d74d32986c"
            },
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

    # Create a model mlcube by Model Owner
    model_executor1_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        model_owner_token,
        {
            "name": "chestxray_mobilenet",
            "git_mlcube_url": (ASSETS_URL + "model_mobilenetv2/container_config.yaml"),
            "mlcube_hash": "618ce7ef9f2b0dbdb0f361823aa4e2efc32e3ef9b29334466bd33eb3eca2aa02",
            "git_parameters_url": (
                ASSETS_URL + "model_mobilenetv2/workspace/parameters.yaml"
            ),
            "parameters_hash": "81a7e5c2006a8f54c4c2bd16d751df44d3cde3feb1a0c12768df095744a76c60",
            "additional_files_tarball_url": (
                "https://storage.googleapis.com/medperf-storage/"
                "chestxray_tutorial/mobilenetv2_weights.tar.gz"
            ),
            "additional_files_tarball_hash": "771f67bba92a11c83d16a522f0ba1018020ff758e2277d33f49056680c788892",
            "image_tarball_url": "",
            "image_tarball_hash": "",
            "image_hash": "33d26c8e266be9fe072081fb157313bfa51778b2934ab64bd622c8f0cd52dfa1",
            "metadata": {
                "digest": "f27deb052eafd48ad1e350ceef7b0b9600aef0ea3f8cba47baee2b1d17411a83"
            },
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


def create_private_model(api_server: Server, private_model_owner_token, benchmark_owner_token, benchmark):
    print("##########################MODEL OWNER - PRIVATE MODEL##########################")
    # Model Owner Interaction - Creating a Private Model

    # Create a model mlcube by Model Owner
    private_model_executor1_mlcube = api_server.request(
        "/mlcubes/",
        "POST",
        private_model_owner_token,
        {
            "name": "chestxray_cnn_priv",
            # TODO update URL to main repo once this is pushed there
            "git_mlcube_url": (
                "https://raw.githubusercontent.com/RodriguesRBruno/medperf/"
                "d005d8405159e14dc34f04c22fcf24dd67e0aa6e/examples/"
                "chestxray_tutorial/model_custom_cnn_encrypted/container_config.yaml"),
            "mlcube_hash": "5072a12d1eacdcc4489a026a266537f81bbf33e4adb191a43bdcb0ade09da5a6",
            "git_parameters_url": (
                ASSETS_URL + "model_custom_cnn/workspace/parameters.yaml"
            ),
            "parameters_hash": "af0aed4735b5075c198f8b49b3afbf7a0d7eaaaaa2a2b914d5931f0bee51d3f6",
            "additional_files_tarball_url": (
                "https://storage.googleapis.com/medperf-storage/"
                "chestxray_tutorial/cnn_weights.tar.gz"
            ),
            "additional_files_tarball_hash": "bff003e244759c3d7c8b9784af0819c7f252da8626745671ccf7f46b8f19a0ca",
            "image_hash": "c36e83a0b7c81118365e60ba8d9d6586eab1372af5483b0120ae7b8b80f45dbe",
            "image_tarball_url": "",
            "image_tarball_hash": "",
        },
        "id",
    )
    print("Private Model MLCube Created(by Private Model Owner). ID:", private_model_executor1_mlcube)

    # Update state of the Model MLCube to OPERATION
    private_model_executor1_mlcube_state = api_server.request(
        "/mlcubes/" + str(private_model_executor1_mlcube) + "/",
        "PUT",
        private_model_owner_token,
        {"state": "OPERATION"},
        "state",
    )
    print(
        "Model MlCube state updated to",
        private_model_executor1_mlcube_state,
        "by Private Model Owner",
    )

    # Associate the model-executor1 mlcube to the created benchmark by model owner user
    private_model_executor1_in_benchmark = api_server.request(
        "/mlcubes/benchmarks/",
        "POST",
        private_model_owner_token,
        {
            "model_mlcube": private_model_executor1_mlcube,
            "benchmark": benchmark,
            "metadata": {"key1": "value1", "key2": "value2"},
        },
        "approval_status",
    )

    print(
        "Model MlCube Id:",
        private_model_executor1_mlcube,
        "associated to Benchmark Id:",
        benchmark,
        "(by Private Model Owner) which is in",
        private_model_executor1_in_benchmark,
        "state",
    )

    # Mark the model-executor1 association with created benchmark as approved by benchmark owner
    model_executor1_in_benchmark_status = api_server.request(
        "/mlcubes/"
        + str(private_model_executor1_mlcube)
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
        private_model_executor1_mlcube,
        "associated to Benchmark Id:",
        benchmark,
        "is marked",
        model_executor1_in_benchmark_status,
        "(by Benchmark Owner)",
    )
