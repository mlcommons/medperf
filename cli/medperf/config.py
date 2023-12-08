from ._version import __version__
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

major_version, minor_version, patch_version = __version__.split(".")

server = "https://api.medperf.org"
certificate = None

local_server = "https://localhost:8000"
local_certificate = str(BASE_DIR / "server" / "cert.crt")

# START Auth0 config

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

auth_jwks_storage = ".jwks"
auth_jwks_cache_ttl = 600  # fetch jwks every 10 mins. Default value in auth0 python SDK

# END Auth0 config

local_tokens_path = BASE_DIR / "mock_tokens" / "tokens.json"

token_expiration_leeway = 10  # Refresh tokens 10 seconds before expiration
access_token_storage_id = "medperf_access_token"
refresh_token_storage_id = "medperf_refresh_token"

storage = str(Path.home().resolve() / ".medperf")
logs_storage = "logs"
tmp_storage = "tmp"
data_storage = "data"
demo_data_storage = "demo"
cubes_storage = "cubes"
images_storage = ".images"
predictions_storage = "predictions"
results_storage = "results"
results_info_file = "result-info.yaml"
benchmarks_storage = "benchmarks"
benchmarks_filename = "benchmark.yaml"
config_path = "config.yaml"
workspace_path = "workspace"
test_storage = "tests"
trash_folder = ".trash"
experiments_logs_storage = "experiments_logs"
cleanup = True
creds_folder = ".tokens"

test_report_file = "test_report.yaml"
cube_filename = "mlcube.yaml"
params_filename = "parameters.yaml"
additional_path = "workspace/additional_files"
tarball_filename = "tmp.tar.gz"
image_path = "workspace/.image"
reg_file = "registration-info.yaml"
log_file = "logs/medperf.log"
loglevel = "info"
demo_dset_paths_file = "paths.yaml"
cube_metadata_filename = "mlcube-meta.yaml"

credentials_keyword = "credentials"
default_profile_name = "default"
testauth_profile_name = "testauth"
test_profile_name = "local"
platform = "docker"
gpus = None
default_page_size = 32  # This number was chosen arbitrarily
ddl_stream_chunk_size = 10 * 1024 * 1024  # 10MB. This number was chosen arbitrarily
ddl_max_redownload_attempts = 3
comms = "REST"
ui = "CLI"

prepare_timeout = None
sanity_check_timeout = None
statistics_timeout = None
infer_timeout = None
evaluate_timeout = None
mlcube_configure_timeout = None
mlcube_inspect_timeout = None

configurable_parameters = [
    "server",
    "certificate",
    "auth_class",
    "auth_domain",
    "auth_jwks_url",
    "auth_idtoken_issuer",
    "auth_client_id",
    "auth_audience",
    "comms",
    "ui",
    "loglevel",
    "prepare_timeout",
    "sanity_check_timeout",
    "statistics_timeout",
    "infer_timeout",
    "evaluate_timeout",
    "platform",
    "gpus",
    "cleanup",
]

templates = {
    "data_preparator": "templates/data_preparator_mlcube",
    "model": "templates/model_mlcube",
    "evaluator": "templates/evaluator_mlcube",
    "gandlf": "templates/gandlf_mlcube",
}

# Temporary paths to cleanup that cannot be created in `tmp_storage`
tmp_paths = []
