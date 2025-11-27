from medperf.entities.cube import Cube
from medperf.utils import generate_tmp_path
import yaml


def run_mlcube(
    cube_path: str,
    task: str,
    parameters_file_path: str = None,
    additional_files_path: str = None,
    output_logs: str = None,
    timeout: int = None,
    mounts: dict = {},
    env: dict = {},
    ports: list = [],
    disable_network: bool = True,
    download: bool = False,
):
    """Dev utility command"""
    container_config = None
    parameters_config = None
    with open(cube_path, "r") as f:
        container_config = yaml.safe_load(f)
    if parameters_file_path:
        with open(parameters_file_path, "r") as f:
            parameters_config = yaml.safe_load(f)

    c = Cube(
        name="test",
        for_test=True,
        container_config=container_config,
        parameters_config=parameters_config,
    )
    if parameters_file_path is not None:
        c.params_path = generate_tmp_path()
    if additional_files_path is not None:
        c.additional_files_folder_path = additional_files_path

    if download:
        c.download_run_files()
    c.run(task, output_logs, timeout, mounts, env, ports, disable_network)
