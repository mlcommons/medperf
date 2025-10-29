from ._version import __version__
from pathlib import Path
from os import getenv

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
refresh_token_expiration_leeway = (
    10  # Logout users 10 seconds before absolute token expiration.
)
token_absolute_expiry = 2592000  # Refresh token absolute expiration time (seconds). This value is set on auth0's configuration
access_token_storage_id = "medperf_access_token"
refresh_token_storage_id = "medperf_refresh_token"

local_tokens_path = BASE_DIR / "mock_tokens" / "tokens.json"

# Storage config
config_storage = Path.home().resolve() / ".medperf_config"
logs_storage = Path.home().resolve() / ".medperf_logs"
airflow_venv_dir = str(config_storage / ".airflow_venv")
config_path = getenv("MEDPERF_CONFIG_PATH", str(config_storage / "config.yaml"))
auth_jwks_file = str(config_storage / ".jwks")
creds_folder = str(config_storage / ".tokens")
tokens_db = str(config_storage / ".tokens_db")
pki_assets = str(config_storage / ".pki_assets")
webui_host_props = str(config_storage / ".webui_host_props")

# TODO: should we change this?
safe_root = ""  # Base path to accept input paths from user.

images_folder = ".images"
trash_folder = ".trash"
tmp_folder = ".tmp"
demo_datasets_folder = "demo"

benchmarks_folder = "benchmarks"
cubes_folder = "cubes"
datasets_folder = "data"
experiments_logs_folder = "experiments_logs"
executions_folder = "executions"
predictions_folder = "predictions"
tests_folder = "tests"
training_folder = "training"
aggregators_folder = "aggregators"
cas_folder = "cas"
training_events_folder = "training_events"

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
    "executions_folder": {
        "base": default_base_storage,
        "name": executions_folder,
    },
    "predictions_folder": {
        "base": default_base_storage,
        "name": predictions_folder,
    },
    "tests_folder": {
        "base": default_base_storage,
        "name": tests_folder,
    },
    "training_folder": {
        "base": default_base_storage,
        "name": training_folder,
    },
    "aggregators_folder": {
        "base": default_base_storage,
        "name": aggregators_folder,
    },
    "cas_folder": {
        "base": default_base_storage,
        "name": cas_folder,
    },
    "training_events_folder": {
        "base": default_base_storage,
        "name": training_events_folder,
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
    "executions_folder",
    "predictions_folder",
    "tests_folder",
    "training_folder",
    "aggregators_folder",
    "cas_folder",
    "training_events_folder",
]

# MedPerf filenames conventions
results_info_file = "result-info.yaml"
benchmarks_filename = "benchmark.yaml"
test_report_file = "test_report.yaml"
reg_file = "registration-info.yaml"
agg_file = "agg-info.yaml"
ca_file = "ca-info.yaml"
training_event_file = "event.yaml"
cube_metadata_filename = "mlcube-meta.yaml"
log_file = "medperf.log"
webui_log_file = "medperf_webui.log"
data_monitor_log_file = "medperf_data_monitor.log"
log_package_file = "medperf_logs.tar.gz"
tarball_filename = "tmp.tar.gz"
demo_dset_paths_file = "paths.yaml"
mlcube_cache_file = ".cache_metadata.yaml"
training_exps_filename = "training-info.yaml"
participants_list_filename = "cols.yaml"
training_exp_plan_filename = "plan.yaml"
training_exp_status_filename = "status.yaml"
training_report_file = "report.yaml"
training_report_folder = "report"
training_out_agg_logs = "agg_logs"
training_out_col_logs = "col_logs"
training_out_weights = "weights"
ca_cert_folder = "ca_cert"
ca_config_file = "ca_config.json"
agg_config_file = "aggregator_config.yaml"
report_file = "report.yaml"
metadata_folder = "metadata"
statistics_filename = "statistics.yaml"
dataset_raw_paths_file = "raw.yaml"
ready_flag_file = ".ready"
partial_flag = ".partial"
executed_flag = ".executed"
results_filename = "results.yaml"
local_metrics_outputs = "local_outputs"
airflow_requirements_file = "airflow_requirements.txt"

# MLCube assets conventions
cube_filename = "container_config.yaml"
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
shm_size = None
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
webui = "WEBUI"

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
    "shm_size",
    "cleanup",
    "container_loglevel",
]
configurable_parameters = [
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
    "data_preparator": "templates/data_preparator_container",
    "model": "templates/model_container",
    "evaluator": "templates/evaluator_container",
    "gandlf": "templates/gandlf_container",
}

# Temporary paths to cleanup
tmp_paths = []

# Data Import/Export config
archive_config_filename = "config.yaml"
