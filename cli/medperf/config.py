from ._version import __version__
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

major_version, minor_version, patch_version = __version__.split(".")

# MedPerf server
server = "https://api.medperf.org"
certificate = None

local_server = "https://localhost:8000"
local_certificate = str(BASE_DIR / "server" / "cert.crt")

comms = "REST"

# Auth config
auth = None  # This will be overwritten by the globally initialized auth class object
auth_class = "Auth0"

auth_domain = "auth.medperf.org"
auth_dev_domain = "dev-5xl8y6uuc2hig2ly.us.auth0.com"

auth_jwks_url = f"https://{auth_domain}/.well-known/jwks.json"
auth_dev_jwks_url = f"https://{auth_dev_domain}/.well-known/jwks.json"

auth_idtoken_issuer = f"https://{auth_domain}/"
auth_dev_idtoken_issuer = f"https://{auth_dev_domain}/"

auth_client_id = "vFtfndViDFd0BeMdMKBgsKA9aV9BDtrY"
auth_dev_client_id = "PSe6pJzYJ9ZmLuLPagHEDh6W44fv9nat"

auth_audience = "https://api.medperf.org/"
auth_dev_audience = "https://localhost-dev/"

auth_jwks_cache_ttl = 600  # fetch jwks every 10 mins. Default value in auth0 python SDK

token_expiration_leeway = 10  # Refresh tokens 10 seconds before expiration
access_token_storage_id = "medperf_access_token"
refresh_token_storage_id = "medperf_refresh_token"

local_tokens_path = BASE_DIR / "mock_tokens" / "tokens.json"

# Storage config
config_storage = Path.home().resolve() / ".medperf_config"
logs_storage = Path.home().resolve() / ".medperf_logs"
config_path = str(config_storage / "config.yaml")
auth_jwks_file = str(config_storage / ".jwks")
creds_folder = str(config_storage / ".tokens")
tokens_db = str(config_storage / ".tokens_db")

images_folder = ".images"
trash_folder = ".trash"
tmp_folder = ".tmp"
demo_datasets_folder = "demo"

benchmarks_folder = "benchmarks"
cubes_folder = "cubes"
datasets_folder = "data"
experiments_logs_folder = "experiments_logs"
results_folder = "results"
predictions_folder = "predictions"
tests_folder = "tests"

default_base_storage = str(Path.home().resolve() / ".medperf")

storage = {
    "images_folder": {
        "base": default_base_storage,
        "name": images_folder,
    },
    "trash_folder": {
        "base": default_base_storage,
        "name": trash_folder,
    },
    "tmp_folder": {
        "base": default_base_storage,
        "name": tmp_folder,
    },
    "demo_datasets_folder": {
        "base": default_base_storage,
        "name": demo_datasets_folder,
    },
    "benchmarks_folder": {
        "base": default_base_storage,
        "name": benchmarks_folder,
    },
    "cubes_folder": {
        "base": default_base_storage,
        "name": cubes_folder,
    },
    "datasets_folder": {
        "base": default_base_storage,
        "name": datasets_folder,
    },
    "experiments_logs_folder": {
        "base": default_base_storage,
        "name": experiments_logs_folder,
    },
    "results_folder": {
        "base": default_base_storage,
        "name": results_folder,
    },
    "predictions_folder": {
        "base": default_base_storage,
        "name": predictions_folder,
    },
    "tests_folder": {
        "base": default_base_storage,
        "name": tests_folder,
    },
}

root_folders = [
    "images_folder",
    "trash_folder",
    "tmp_folder",
    "demo_datasets_folder",
]
server_folders = [
    "benchmarks_folder",
    "cubes_folder",
    "datasets_folder",
    "experiments_logs_folder",
    "results_folder",
    "predictions_folder",
    "tests_folder",
]

# MedPerf filenames conventions
results_info_file = "result-info.yaml"
benchmarks_filename = "benchmark.yaml"
test_report_file = "test_report.yaml"
reg_file = "registration-info.yaml"
cube_metadata_filename = "mlcube-meta.yaml"
log_file = "medperf.log"
log_package_file = "medperf_logs.tar.gz"
tarball_filename = "tmp.tar.gz"
demo_dset_paths_file = "paths.yaml"
mlcube_cache_file = ".cache_metadata.yaml"
report_file = "report.yaml"
metadata_folder = "metadata"
statistics_filename = "statistics.yaml"
dataset_raw_paths_file = "raw.yaml"
ready_flag_file = ".ready"

# MLCube assets conventions
cube_filename = "mlcube.yaml"
params_filename = "parameters.yaml"
workspace_path = "workspace"
additional_path = "workspace/additional_files"
image_path = "workspace/.image"

# requests
default_page_size = 32  # This number was chosen arbitrarily
ddl_stream_chunk_size = 10 * 1024 * 1024  # 10MB. This number was chosen arbitrarily
ddl_max_redownload_attempts = 3
wait_before_sending_reports = 30  # In seconds

# Container config
gpus = None
platform = "docker"
prepare_timeout = None
sanity_check_timeout = None
statistics_timeout = None
infer_timeout = None
evaluate_timeout = None
container_loglevel = None
mlcube_configure_timeout = None
mlcube_inspect_timeout = None

# Other
loglevel = "debug"
logs_backup_count = 100
cleanup = True
ui = "CLI"

default_profile_name = "default"
testauth_profile_name = "testauth"
test_profile_name = "local"
credentials_keyword = "credentials"

inline_parameters = [
    "loglevel",
    "prepare_timeout",
    "sanity_check_timeout",
    "statistics_timeout",
    "infer_timeout",
    "evaluate_timeout",
    "platform",
    "gpus",
    "cleanup",
    "container_loglevel",
]
configurable_parameters = inline_parameters + [
    "server",
    "certificate",
    "auth_class",
    "auth_domain",
    "auth_jwks_url",
    "auth_idtoken_issuer",
    "auth_client_id",
    "auth_audience",
]

templates = {
    "data_preparator": "templates/data_preparator_mlcube",
    "model": "templates/model_mlcube",
    "evaluator": "templates/evaluator_mlcube",
    "gandlf": "templates/gandlf_mlcube",
}

# Temporary paths to cleanup
tmp_paths = []
