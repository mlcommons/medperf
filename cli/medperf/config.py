from os.path import expanduser, abspath

version = "0.0.0"
server = "https://medperf.org"
certificate = None

local_server = "https://localhost:8000"
local_certificate = "~/.medperf.crt"

storage = abspath(expanduser("~/.medperf"))
tmp_prefix = "tmp_"
logs_storage = "logs"
tmp_storage = "tmp"
data_storage = "data"
demo_data_storage = "demo"
cubes_storage = "cubes"
predictions_storage = "predictions"
results_storage = "results"
results_filename = "result.yaml"
benchmarks_storage = "benchmarks"
benchmarks_filename = "benchmark.yaml"
credentials_path = "credentials"
workspace_path = "workspace"
cube_filename = "mlcube.yaml"
params_filename = "parameters.yaml"
additional_path = "workspace/additional_files"
tarball_filename = "tmp.tar.gz"
image_path = "workspace/.image"
reg_file = "registration-info.yaml"
log_file = "logs/medperf.log"
test_cube_prefix = "test_"
test_dset_prefix = "test_"
demo_dset_paths_file = "paths.yaml"
default_comms = "REST"
default_ui = "CLI"
git_file_domain = "https://raw.githubusercontent.com"
comms = None
ui = None
