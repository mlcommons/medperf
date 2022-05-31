from os.path import expanduser, abspath

version = "0.0.0"
server = "http://localhost:8000"
storage = abspath(expanduser("~/.medperf"))
tmp_reg_prefix = "tmp_"
logs_storage = "logs"
tmp_storage = "tmp"
data_storage = "data"
cubes_storage = "cubes"
predictions_storage = "predictions"
results_storage = "results"
results_filename = "result.yaml"
credentials_path = "credentials"
workspace_path = "workspace"
cube_filename = "mlcube.yaml"
params_filename = "parameters.yaml"
additional_path = "workspace/additional_files"
tarball_filename = "tmp.tar.gz"
reg_file = "registration-info.yaml"
log_file = "logs/medperf.log"
default_comms = "REST"
default_ui = "CLI"
git_file_domain = "https://raw.githubusercontent.com"
comms = None
ui = None
