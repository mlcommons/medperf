from pathlib import Path
import os

version = "0.0.0"
server = "http://localhost:8000"
storage = os.path.join(str(Path.home(), ".medperf"))
tmp_reg_prefix = "tmp_"
tmp_storage = "tmp"
data_storage = "data"
cubes_storage = "cubes"
results_storage = "results"
credentials_path = "credentials"
model_output = "outputs/predictions.csv"
workspace_path = "workspace"
cube_filename = "mlcube.yaml"
params_filename = "parameters.yaml"
additional_path = "workspace/additional_files"
tarball_filename = "tmp.tar.gz"
reg_file = "registration-info.yaml"
log_file = "medperf.log"
default_comms = "REST"
default_ui = "CLI"
