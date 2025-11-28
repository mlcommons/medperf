HOST = "127.0.0.1"
WEBUI_PORT = 8100
SERVER_PORT = 8000

LOCAL_PROFILE = "Local"

BASE_URL = f"http://{HOST}:{WEBUI_PORT}" + "{}"

BMK_OWNER_EMAIL = "testbo@example.com"
MODEL_OWNER_EMAIL = "testmo@example.com"
DSET_OWNER_EMAIL = "testdo@example.com"

# Benchmark Workflow Test Inputs
DATA_PREP_PATH = "medperf_tutorial/data_preparator/container_config.yaml"
MODEL_PATH = "medperf_tutorial/model_custom_cnn/container_config.yaml"
EVALUATOR_PATH = "medperf_tutorial/metrics/container_config.yaml"
DATA_PATH = "medperf_tutorial/demo_data/images"
LABELS_PATH = "medperf_tutorial/demo_data/labels"

# Benchmark Owner Data_Preparator Container Registration Inputs
DATA_PREPARATOR_CONTAINER = {
    "name": "my-prep",
    "manifest": "https://raw.githubusercontent.com/mlcommons/medperf/main/examples"
    + "/chestxray_tutorial/data_preparator/container_config.yaml",
    "parameters": "https://raw.githubusercontent.com/mlcommons/medperf/main/examples"
    + "/chestxray_tutorial/data_preparator/workspace/parameters.yaml",
    "additional": None,
}

# Benchmark Owner Reference_Model Container Registration Inputs
REF_MODEL_CONTAINER = {
    "name": "my-refmodel",
    "manifest": "https://raw.githubusercontent.com/mlcommons/medperf/main/examples"
    + "/chestxray_tutorial/model_custom_cnn/container_config.yaml",
    "parameters": "https://raw.githubusercontent.com/mlcommons/medperf/main/examples"
    + "/chestxray_tutorial/model_custom_cnn/workspace/parameters.yaml",
    "additional": "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz",
}

# Benchmark Owner Metrics Container Registration Inputs
METRICS_CONTAINER = {
    "name": "my-metrics",
    "manifest": "https://raw.githubusercontent.com/mlcommons/medperf/main/examples"
    + "/chestxray_tutorial/metrics/container_config.yaml",
    "parameters": "https://raw.githubusercontent.com/mlcommons/medperf/main/examples"
    + "/chestxray_tutorial/metrics/workspace/parameters.yaml",
    "additional": None,
}

# Benchmark Registration Inputs
BMK_NAME = "tutorial_bmk"
BMK_DESC = "MedPerf demo bmk"
REF_DATASET_TARBALL = (
    "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz"
)
DATA_PREP_NAME = "my-prep"
REF_MODEL_NAME = "my-refmodel"
METRICS_NAME = "my-metrics"

# Container Compatibility Test Inputs
CONTAINER_PATH = "medperf_tutorial/model_mobilenetv2/container_config.yaml"

# Container Registration Inputs
CONTAINER = {
    "name": "my-model",
    "manifest": "https://raw.githubusercontent.com/mlcommons/medperf/main/examples"
    + "/chestxray_tutorial/model_mobilenetv2/container_config.yaml",
    "parameters": "https://raw.githubusercontent.com/mlcommons/medperf/main/examples"
    + "/chestxray_tutorial/model_mobilenetv2/workspace/parameters.yaml",
    "additional": "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/mobilenetv2_weights.tar.gz",
}

# Encrypted Container Registration Inputs
ENCRYPTED_CONTAINER = {
    "name": "my-encrypted-model",
    "manifest": "https://raw.githubusercontent.com/RodriguesRBruno/medperf/0f1113bca1c2eef6a3c40b83032a9982b008effd"
    + "/examples/chestxray_tutorial/model_custom_cnn_encrypted/container_config.yaml",
    "parameters": "https://raw.githubusercontent.com/RodriguesRBruno/medperf/0f1113bca1c2eef6a3c40b83032a9982b008effd"
    + "/examples/chestxray_tutorial/model_custom_cnn_encrypted/workspace/parameters.yaml",
    "additional": "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz",
}

DECRYPTION_KEY_PATH = "examples/chestxray_tutorial/model_custom_cnn_encrypted/key.bin"

# Dataset Registration Inputs
DATASET_NAME = "mytestdata"
DATASET_DESC = "A tutorial dataset"
DATASET_LOCATION = "My machine"
DATASET_DATA_PATH = "medperf_tutorial/sample_raw_data/images"
DATASET_LABELS_PATH = "medperf_tutorial/sample_raw_data/labels"
