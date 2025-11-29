from medperf.entities.cube import Cube
from typing import Optional


class MigrationCube(Cube):
    """
    Includes the soon to be removed 'git_mlcube_url' and 'parameters_file'
    used to make this migration.
    """

    git_mlcube_url: str
    mlcube_hash: Optional[str]
    git_parameters_url: Optional[str]
    parameters_hash: Optional[str]
    container_config: Optional[str]
    parameters_config: Optional[str]
