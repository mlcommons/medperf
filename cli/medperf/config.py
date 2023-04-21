from ._version import __version__
from os.path import expanduser, abspath

major_version, minor_version, patch_version = __version__.split(".")

server = "https://api.medperf.org"
certificate = None

local_server = "https://localhost:8000"
local_certificate = "server/cert.crt"

storage = abspath(expanduser("~/.medperf"))
tmp_prefix = "tmp_"
logs_storage = "logs"
tmp_storage = "tmp"
data_storage = "data"
demo_data_storage = "demo"
cubes_storage = "cubes"
images_storage = ".images"
predictions_storage = "predictions"
results_storage = "results"
statistics_filename = "tmp_statistics.yaml"
results_info_file = "result-info.yaml"
benchmarks_storage = "benchmarks"
benchmarks_filename = "benchmark.yaml"
config_path = "config.yaml"
workspace_path = "workspace"
test_storage = "tests"
cleanup = True

test_report_file = "test_report.yaml"
cube_filename = "mlcube.yaml"
params_filename = "parameters.yaml"
additional_path = "workspace/additional_files"
tarball_filename = "tmp.tar.gz"
image_path = "workspace/.image"
reg_file = "registration-info.yaml"
log_file = "logs/medperf.log"
loglevel = "info"
test_cube_prefix = "test_"
test_dset_prefix = "test_"
demo_dset_paths_file = "paths.yaml"
cube_metadata_filename = "mlcube-meta.yaml"
cube_hashes_filename = "mlcube-hashes.yaml"

credentials_keyword = "credentials"
default_profile_name = "default"
test_profile_name = "test"
platform = "docker"
gpus = "all"
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

configurable_parameters = [
    "server",
    "certificate",
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
}

extra_cleanup_paths = []
