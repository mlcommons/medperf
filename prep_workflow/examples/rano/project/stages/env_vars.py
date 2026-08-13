import os


WORKSPACE_DIR = os.getenv("WORKSPACE_DIRECTORY")
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
DATA_SUBDIR = os.path.join(*DATA_DIR.split(os.sep)[-2:])
INPUT_DIR = os.path.join(WORKSPACE_DIR, "input_data")
