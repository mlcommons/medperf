from os.path import expanduser, abspath

customizable_params = {
    "server": "URL of a hosted MedPerf API instance",
    "certificate": "path to a valid SSL certificate",
    "comms": "communications interface to use. [REST]",
    "ui": "UI interface to use. [CLI]",
    "loglevel": "Logging level [debug | info | warning | error]",
    "prepare_timeout": "Maximum time in seconds before interrupting prepare task",
    "sanity_check_timeout": "Maximum time in seconds before interrupting sanity_check task",
    "statistics_timeout": "Maximum time in seconds before interrupting statistics task",
    "infer_timeout": "Maximum time in seconds before interrupting infer task",
    "evaluate_timeout": "Maximum time in seconds before interrupting evaluate task",
    "platform": "Platform to use for MLCube. Valid options: docker, singularity",
    "cleanup": "Wether to clean up temporary medperf storage after execution"
}

version = "0.0.0"
server = "https://api.medperf.org"
certificate = None

local_server = "https://localhost:8000"
local_certificate = "~/.medperf_test.crt"

storage = abspath(expanduser("~/.medperf"))
tmp_prefix = "tmp_"
logs_storage = "logs"
tmp_storage = "tmp"
data_storage = "data"
demo_data_storage = "demo"
cubes_storage = "cubes"
predictions_storage = "predictions"
results_storage = "results"
statistics_filename = "tmp_statistics.yaml"
results_filename = "result.yaml"
results_info_file = "result-info.yaml"
benchmarks_storage = "benchmarks"
benchmarks_filename = "benchmark.yaml"
credentials_path = "credentials"
config_path = "config"
workspace_path = "workspace"
cleanup = True

cube_filename = "mlcube.yaml"
params_filename = "parameters.yaml"
additional_path = "workspace/additional_files"
tarball_filename = "tmp.tar.gz"
image_path = "workspace/.image"
reg_file = "registration-info.yaml"
log_file = "logs/medperf.log"
loglevel = "info"
test_cube_prefix = "test_"
cube_submission_id = "tmp_submission"
test_dset_prefix = "test_"
demo_dset_paths_file = "paths.yaml"
cube_metadata_filename = "mlcube-meta.yaml"
cube_hashes_filename = "mlcube-hashes.yaml"
cube_get_max_attempts = 3

profile = "default"
platform = "docker"
default_page_size = 32  # This number was chosen arbitrarily
comms = "REST"
ui = "CLI"

prepare_timeout = None
sanity_check_timeout = None
statistics_timeout = None
infer_timeout = None
evaluate_timeout = None
