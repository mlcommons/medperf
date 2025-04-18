from medperf.entities.cube import Cube


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
    c = Cube(name="test", for_test=True, git_mlcube_url="https://example.com")
    c.cube_path = cube_path
    c.params_path = parameters_file_path
    c.additiona_files_folder_path = additional_files_path
    if download:
        c.download_run_files()
    c.run(task, output_logs, timeout, mounts, env, ports, disable_network)
