WSPACE_PATH = "workspace"
ADD_PATH = "additional_files"
ADD_FILE = "additional_files.tar.gz"
MLCUBE_FILE = "mlcube.yaml"
PARAMS_FILE = "parameters.yaml"
STATS_FILE = "statistics.yaml"
RESULTS_FILE = "results.yaml"
RUNNERS = ["docker", "singularity"]

TASK_DEFINITIONS = {
    "infer": {
        "inputs": {"data_path": None, "parameters_file": PARAMS_FILE},
        "outputs": {"output_path": None},
    },
    "prepare": {
        "inputs": {
            "data_path": None,
            "labels_path": None,
            "parameters_file": PARAMS_FILE,
        },
        "outputs": {"output_path": None},
    },
    "sanity_check": {"inputs": {"data_path": None, "parameters_file": PARAMS_FILE}},
    "statistics": {
        "inputs": {"data_path": None, "parameters_file": PARAMS_FILE},
        "outputs": {"output_path": STATS_FILE},
    },
    "evaluate": {
        "inputs": {"predictions": None, "labels": None, "parameters_file": PARAMS_FILE},
        "outputs": {"output_path": RESULTS_FILE},
    },
}
VALID_COMBINATIONS = [
    {"prepare", "sanity_check", "statistics"},
    {"infer",},
    {"evaluate",},
]
