import venv
from medperf import config
import os
import shutil
from pathlib import Path
from medperf.exceptions import MedperfException
from medperf.utils import spawn_and_kill, combine_proc_sp_text
import shlex


def create_airflow_venv_if_not_exists(force_creation=False):
    if os.path.exists(config.airflow_venv_dir) and not force_creation:
        return

    requirements_file = str(
        Path(__file__).parent.resolve() / config.airflow_requirements_file
    )
    if not os.path.exists(requirements_file):
        raise MedperfException(
            f"Could not find the {config.airflow_requirements_file}! Please verify your MedPerf installation."
        )
    # TODO add Windows executable if we eventually support windows
    python_executable = os.path.join(config.airflow_venv_dir, "bin", "python")

    venv.create(env_dir=config.airflow_venv_dir, clear=True, with_pip=True)
    if not os.path.exists(python_executable):
        shutil.rmtree(config.airflow_venv_dir)
        raise MedperfException(
            "Failed to find the Python executable for Airflow environment "
            f"in directory {config.airflow_venv_dir}. "
            "The virtual environment has been deleted."
        )

    command = [python_executable, "-m", "pip", "install", "-r", requirements_file]
    with spawn_and_kill(shlex.join(command), timeout=None) as spawn_wrapper:
        combine_proc_sp_text(spawn_wrapper.proc)

    if spawn_wrapper.proc.exitstatus != 0:
        shutil.rmtree(config.airflow_venv_dir)
        error_msg = f"Failed to install dependencies to the Airflow environment located at {config.airflow_venv_dir}.\n"
        error_msg += "The virtual environment has been deleted."
        raise MedperfException(error_msg)


if __name__ == "__main__":
    create_airflow_venv_if_not_exists(force_creation=True)
