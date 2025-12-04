import os
from utils import get_collaborator_cn
import shutil
from subprocess import check_call


def start_collaborator(workspace_folder):
    cn = get_collaborator_cn()
    check_call(
        [os.environ.get("OPENFL_EXECUTABLE", "fx"), "collaborator", "start", "-n", cn],
        cwd=workspace_folder,
    )

    # Cleanup
    shutil.rmtree(workspace_folder, ignore_errors=True)


def check_connectivity(workspace_folder):
    cn = get_collaborator_cn()
    check_call(
        [
            os.environ.get("OPENFL_EXECUTABLE", "fx"),
            "collaborator",
            "connectivity_check",
            "-n",
            cn,
        ],
        cwd=workspace_folder,
    )
