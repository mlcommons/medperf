WSPACE_PATH = "workspace"
ADD_PATH = "additional_files"
ADD_FILE = "additional_files.tar.gz"
MLCUBE_FILE = "mlcube.yaml"
PARAMS_FILE = "parameters.yaml"
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
        "outputs": {"output_path": None},
    },
    "evaluate": {
        "inputs": {"predictions": None, "labels": None, "parameters_file": PARAMS_FILE},
        "outputs": {"output_path": None},
    },
}
VALID_COMBINATIONS = {
    "Data Preparation MLCube": {"prepare", "sanity_check", "statistics"},
    "Model MLCube": {"infer",},
    "Evaluator MLCube": {"evaluate",},
}
