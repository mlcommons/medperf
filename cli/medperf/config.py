from pathlib import Path
from os.path import expanduser, abspath

version = "0.0.0"
server = "http://localhost:8000"
storage = abspath(expanduser("~/.medperf"))
tmp_prefix = "tmp_"
tmp_storage = "tmp"
data_storage = "data"
cubes_storage = "cubes"
results_storage = "results"
results_filename = "result.yaml"
benchmarks_storage = "benchmarks"
benchmarks_filename = "benchmark.yaml"
credentials_path = "credentials"
model_output = "outputs/predictions.csv"
workspace_path = "workspace"
cube_filename = "mlcube.yaml"
params_filename = "parameters.yaml"
additional_path = "workspace/additional_files"
tarball_filename = "tmp.tar.gz"
reg_file = "registration-info.yaml"
log_file = "medperf.log"
test_cube_prefix = "test_"
test_dset_prefix = "test_"
demo_dset_paths_file = "paths.yaml"
default_comms = "REST"
default_ui = "CLI"
comms = None
ui = None
