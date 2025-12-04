from pydantic import BaseModel


class ContainerInput(BaseModel):
    name: str = ""
    config: str
    parameters: str = ""
    additional_local: str = ""
    additional_remote: str = ""


HOST = "127.0.0.1"
WEBUI_PORT = 8100
SERVER_PORT = 8000

LOCAL_PROFILE = "Local"

BASE_URL = f"http://{HOST}:{WEBUI_PORT}" + "{}"

BMK_OWNER_EMAIL = "testbo@example.com"
MODEL_OWNER_EMAIL = "testmo@example.com"
DSET_OWNER_EMAIL = "testdo@example.com"

# Containers Names
DATA_PREP_NAME = "my-prep"
REF_MODEL_NAME = "my-refmodel"
METRICS_NAME = "my-metrics"

# Benchmark Workflow Test and Containers Registration Inputs
BMK_DATA_PREP_BASE = "medperf_tutorial/data_preparator/{}"
BMK_REF_MODEL_BASE = "medperf_tutorial/model_custom_cnn/{}"
BMK_EVALUATOR_BASE = "medperf_tutorial/metrics/{}"

BMK_DATA_PREP = ContainerInput(
    name=DATA_PREP_NAME,
    config=BMK_DATA_PREP_BASE.format("container_config.yaml"),
    parameters=BMK_DATA_PREP_BASE.format("workspace/parameters.yaml"),
)
BMK_REF_MODEL = ContainerInput(
    name=REF_MODEL_NAME,
    config=BMK_REF_MODEL_BASE.format("container_config.yaml"),
    parameters=BMK_REF_MODEL_BASE.format("workspace/parameters.yaml"),
    additional_local=BMK_REF_MODEL_BASE.format("workspace/additional_files/"),
    additional_remote="https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz",
)
BMK_EVALUATOR = ContainerInput(
    name=METRICS_NAME,
    config=BMK_EVALUATOR_BASE.format("container_config.yaml"),
    parameters=BMK_EVALUATOR_BASE.format("workspace/parameters.yaml"),
)
BMK_DATA_PATH = "medperf_tutorial/demo_data/images"
BMK_LABELS_PATH = "medperf_tutorial/demo_data/labels"


# Benchmark Registration Inputs
BMK_NAME = "tutorial_bmk"
BMK_DESC = "MedPerf demo bmk"
REF_DATASET_TARBALL = (
    "https://storage.googleapis.com/medperf-storage/chestxray_tutorial/demo_data.tar.gz"
)

MODEL_BASE = "medperf_tutorial/model_mobilenetv2/{}"

# Model Compatibility Test and Registration Inputs
MODEL = ContainerInput(
    name="my-model",
    config=MODEL_BASE.format("container_config.yaml"),
    parameters=MODEL_BASE.format("workspace/parameters.yaml"),
    additional_local=MODEL_BASE.format("workspace/additional_files/"),
    additional_remote="https://storage.googleapis.com/medperf-storage/chestxray_tutorial/mobilenetv2_weights.tar.gz",
)

ENCRYPTED_MODEL_BASE = "examples/chestxray_tutorial/model_custom_cnn_encrypted/{}"

# Encrypted Model Registration Inputs
ENCRYPTED_MODEL = ContainerInput(
    name="my-encrypted-model",
    config=ENCRYPTED_MODEL_BASE.format("container_config.yaml"),
    parameters=ENCRYPTED_MODEL_BASE.format("workspace/parameters.yaml"),
    additional_remote="https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz",
)

DECRYPTION_KEY_PATH = ENCRYPTED_MODEL_BASE.format("key.bin")

# Dataset Registration Inputs
DATASET_NAME = "mytestdata"
DATASET_DESC = "A tutorial dataset"
DATASET_LOCATION = "My machine"
DATASET_DATA_PATH = "medperf_tutorial/sample_raw_data/images"
DATASET_LABELS_PATH = "medperf_tutorial/sample_raw_data/labels"
